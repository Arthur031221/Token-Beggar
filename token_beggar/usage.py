"""Token accounting for one reply: the main chat plus every subagent, and the external AIs separately."""

import json
import time
from datetime import datetime
from pathlib import Path

from . import catalog, paths, transcript

FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
HUMAN_SKIP = ("This session is being continued", "<system-reminder>", "<command-", "<local-command", "[Request interrupted")


def total(usage: dict | None) -> int:
    """input + output + cache read + cache write."""
    return sum(v for k in FIELDS if isinstance(v := (usage or {}).get(k), int | float))


def find_transcript(session_id: str) -> Path | None:
    for path in (paths.claude_dir() / "projects").glob(f"*/{session_id}.jsonl"):
        return path
    return None


def _is_human(entry: dict) -> bool:
    if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else [b for b in content or [] if isinstance(b, dict)]
    texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    return bool(texts) and not any(b.get("type") == "tool_result" for b in blocks) and not texts[0].startswith(HUMAN_SKIP)


def reply_window(items: list[dict]) -> list[dict]:
    """Everything since the last prompt a human typed."""
    start = 0
    for index, entry in enumerate(items):
        if _is_human(entry):
            start = index
    return items[start:]


def _seconds(entry: dict) -> float:
    try:
        return datetime.fromisoformat(str(entry.get("timestamp")).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def prompt_text(window: list[dict]) -> str:
    for entry in window[:1]:
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        return " ".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _price(model_id: str | None, fallback: catalog.Model | None, usage: dict) -> float:
    """Dollars at the list price of the model that made the call; the fallback model when the record does not name one."""
    model = catalog.find(model_id) or fallback
    return model.cost(usage) if model else 0.0


def _unique_usage(path: Path, fallback: catalog.Model | None = None) -> tuple[int, float] | None:
    """(tokens, dollars) of every distinct assistant message in a transcript file. A message is logged once per content block."""
    seen: dict[str, tuple[int, float]] = {}
    try:
        for line in path.read_text().splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = entry.get("message") or {}
            if entry.get("type") == "assistant" and message.get("usage"):
                seen[message.get("id") or f"anon{len(seen)}"] = (total(message["usage"]), _price(message.get("model"), fallback, message["usage"]))
    except OSError:
        return None
    return sum(t for t, _ in seen.values()), sum(c for _, c in seen.values())


def agent_usage(transcript_path: str | None, agent_id: str, fallback: dict | None, model_id: str | None) -> tuple[int, float, bool]:
    """(tokens, dollars, exact). The subagent's own transcript has every call. The usage in the parent's tool result covers only the last call."""
    worker = catalog.find(model_id)
    if transcript_path:
        main = Path(transcript_path)
        found = _unique_usage(main.with_suffix("") / "subagents" / f"agent-{agent_id}.jsonl", worker)
        if found is not None:
            return found[0], found[1], True
    return total(fallback), _price(model_id, None, fallback or {}), False


def tally(window: list[dict], transcript_path: str | None = None) -> dict:
    """Tokens and list-price dollars of the main chain (once per message id) and of every finished subagent (once per agent id)."""
    messages: dict[str, tuple[int, float]] = {}
    for entry in transcript.main_chain(window):
        message = entry.get("message") or {}
        if entry["type"] == "assistant" and message.get("usage"):
            key = message.get("id") or f"anon{len(messages)}"
            now = (total(message["usage"]), _price(message.get("model"), None, message["usage"]))
            messages[key] = max(messages.get(key, (0, 0.0)), now)
    uses: dict[str, dict] = {}
    done: dict[str, dict] = {}
    for entry in window:
        for block in transcript._blocks(entry):
            if block.get("type") == "tool_use" and block.get("name") in ("Task", "Agent"):
                uses[block.get("id")] = block.get("input") or {}
        result = entry.get("toolUseResult")
        if isinstance(result, dict) and result.get("agentId") and result["agentId"] not in done:
            call = next((b.get("tool_use_id") for b in transcript._blocks(entry) if b.get("type") == "tool_result"), None)
            asked = uses.get(call, {})
            model_id = result.get("resolvedModel") or asked.get("model")
            tokens, dollars, exact = agent_usage(transcript_path, result["agentId"], result.get("usage"), model_id)
            done[result["agentId"]] = {
                "id": call,
                "model": result.get("resolvedModel"),
                "input": asked,
                "tokens": tokens,
                "cost": dollars,
                "exact": exact,
            }
    dispatches = list(done.values())
    return {
        "main": sum(t for t, _ in messages.values()),
        "agents": sum(d["tokens"] for d in dispatches),
        "main_cost": sum(c for _, c in messages.values()),
        "agents_cost": sum(d["cost"] for d in dispatches),
        "dispatches": dispatches,
        "pending": sum(1 for u in uses if u not in {d["id"] for d in dispatches}),
    }


def edited_files(window: list[dict]) -> set[str]:
    files = set()
    for _, block in transcript.tool_calls(window):
        if block.get("name") in transcript.EDIT_TOOLS:
            data = block.get("input") or {}
            if data.get("file_path") or data.get("notebook_path"):
                files.add(data.get("file_path") or data.get("notebook_path"))
    return files


# ---- the per session ledger: what the transcript cannot tell ----------------------------------------------------


def _ledger(session_id: str) -> Path:
    folder = paths.home() / "ledger"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.jsonl"


def record(session_id: str, **fields) -> None:
    with _ledger(session_id).open("a") as handle:
        handle.write(json.dumps({"t": time.time(), **fields}) + "\n")


def ledger(session_id: str, since: float = 0.0) -> list[dict]:
    out = []
    try:
        for line in _ledger(session_id).read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("t", 0) >= since:
                out.append(row)
    except OSError:
        pass
    return out


def display_name(model: catalog.Model | None) -> str:
    """claude-opus-5-5 -> Opus 5.5"""
    if not model:
        return "the chat model"
    parts = model.id.split("-")[2:]
    return f"{model.alias.capitalize()} {'.'.join(parts)}" if parts else model.alias.capitalize()


def prune(days: int = 14) -> None:
    cutoff = time.time() - days * 86400
    for old in (paths.home() / "ledger").glob("*.jsonl"):
        if old.stat().st_mtime < cutoff:
            old.unlink(missing_ok=True)
