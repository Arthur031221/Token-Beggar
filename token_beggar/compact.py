"""Dynamic compaction: warn before the point, defer it while a step is mid-air, never lose the thread."""

import json
import os
import re
from pathlib import Path

from . import handoff, paths, transcript

WARN_FRACTION = 0.875  # 350k of a 400k compaction point
DEFER_STEP = 0.05  # each deferral lifts the point by 5 percent of the window
MAX_DEFERRALS = 3


def parse_window(value: str | None) -> int | None:
    """'400000', '400k' or '1m'."""
    if not value:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kKmM]?)\s*", value)
    if not match:
        return None
    scale = {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()]
    return int(float(match.group(1)) * scale)


def configured_window(cwd: str | None = None) -> int | None:
    """The compaction point the user set, from the environment or the settings env block. None when they did not set one."""
    found = parse_window(os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW"))
    if found:
        return found
    files = [paths.claude_dir() / "settings.json"]
    if cwd:
        files = [Path(cwd) / ".claude" / "settings.local.json", Path(cwd) / ".claude" / "settings.json"] + files
    for file in files:
        try:
            env = json.loads(file.read_text()).get("env") or {}
        except (OSError, json.JSONDecodeError):
            continue
        found = parse_window(str(env.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "")))
        if found:
            return found
    return None


def _state_file(session_id: str) -> Path:
    folder = paths.home() / "compact-state"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.json"


def _deferrals(session_id: str) -> int:
    try:
        return int(json.loads(_state_file(session_id).read_text()).get("deferrals", 0))
    except (OSError, json.JSONDecodeError, ValueError):
        return 0


def _set_deferrals(session_id: str, count: int) -> None:
    _state_file(session_id).write_text(json.dumps({"deferrals": count}))


def mid_step_reason(items: list[dict]) -> str | None:
    """The one rule: files were edited and no test, lint or build ran after the last edit."""
    unverified = transcript.unverified_edits(items)
    if unverified:
        return f"{len(unverified)} file(s) edited since the last test, lint or build"
    return None


def usage_notice(items: list[dict], window: int | None) -> str | None:
    used = transcript.context_tokens(items)
    if not window or used < WARN_FRACTION * window:
        return None
    return (
        f"Context is about {used // 1000}k of a {window // 1000}k compaction point. "
        "Reach a clean stopping point soon: finish the edit in hand, run the tests, then continue. "
        "A handoff note is written automatically before compaction."
    )


def on_precompact(payload: dict) -> tuple[int, str]:
    """Return (exit_code, message). Exit 2 defers an automatic compaction."""
    session_id = payload.get("session_id", "unknown")
    items = transcript.entries(payload["transcript_path"]) if payload.get("transcript_path") else []
    handoff.write(session_id, items, payload.get("cwd"))
    handoff.prune()
    window = configured_window(payload.get("cwd"))
    if payload.get("trigger") != "auto" or not window:  # without a known window a deferral could run past the model's real limit
        return 0, ""
    count = _deferrals(session_id)
    reason = mid_step_reason(items)
    limit = int(window * (1 + DEFER_STEP * MAX_DEFERRALS))
    if reason and count < MAX_DEFERRALS and transcript.context_tokens(items) < limit:
        _set_deferrals(session_id, count + 1)
        return 2, f"Token Beggar deferred compaction ({count + 1}/{MAX_DEFERRALS}): {reason}. Finish the step and run the tests."
    _set_deferrals(session_id, 0)
    return 0, ""


def on_session_start(payload: dict) -> str | None:
    """After a compaction, put the handoff note back in front of the model."""
    if payload.get("source") != "compact":
        return None
    note = handoff.read(payload.get("session_id", ""))
    if not note:
        return None
    return "Token Beggar restored this note from before the compaction:\n\n" + note
