"""The durable note written before a compaction, and handed back right after it."""

import json
import time
from pathlib import Path

from . import paths, transcript

MAX_PROMPT = 700


def _clip(text: str, limit: int = MAX_PROMPT) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build(items: list[dict], cwd: str | None = None) -> str:
    """Decisions live in the conversation, so the note keeps what can be read off it exactly:
    the task, the files touched, the commands run, the open todos and where the last turn stopped."""
    prompts = transcript.user_prompts(items)
    calls = transcript.tool_calls(items)
    touched: list[str] = []
    for _, block in calls:
        if block.get("name") in transcript.EDIT_TOOLS:
            data = block.get("input") or {}
            file = data.get("file_path") or data.get("notebook_path")
            if file:
                if file in touched:
                    touched.remove(file)
                touched.append(file)
    commands = [str((b.get("input") or {}).get("command", "")) for _, b in calls if b.get("name") == "Bash"]
    open_todos = [t for t in transcript.todos(items) if t.get("status") != "completed"]
    unverified = transcript.unverified_edits(items)

    lines = ["# Token Beggar handoff", "", f"Written {time.strftime('%Y-%m-%d %H:%M')} in {cwd or 'unknown directory'}.", ""]
    if prompts:
        lines += ["## Original request", _clip(prompts[0]), ""]
        if len(prompts) > 1:
            lines += ["## Latest requests"] + [f"- {_clip(p, 300)}" for p in prompts[-3:]] + [""]
    if touched:
        lines += ["## Files changed (oldest first)"] + [f"- {f}" for f in touched[-40:]] + [""]
    if commands:
        lines += ["## Last commands"] + [f"- `{_clip(c, 160)}`" for c in commands[-8:]] + [""]
    if open_todos:
        lines += ["## Open todos"] + [f"- [{t.get('status', 'pending')}] {_clip(str(t.get('content', '')), 160)}" for t in open_todos] + [""]
    if unverified:
        lines += ["## Edited since the last test, lint or build", *[f"- {f}" for f in unverified[-20:]], ""]
    last = transcript.last_assistant_text(items)
    if last:
        lines += ["## Where the last turn stopped", _clip(last, 900), ""]
    return "\n".join(lines).rstrip() + "\n"


def note_path(session_id: str) -> Path:
    folder = paths.home() / "handoff"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.md"


def write(session_id: str, items: list[dict], cwd: str | None = None) -> Path:
    path = note_path(session_id)
    path.write_text(build(items, cwd))
    return path


def read(session_id: str) -> str | None:
    path = note_path(session_id)
    return path.read_text() if path.is_file() else None


def prune(days: int = 14) -> None:
    cutoff = time.time() - days * 86400
    for old in (paths.home() / "handoff").glob("*.*"):
        if old.stat().st_mtime < cutoff:
            old.unlink(missing_ok=True)


def write_model(
    session_id: str, text: str, mid_step: bool, used: int, progress: float | None = None, phase_done: bool = False, needs_detail: bool = False
) -> Path:
    """The note the chat model wrote itself. `used` is the context size when it wrote it, so a stale note can be told apart."""
    path = note_path(session_id).with_suffix(".model.md")
    path.write_text(text.strip() + "\n")
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                "mid_step": mid_step,
                "used": used,
                "at": time.time(),
                "progress": progress,
                "phase": "done" if phase_done else "",
                "needs_detail": needs_detail,
            }
        )
    )
    return path


def read_model(session_id: str) -> dict | None:
    path = note_path(session_id).with_suffix(".model.md")
    try:
        meta = json.loads(path.with_suffix(".json").read_text())
        return {
            "text": path.read_text(),
            "mid_step": bool(meta["mid_step"]),
            "used": int(meta["used"]),
            "at": meta.get("at", 0),
            "progress": meta.get("progress"),
            "phase": meta.get("phase", ""),
            "needs_detail": bool(meta.get("needs_detail", False)),
        }
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None
