"""Hook entry points. A failure here must never get in the way of the user's session."""

import json
import os
import subprocess
import sys
import time
import traceback

from . import card, catalog, ceiling, compact, external, footer, inventory, paths, profiles, transcript, update

MIN_PROMPT_CHARS = 25
SUBAGENT = "token-beggar:beggar-worker"


def disabled() -> bool:
    return os.environ.get("TOKEN_BEGGAR") == "off" or (paths.home() / "off").exists()


def _emit(event: str, text: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def _effort(payload: dict) -> str | None:
    return (payload.get("effort") or {}).get("level") if isinstance(payload.get("effort"), dict) else None


def _top(payload: dict) -> dict:
    return ceiling.resolve(payload.get("transcript_path"), payload.get("cwd"), _effort(payload))


def _session_file(session_id: str, suffix: str):
    folder = paths.home() / "sessions"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.{suffix}"


def _carded_ceiling(session_id: str, signature: str | None = None) -> str | None:
    """The ceiling the session's card was built for. Pass a signature to record one."""
    stored = _session_file(session_id, "ceiling")
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


def _compaction_text(payload: dict, top: dict, items: list[dict] | None = None) -> list[str]:
    """The note request near the compaction point, and the one-time word after a deferral."""
    if not payload.get("transcript_path"):
        return []
    session_id = payload.get("session_id", "unknown")
    point = compact.resolve(payload.get("cwd"), catalog.find(top["model"]))
    parts = []
    if not point["disabled"]:
        used = transcript.tail_context_tokens(payload["transcript_path"])
        if used >= min(compact.warn_point(point["threshold"]), compact.early_point(point)):  # only parse the whole transcript when it is near
            items = items or transcript.entries(payload["transcript_path"])
            notice = compact.usage_notice(session_id, items, point)
            if notice:
                parts.append(notice)
    deferred = compact.deferred_notice(session_id)
    if deferred:
        parts.append(deferred)
    return parts


def on_prompt(payload: dict) -> None:
    prompt = payload.get("prompt", "")
    if disabled():
        return
    session_id = payload.get("session_id", "unknown")
    top = _top(payload)
    parts = []
    if len(prompt.strip()) >= MIN_PROMPT_CHARS and not prompt.lstrip().startswith("/"):
        _weekly_refresh()
        before = external.load_caps(session_id)
        caps = external.save_caps(session_id, external.parse_caps(prompt))
        signature = f"{top['model']}|{top['effort']}"
        if _carded_ceiling(session_id) == signature:
            parts.append(card.reminder())
            if caps != before:
                parts.append("User caps now: " + (", ".join(f"{t} {c}" for t, c in caps.items()) or "none") + ". Honour them.")
        else:  # first prompt, or the model or effort changed since the last card
            parts.append(card.build(top, inventory.load(payload.get("cwd")), caps))
            _carded_ceiling(session_id, signature)
    parts += _compaction_text(payload, top)
    if parts:
        _emit("UserPromptSubmit", "\n".join(parts))


def _watch_quota(payload: dict) -> str | None:
    """A worker that ends in a usage limit error marks its model out of quota, so the menu leaves it off without anyone running a command."""
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name") not in ("Agent", "Task") or tool_input.get("subagent_type") != SUBAGENT:
        return None
    response = payload.get("tool_response")
    text = response if isinstance(response, str) else json.dumps(response or "") + str(payload.get("error") or "")
    if not external.QUOTA.search(text):
        return None
    result = response if isinstance(response, dict) else {}
    model = catalog.find(result.get("resolvedModel") or tool_input.get("model"))
    if not model:
        return None
    hours = external.reset_hours(text)
    inventory.mark_exhausted(model.alias, hours)
    return f"Token Beggar marked {model.alias} out of quota for about {hours:.1f}h. Do this subtask inline or on a cheaper model."


def on_posttool(payload: dict) -> None:
    """During a long agentic turn no prompt arrives, so the compaction check runs after tool calls too."""
    if disabled():
        return
    parts = [note for note in (_watch_quota(payload),) if note]
    parts += _compaction_text(payload, _top(payload))
    if parts:
        _emit(payload.get("hook_event_name") or "PostToolUse", "\n".join(parts))


def on_pretool(payload: dict) -> None:
    """Hold a Token Beggar worker to the ceiling and off models that are out of quota."""
    tool_input = payload.get("tool_input") or {}
    if disabled() or tool_input.get("subagent_type") != SUBAGENT:
        return
    top = _top(payload)
    ceiling_model = catalog.find(top["model"])
    if not ceiling_model:
        return
    gone = profiles.exhausted(inventory.load(payload.get("cwd")))
    fixed = dict(tool_input)
    wanted = catalog.find(tool_input.get("model")) if tool_input.get("model") else None
    if wanted:
        pick = min((wanted, ceiling_model), key=lambda m: m.tier)
        if pick.alias in gone:  # the nearest cheaper model that still has quota
            lower = [m for m in catalog.models() if m.tier < pick.tier and m.alias not in gone]
            pick = lower[-1] if lower else pick
        if pick.alias != wanted.alias:
            fixed["model"] = pick.alias
    effort = tool_input.get("effort")
    if effort in catalog.EFFORTS:
        capped = catalog.cap_effort(effort, top["effort"])
        if capped != effort:
            fixed["effort"] = capped
    if fixed != tool_input:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": fixed}}))


SETTLE_SECONDS = float(os.environ.get("TOKEN_BEGGAR_SETTLE", "4"))


def _settled(items: list[dict], payload: dict) -> bool:
    """True once the transcript holds the reply's final message. The host can run the Stop hook before it has written it."""
    final = str(payload.get("last_assistant_message") or "").strip()
    return not final or final in transcript.last_assistant_text(items)


def on_stop(payload: dict) -> None:
    """The footer: one line, shown to the user, when the skill routed something in this reply."""
    if disabled() or payload.get("stop_hook_active") or not payload.get("transcript_path"):
        return
    deadline = time.monotonic() + SETTLE_SECONDS
    items = transcript.entries(payload["transcript_path"])
    while not _settled(items, payload) and time.monotonic() < deadline:
        time.sleep(0.25)
        items = transcript.entries(payload["transcript_path"])
    line = footer.build(payload, items, complete=_settled(items, payload))
    if not line:
        return
    window = footer.usage.reply_window(items)
    key = f"{window[0].get('uuid')}:{len(window)}" if window else line
    marker = _session_file(payload.get("session_id", "unknown"), "footer")
    if marker.exists() and marker.read_text() == key:  # the same reply already got its line
        return
    marker.write_text(key)
    print(json.dumps({"systemMessage": line}))


def on_precompact(payload: dict) -> int:
    top = _top(payload)
    code, message = compact.on_precompact(payload, catalog.find(top["model"]))
    if message:
        print(message, file=sys.stderr)
    return code


def on_session_start(payload: dict) -> None:
    if payload.get("source") != "compact" or disabled():
        return
    session_id = payload.get("session_id", "unknown")
    note = compact.on_session_start(payload)
    top = _top(payload)
    text = card.build(top, inventory.load(payload.get("cwd")), external.load_caps(session_id))
    _emit("SessionStart", text + ("\n\n" + note if note else ""))
    _carded_ceiling(session_id, f"{top['model']}|{top['effort']}")


HANDLERS = {"prompt": on_prompt, "posttool": on_posttool, "pretool": on_pretool, "stop": on_stop, "sessionstart": on_session_start}


def run(event: str) -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if event == "precompact":
            return on_precompact(payload)
        HANDLERS[event](payload)
    except Exception:  # a hook must not break the session
        with (paths.home() / "errors.log").open("a") as log:
            log.write(f"{time.strftime('%F %T')} {event}\n{traceback.format_exc()}\n")
    return 0
