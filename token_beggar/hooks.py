"""Hook entry points. A failure here must never get in the way of the user's session."""

import json
import os
import subprocess
import sys
import time
import traceback

from . import card, ceiling, compact, inventory, paths, transcript, update

MIN_PROMPT_CHARS = 25


def disabled() -> bool:
    return os.environ.get("TOKEN_BEGGAR") == "off" or (paths.home() / "off").exists()


def _emit(event: str, text: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def _carded_ceiling(session_id: str, signature: str | None = None) -> str | None:
    """The ceiling the session's card was built for. Pass a signature to record one."""
    folder = paths.home() / "sessions"
    folder.mkdir(parents=True, exist_ok=True)
    stored = folder / f"{session_id}.ceiling"
    if signature is None:
        return stored.read_text() if stored.exists() else None
    stored.write_text(signature)
    return signature


def _weekly_refresh() -> None:
    """Start the catalog refresh in the background at most once a week. It never blocks the prompt."""
    if os.environ.get("TOKEN_BEGGAR_OFFLINE") == "1" or not update.due():
        return
    update.mark_checked()
    subprocess.Popen(
        [sys.executable, "-m", "token_beggar", "update", "--quiet"],
        cwd=str(paths.PACKAGE_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def on_prompt(payload: dict) -> None:
    prompt = payload.get("prompt", "")
    if disabled() or len(prompt.strip()) < MIN_PROMPT_CHARS or prompt.lstrip().startswith("/"):
        return
    session_id = payload.get("session_id", "unknown")
    cwd = payload.get("cwd")
    _weekly_refresh()
    top = ceiling.resolve(payload.get("transcript_path"), cwd)
    parts = []
    signature = f"{top['model']}|{top['effort']}"
    if _carded_ceiling(session_id) == signature:
        parts.append(card.reminder())
    else:  # first prompt, or the model or effort changed since the last card
        parts.append(card.build(top, inventory.load(cwd)))
        _carded_ceiling(session_id, signature)
    if payload.get("transcript_path"):
        notice = compact.usage_notice(transcript.entries(payload["transcript_path"]), compact.configured_window(cwd))
        if notice:
            parts.append(notice)
    _emit("UserPromptSubmit", "\n".join(parts))


def on_precompact(payload: dict) -> int:
    code, message = compact.on_precompact(payload)
    if message:
        print(message, file=sys.stderr)
    return code


def on_session_start(payload: dict) -> None:
    if payload.get("source") != "compact" or disabled():
        return
    session_id = payload.get("session_id", "unknown")
    note = compact.on_session_start(payload)
    top = ceiling.resolve(payload.get("transcript_path"), payload.get("cwd"))
    text = card.build(top, inventory.load(payload.get("cwd")))
    _emit("SessionStart", text + ("\n\n" + note if note else ""))
    _carded_ceiling(session_id, f"{top['model']}|{top['effort']}")


def run(event: str) -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if event == "prompt":
            on_prompt(payload)
        elif event == "precompact":
            return on_precompact(payload)
        elif event == "sessionstart":
            on_session_start(payload)
    except Exception:  # a hook must not break the session
        with (paths.home() / "errors.log").open("a") as log:
            log.write(f"{time.strftime('%F %T')} {event}\n{traceback.format_exc()}\n")
    return 0
