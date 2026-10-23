"""The arms a benchmark run can use, each as a plugin directory plus extra environment.

alone                    no plugin
v020                     the released v0.2.0 (commit 9b63cdb), built once from git
main                     main before the size aware strategy (commit b761ce6, called "Main before v0.3.0" in the reports; the released v0.2.0 is 9b63cdb), built once from git (hard task benchmark)
sized                    the first wording of the size aware card (hard task benchmark), not shipped: it judged every real issue small and routed 1 run in 26
verify                   this tree, the size aware card with the large task triggers and the required review of the diff (hard task benchmark), copied once
scoped                   this tree, the size aware card plus the scope rule (the worker lists every site that shares the symptom, the chat checks the list), copied once
final                    this tree, the mode picked from the measured ratio of the model and effort (one line card at Opus 5.5 high)
fullcard                 this tree with the full menu forced (TOKEN_BEGGAR_MODE=full): the pass before the stand down rule
final-no-<lever>         this tree with one lever taken out, to price that lever alone:
    bulk-agy             outside tools turned off, so bulk reading cannot go to agy
    lean-tools           the worker inherits every tool instead of the six it needs
    batch                the batching rule removed
    short-output         the short-output rules removed from the card, the rules and the worker
    early                the early compaction prompt switched off (judged by long_session.py, not run.py)
"""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = Path(os.environ.get("TB_ARMS", "/tmp/tb-arms"))
V020_COMMIT = "9b63cdb"
MAIN_COMMIT = "b761ce6"  # main before the size aware strategy: model based modes, lean card at Opus 5.5 high
LEVERS = ("bulk-agy", "lean-tools", "batch", "short-output", "early")


def _copy_tree(dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", "benchmark", "__pycache__", "*.pyc", "demo", "assets"))
    return dest


def _sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, (path, old)
    path.write_text(text.replace(old, new))


def _drop_rule(path: Path, start: str) -> None:
    lines = path.read_text().splitlines(keepends=True)
    kept = [line for line in lines if not line.lstrip().startswith(start)]
    assert len(kept) < len(lines), (path, start)
    path.write_text("".join(kept))


def _from_git(commit: str, name: str) -> Path:
    dest = BUILD / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", commit], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    return dest


def _v020() -> Path:
    return _from_git(V020_COMMIT, "v020")


def _ablation(lever: str) -> Path:
    dest = _copy_tree(BUILD / f"final-no-{lever}")
    if lever == "lean-tools":
        _drop_rule(dest / "agents" / "beggar-worker.md", "tools:")
    elif lever == "batch":
        _drop_rule(dest / "data" / "profiles.json", '"Batch:')
        _sub(dest / "token_beggar" / "card.py", " Independent ones go in one message.", "")
    elif lever == "early":
        _sub(dest / "token_beggar" / "compact.py", 'if point["user_set"] or used < early_point(point)', "if True or used < early_point(point)")
    elif lever == "short-output":
        _drop_rule(dest / "data" / "profiles.json", '"Keep output short')
        _drop_rule(dest / "agents" / "beggar-worker.md", "- Report in under 150 words")
        _sub(dest / "token_beggar" / "card.py", "the check to run and 'report under 150 words'.", "and the check to run.")
    return dest


def plugin_dir(arm: str) -> Path | None:
    if arm == "alone":
        return None
    if arm in ("final", "fullcard"):
        return ROOT
    if arm == "sized":  # built from git at the commit that held the first wording
        dest = BUILD / "sized"
        return dest if dest.exists() else _from_git("c605b3e", "sized")
    if arm in ("verify", "scoped"):  # a snapshot, so editing the tree during a long benchmark cannot leak into the arm
        dest = BUILD / arm
        return dest if dest.exists() else _copy_tree(dest)
    if arm == "main":
        dest = BUILD / "main"
        return dest if dest.exists() else _from_git(MAIN_COMMIT, "main")
    if arm == "v020":
        dest = BUILD / "v020"
        return dest if dest.exists() else _v020()
    lever = arm.removeprefix("final-no-")
    if lever not in LEVERS:
        raise SystemExit(f"unknown arm {arm}")
    dest = BUILD / arm
    return dest if dest.exists() else _ablation(lever)


def extra_env(arm: str) -> dict:
    # the lever ablations are cut from the full card, except early compaction, which belongs to every mode
    env = {"TOKEN_BEGGAR_MODE": "full"} if arm == "fullcard" or (arm.startswith("final-no-") and arm != "final-no-early") else {}
    if arm == "final-no-bulk-agy":
        env["TOKEN_BEGGAR_EXTERNAL"] = "none"
    return env


def prepare(arms: list[str]) -> None:
    """Build every directory once, before parallel runs start."""
    for arm in arms:
        plugin_dir(arm)
