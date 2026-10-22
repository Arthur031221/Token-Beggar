"""`token-beggar doctor`: the things that quietly stop routing from working, in one list."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import catalog, ceiling, compact, hooks, paths

OK, WARN, FAIL = "ok", "warn", "fail"
STALE_CATALOG_DAYS = 30


def _python() -> tuple[str, str]:
    version = ".".join(map(str, sys.version_info[:3]))
    return (OK, version) if sys.version_info >= (3, 10) else (FAIL, f"{version}, 3.10 or newer is required")


def _state() -> tuple[str, str]:
    probe = paths.home() / ".doctor"
    try:
        probe.write_text("x")
        probe.unlink()
    except OSError as error:
        return FAIL, f"{paths.home()} is not writable ({error.strerror})"
    return OK, str(paths.home())


def _switch() -> tuple[str, str]:
    if os.environ.get("TOKEN_BEGGAR") == "off":
        return WARN, "TOKEN_BEGGAR=off is set in this environment, so the hooks do nothing"
    if hooks.disabled():
        return WARN, f"{paths.home() / 'off'} exists, so the hooks do nothing. Delete it to turn Token Beggar on"
    return OK, "on"


def _catalog() -> tuple[str, str]:
    try:
        updated = catalog.load().get("updated", "")
        age = (time.time() - time.mktime(time.strptime(updated, "%Y-%m-%d"))) / 86400
    except (OSError, ValueError):
        return FAIL, "models.json is missing or unreadable"
    detail = f"{len(catalog.models())} models, updated {updated}"
    return (OK, detail) if age <= STALE_CATALOG_DAYS else (WARN, f"{detail}, run `token-beggar update`")


def _ceiling() -> tuple[str, str]:
    top = ceiling.resolve(None, os.getcwd())
    if not top["known"]:
        return WARN, "chat model not found in settings or environment, so the card will say the ceiling is unknown"
    return OK, f"{top['model']} at {top['effort']} (effort from {top['effort_source']})"


def _subagent_model() -> tuple[str, str]:
    value = os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL")
    if value:
        return WARN, f"CLAUDE_CODE_SUBAGENT_MODEL={value} forces every worker onto one model. Unset it so routing can choose"
    return OK, "not set"


def _window() -> tuple[str, str]:
    window = compact.configured_window(os.getcwd())
    if window:
        return OK, f"{window:,} tokens"
    return WARN, "CLAUDE_CODE_AUTO_COMPACT_WINDOW is not set (60000 or more), so the guard only writes handoff notes"


def _errors() -> tuple[str, str]:
    log = paths.home() / "errors.log"
    if not log.exists():
        return OK, "no hook errors logged"
    lines = [line for line in log.read_text(errors="ignore").splitlines() if line.strip()]
    if not lines:
        return OK, "no hook errors logged"
    stamp = time.strftime("%F %T", time.localtime(log.stat().st_mtime))
    return WARN, f"{len(lines)} lines in {log}, last written {stamp}: {lines[-1].strip()[:80]}. Delete the file once handled"


def _hook() -> tuple[str, str]:
    """Run the prompt hook the way the host does: `sh -c` on the command in hooks.json, python3 from PATH, a real prompt."""
    command = json.loads((paths.PACKAGE_ROOT / "hooks" / "hooks.json").read_text())["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    payload = {"prompt": "Rename calc_total to order_total across the repo", "session_id": "doctor", "cwd": os.getcwd()}
    with tempfile.TemporaryDirectory() as scratch:
        env = {k: v for k, v in os.environ.items() if k != "TOKEN_BEGGAR"}
        env.update(CLAUDE_PLUGIN_ROOT=str(paths.PACKAGE_ROOT), TOKEN_BEGGAR_HOME=scratch, TOKEN_BEGGAR_OFFLINE="1")
        try:
            done = subprocess.run(["sh", "-c", command], input=json.dumps(payload), capture_output=True, text=True, timeout=10, env=env, cwd=scratch)
        except (OSError, subprocess.TimeoutExpired) as error:
            return FAIL, f"hook did not run: {error}"
        logged = Path(scratch, "errors.log")
        if logged.exists():  # the hook swallows its own exceptions, so the log is where a crash shows
            return FAIL, f"hook crashed: {logged.read_text().strip().splitlines()[-1][:120]}"
    if done.returncode != 0:
        return FAIL, f"`python3` on PATH failed with exit {done.returncode}: {done.stderr.strip()[-120:]}"
    try:
        json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    except (ValueError, KeyError, TypeError):
        return FAIL, "hook ran but did not return a routing card"
    return OK, "runs through python3 on PATH and returns the card"


CHECKS = [
    ("python", _python),
    ("state directory", _state),
    ("switch", _switch),
    ("model catalog", _catalog),
    ("ceiling", _ceiling),
    ("worker model override", _subagent_model),
    ("compaction window", _window),
    ("hook errors", _errors),
    ("hook entry", _hook),
]


def run() -> list[tuple[str, str, str]]:
    """One broken check must not hide the rest of the report."""
    results = []
    for name, check in CHECKS:
        try:
            results.append((name, *check()))
        except Exception as error:
            results.append((name, FAIL, f"check crashed: {type(error).__name__}: {error}"))
    return results


def render(results: list[tuple[str, str, str]]) -> str:
    lines = [f"{status.upper():<5} {name:<22} {detail}" for name, status, detail in results]
    bad = sum(status == FAIL for _, status, _ in results)
    warned = sum(status == WARN for _, status, _ in results)
    lines.append("")
    lines.append("All good." if not (bad or warned) else f"{bad} failed, {warned} to look at.")
    return "\n".join(lines)
