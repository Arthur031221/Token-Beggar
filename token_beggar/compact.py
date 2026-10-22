"""Dynamic compaction: find the real compaction point, warn before it, let the model say where it is in the work,
defer the compaction for a mid-step by an amount that fits the moment, optionally suggest an early /compact at a clean boundary (opt in),
and never lose the thread. A point the user set is theirs: the skill does not choose another, but the note and the mid-step deferral still work."""

import json
import os
import re
from pathlib import Path

from . import catalog, handoff, paths, transcript

WARN_FRACTION = 0.875  # the note is asked for this far into the compaction point...
WARN_ROOM = 30_000  # ...or this many tokens before it, whichever is earlier: one big tool result can jump past a small margin
DEFER_STEP = 0.05  # each deferral lifts the point by 5 percent of the window
MAX_DEFERRALS = 3
FRESH_NOTE_TOKENS = 15_000  # a note older than this much new context no longer describes the session
OUTPUT_RESERVE = 20_000  # Claude Code 2.1.308 keeps this much of the window for the reply
COMPACT_BUFFER = 13_000  # and compacts this far before that
BLOCK_MARGIN = 3_000  # past window - reserve - margin the host refuses requests
SAFETY = 5_000  # a deferral never gets closer than this to the blocking level
EARLY_FRACTION = 0.4  # a finished phase on a context this far into the point is worth compacting early
EARLY_FLOOR = 60_000  # but never on a context smaller than this: there is little to save
EARLY_CEILING = 150_000  # and on a large window do not wait past this: every later turn re-reads the whole context
MIN_WINDOW, MAX_WINDOW = 100_000, 1_000_000  # the host clamps the window setting to this range


def parse_window(value: str | None) -> int | None:
    """'400000', '400k' or '1m'."""
    if not value:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kKmM]?)\s*", value)
    if not match:
        return None
    scale = {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()]
    return int(float(match.group(1)) * scale)


def _settings_files(cwd: str | None) -> list[Path]:
    files = [paths.claude_dir() / "settings.json"]
    if cwd:
        files = [Path(cwd) / ".claude" / "settings.local.json", Path(cwd) / ".claude" / "settings.json"] + files
    return files


def _settings(cwd: str | None) -> list[dict]:
    out = []
    for file in _settings_files(cwd):
        try:
            out.append(json.loads(file.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _env(name: str, cwd: str | None) -> str | None:
    """A setting from the process environment, then the env block of the settings files."""
    if os.environ.get(name):
        return os.environ[name]
    for settings in _settings(cwd):
        value = (settings.get("env") or {}).get(name)
        if value not in (None, ""):
            return str(value)
    return None


def _per_model_window(settings: dict, model: catalog.Model | None) -> int | None:
    for key, block in (settings.get("modelSettings") or {}).items():
        found = catalog.find(key)
        if model and found and found.alias == model.alias and isinstance(block, dict) and block.get("autoCompactWindow") is not None:
            return parse_window(str(block["autoCompactWindow"]))
    return None


def configured_window(cwd: str | None = None, model: catalog.Model | None = None) -> tuple[int, str] | None:
    """The compaction window the user set, with where it came from. None when the host default applies."""
    raw = _env("CLAUDE_CODE_AUTO_COMPACT_WINDOW", cwd)
    if parse_window(raw):
        return min(max(parse_window(raw), MIN_WINDOW), MAX_WINDOW), "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
    for settings in _settings(cwd):
        per_model = _per_model_window(settings, model)
        if per_model:
            return per_model, "modelSettings.autoCompactWindow"
        if settings.get("autoCompactWindow") not in (None, "auto"):
            value = parse_window(str(settings["autoCompactWindow"]))
            if value:
                return value, "autoCompactWindow"
    return None


def disabled(cwd: str | None = None) -> bool:
    if any(_env(name, cwd) in ("1", "true", "True") for name in ("DISABLE_AUTO_COMPACT", "DISABLE_COMPACT")):
        return True
    return any(settings.get("autoCompactEnabled") is False for settings in _settings(cwd))


def resolve(cwd: str | None = None, model: catalog.Model | None = None) -> dict:
    """The compaction point the host will use, worked out the way Claude Code 2.1.308 does it.

    window = the setting, else the model's context window. The host reserves the reply size and compacts 13k before that,
    so threshold = window - 20k - 13k, or a percentage of window - 20k when CLAUDE_AUTOCOMPACT_PCT_OVERRIDE is set.
    `token-beggar window` prints this; `/context` in the host shows the same 33k buffer."""
    context = (model or catalog.find("sonnet")).context_window
    chosen = configured_window(cwd, model)
    window, source = (min(chosen[0], context), chosen[1]) if chosen else (context, "model default")
    usable = window - OUTPUT_RESERVE
    threshold = usable - COMPACT_BUFFER
    pct = _env("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", cwd)
    user_set = bool(chosen) or bool(pct)
    try:
        if pct and 0 < float(pct) <= 100:
            threshold = min(int(usable * float(pct) / 100), threshold)
            source += f" + CLAUDE_AUTOCOMPACT_PCT_OVERRIDE={pct}"
    except ValueError:
        pass
    blocked = context - OUTPUT_RESERVE - BLOCK_MARGIN
    return {
        "window": window,
        "source": source,
        "context_window": context,
        "threshold": threshold,
        "disabled": disabled(cwd),
        "user_set": user_set,
        "defer_limit": min(threshold + int(DEFER_STEP * MAX_DEFERRALS * window), blocked - SAFETY),
    }


def _state_file(session_id: str) -> Path:
    folder = paths.home() / "compact-state"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.json"


def _state(session_id: str) -> dict:
    try:
        return json.loads(_state_file(session_id).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save(session_id: str, **changes) -> None:
    _state_file(session_id).write_text(json.dumps({**_state(session_id), **changes}))


def mechanical_reason(items: list[dict]) -> str | None:
    """The fallback rule when the model left no fresh note: files were edited and no test, lint or build ran after the last edit."""
    unverified = transcript.unverified_edits(items)
    if unverified:
        return f"{len(unverified)} file(s) edited since the last test, lint or build"
    return None


def verdict(session_id: str, items: list[dict]) -> tuple[bool, str]:
    """(mid_step, why). A fresh note from the chat model decides. Without one, the mechanical rule does."""
    note = handoff.read_model(session_id)
    used = transcript.context_tokens(items)
    if note and used - note["used"] <= FRESH_NOTE_TOKENS:
        if note["mid_step"]:
            return True, "the model's note says it is in the middle of a step"
        return False, "the model's note says it is at a clean stopping point"
    if note and note["mid_step"]:  # an old mid-step note cannot show the step is over; deferral is bounded, so lean to finishing the step
        return True, "the model's last note said it was in the middle of a step and it has not said otherwise"
    reason = mechanical_reason(items)
    return (True, reason) if reason else (False, "no unfinished edits found")


def early_enabled() -> bool:
    """The early suggestion is opt in: the long-session benchmark measured it at no saving and a quality loss (see the README)."""
    return os.environ.get("TOKEN_BEGGAR_EARLY", "").lower() in ("1", "on", "true", "yes")


def early_point(point: dict) -> int:
    return min(EARLY_CEILING, max(EARLY_FLOOR, int(EARLY_FRACTION * point["threshold"])))


def deferral_plan(session_id: str, point: dict) -> dict:
    """How the skill wants to treat this moment. A point the user set is used as it is: the skill stops choosing it (no early
    suggestion), but a mid-step compaction is still deferred from that point.

    A phase that just ended on a long context means compact soon (the host cannot be told to compact early, so the user is
    asked to type /compact). A step that is mid-way is deferred in steps of 5 percent of the window, as many as the work left needs:
    all of them when the later work depends on early detail, one when the step is nearly done. Always below the host's blocking level."""
    note = handoff.read_model(session_id) or {}
    if note.get("phase") == "done" and not point["user_set"]:
        return {"mode": "early", "deferrals": 0, "wanted": early_point(point), "why": "the last phase is finished, so compact early"}
    progress = note.get("progress")
    if note.get("needs_detail") or progress is None:
        count = MAX_DEFERRALS
    else:
        count = min(MAX_DEFERRALS, max(1, round((1 - progress) * MAX_DEFERRALS + 0.4)))
    wanted = min(point["threshold"] + int(DEFER_STEP * count * point["window"]), point["defer_limit"])
    return {"mode": "defer", "deferrals": count, "wanted": wanted, "why": "mid-step: finish it before compacting"}


def warn_point(threshold: int) -> int:
    """The context size where the model is asked for its note: early enough that one large tool result cannot jump past the point."""
    return max(int(threshold * 0.5), min(int(WARN_FRACTION * threshold), threshold - WARN_ROOM))


def command() -> str:
    return str(paths.PACKAGE_ROOT / "bin" / "token-beggar")


def usage_notice(session_id: str, items: list[dict], point: dict) -> str | None:
    """Ask the chat model for a note when the context nears the compaction point. Throttled, so a long turn is not nagged."""
    if point["disabled"]:
        return None
    used = transcript.context_tokens(items)
    early = early_notice(session_id, used, point)
    if early:
        return early
    if used < warn_point(point["threshold"]):
        return None
    state, step = _state(session_id), max(10_000, int(0.025 * point["threshold"]))
    note = handoff.read_model(session_id)
    if note and used - note["used"] < step:
        return None
    if used - state.get("warned_at", -(10**9)) < step:
        return None
    _save(session_id, warned_at=used)
    over = " The point has been passed, so the host may compact at any moment." if used >= point["threshold"] else ""
    return (
        f"Token Beggar: context is about {used // 1000}k of a {point['threshold'] // 1000}k compaction point.{over} "
        "Judge now whether you are in the middle of a step: edits not yet verified, a change half done across files, a plan with open items. "
        "Then run once, with your own words on stdin: "
        f"{command()} note --mid-step (or --clean) <<'EOF' ... EOF. "
        "Put in it the goal, the decisions and why, open threads, file paths, and the next steps in order. "
        "Add --progress 0.0 to 1.0 for how far the current step is, --needs-early-detail if the next work depends on early details, "
        "or --phase-done instead of --clean if a phase just finished. "
        "A mid-step note defers the compaction a little so you can finish the step. The note is read back after the compaction."
    )


def early_notice(session_id: str, used: int, point: dict) -> str | None:
    """On a long context, once per stage: ask the model whether a phase just finished, and if so to suggest /compact to the user.
    Compacting at a clean boundary drops the raw reading the finished phase needed and keeps what the next phase needs, so every
    later turn re-reads less."""
    if not early_enabled() or point["user_set"] or used < early_point(point) or used >= warn_point(point["threshold"]):
        return None
    state = _state(session_id)
    last = state.get("suggested_at", -(10**9))
    if used < last - 20_000:  # the context shrank, so a compaction happened since
        last = -(10**9)
    if used - last < max(50_000, int(0.1 * point["threshold"])):
        return None
    _save(session_id, suggested_at=used)
    note = handoff.read_model(session_id)
    finished = note and note.get("phase") == "done" and used - note["used"] <= FRESH_NOTE_TOKENS
    lead = f"Token Beggar: context is {used // 1000}k. "
    if finished:
        return (
            lead + "Your note says the last phase is finished. Tell the user in one line that this is a good moment to type /compact "
            "(the note is read back after it). Say nothing more about it until the next phase ends."
        )
    return (
        lead + "If you have just finished a phase and the rest of the work does not depend on its raw details (file contents, long outputs), "
        f"run once: {command()} note --phase-done <<'EOF' ... EOF with the goal, decisions and why, what was found, file paths and next steps, "
        "then tell the user in one line that this is a good moment to type /compact: later turns re-read the whole context, "
        "so compacting now is cheaper. "
        "If the next work needs those details, run the same with --needs-early-detail instead of --phase-done and say nothing to the user. "
        "If you are in the middle of a step, ignore this."
    )


def on_precompact(payload: dict, model: catalog.Model | None = None) -> tuple[int, str]:
    """Return (exit_code, message). Exit 2 defers an automatic compaction."""
    session_id = payload.get("session_id", "unknown")
    items = transcript.entries(payload["transcript_path"]) if payload.get("transcript_path") else []
    handoff.write(session_id, items, payload.get("cwd"))
    handoff.prune()
    point = resolve(payload.get("cwd"), model)
    if payload.get("trigger") != "auto" or point["disabled"]:
        return 0, ""
    used = transcript.context_tokens(items)
    _save(session_id, compacted_at=used)
    count = _state(session_id).get("deferrals", 0)
    mid_step, why = verdict(session_id, items)
    plan = deferral_plan(session_id, point)
    allowed = plan["deferrals"] if plan["mode"] == "defer" else 0
    if mid_step and count < allowed and used < point["defer_limit"]:
        _save(session_id, deferrals=count + 1, deferred=True)
        return 2, f"Token Beggar deferred compaction ({count + 1}/{allowed}): {why}. Finish the step and run the tests."
    _save(session_id, deferrals=0, deferred=False)
    return 0, ""


def deferred_notice(session_id: str) -> str | None:
    """After a deferral the model hears about it once, on the next tool call or prompt."""
    if not _state(session_id).get("deferred"):
        return None
    _save(session_id, deferred=False)
    return (
        "Token Beggar deferred the compaction because you are mid-step. Finish the step and run the check now. "
        f"Then update your note with {command()} note --clean so the next compaction goes through."
    )


def on_session_start(payload: dict) -> str | None:
    """After a compaction, put the notes back in front of the model: its own note first, the mechanical extract as the fallback."""
    if payload.get("source") != "compact":
        return None
    session_id = payload.get("session_id", "")
    own = handoff.read_model(session_id)
    extract = handoff.read(session_id)
    if own:
        behind = _state(session_id).get("compacted_at", own["used"]) - own["used"]
        if behind > FRESH_NOTE_TOKENS:  # the model wrote it a good while before the compaction, so work has happened since
            text = (
                f"Token Beggar restored the note you wrote, but it is about {behind // 1000}k tokens older than the compaction, "
                "so it may be behind. The extract below is the later record; trust it where they differ:\n\n"
            )
            return text + (extract + "\n\nYour older note:\n" if extract else "") + own["text"]
        text = "Token Beggar restored the note you wrote before the compaction:\n\n" + own["text"]
        return text + ("\n\n(Mechanical extract of the transcript, in case the note missed something:\n" + extract + ")" if extract else "")
    if extract:
        return "Token Beggar restored this note from before the compaction:\n\n" + extract
    return None
