"""The arms a benchmark run can use, each as a plugin directory plus extra environment.

alone                    no plugin
v020                     the released v0.2.0 (commit 9b63cdb), built once from git
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


def _v020() -> Path:
    dest = BUILD / "v020"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", V020_COMMIT], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    return dest


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
    if arm == "v020":
        dest = BUILD / "v020"
        return dest if dest.exists() else _v020()
    lever = arm.removeprefix("final-no-")
    if lever not in LEVERS:
        raise SystemExit(f"unknown arm {arm}")
    dest = BUILD / arm
    return dest if dest.exists() else _ablation(lever)


def extra_env(arm: str) -> dict:
    env = {"TOKEN_BEGGAR_MODE": "full"} if arm == "fullcard" or arm.startswith("final-no-") else {}  # the ablations are cut from the full card
    if arm == "final-no-bulk-agy":
        env["TOKEN_BEGGAR_EXTERNAL"] = "none"
    return env


def prepare(arms: list[str]) -> None:
    """Build every directory once, before parallel runs start."""
    for arm in arms:
        plugin_dir(arm)
