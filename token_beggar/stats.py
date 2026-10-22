"""What delegation actually moved, read from the user's own Claude Code transcripts."""

import time
from pathlib import Path

from . import catalog, paths, transcript

WORKER_SUFFIX = "beggar-worker"
CACHE_READ = 0.1  # list price multipliers for cached prompt tokens
CACHE_WRITE = 1.25


def _count(usage: dict, key: str) -> int:
    value = usage.get(key)
    return value if isinstance(value, int | float) else 0


def _cost(usage: dict, model: catalog.Model) -> float:
    fresh = _count(usage, "input_tokens") + _count(usage, "cache_read_input_tokens") * CACHE_READ
    fresh += _count(usage, "cache_creation_input_tokens") * CACHE_WRITE
    return (fresh * model.input_per_mtok + _count(usage, "output_tokens") * model.output_per_mtok) / 1e6


def _chat_models(items: list[dict]) -> dict[str, str]:
    """Tool call id -> model of the main chat message that made the call."""
    found = {}
    for entry in transcript.main_chain(items):
        if entry["type"] == "assistant":
            model = (entry.get("message") or {}).get("model")
            for block in transcript._blocks(entry):
                if block.get("type") == "tool_use" and model:
                    found[block.get("id")] = model
    return found


def worker_runs(items: list[dict], seen: set | None = None) -> list[dict]:
    """Finished Token Beggar workers in one transcript, once per agent, with the chat model that started each."""
    chat = _chat_models(items)
    seen = set() if seen is None else seen
    runs = []
    for entry in items:
        result = entry.get("toolUseResult")
        if not isinstance(result, dict) or not str(result.get("agentType", "")).endswith(WORKER_SUFFIX):
            continue
        usage, agent = result.get("usage"), result.get("agentId")
        if not usage or (agent and agent in seen):  # a background launch carries no usage yet
            continue
        seen.add(agent)
        call = next((b.get("tool_use_id") for b in transcript._blocks(entry) if b.get("type") == "tool_result"), None)
        runs.append({"worker": result.get("resolvedModel"), "chat": chat.get(call), "usage": usage})
    return runs


def transcripts(days: float, root: Path | None = None) -> list[Path]:
    base = (root or paths.claude_dir()) / "projects"
    cutoff = time.time() - days * 86400
    found = []
    for path in base.glob("*/*.jsonl"):
        try:
            if path.stat().st_mtime >= cutoff:
                found.append(path)
        except OSError:  # deleted between the listing and the check
            continue
    return found


def _mentions_worker(path: Path) -> bool:
    """Cheap pre-filter so a long history is not parsed line by line."""
    try:
        return WORKER_SUFFIX.encode() in path.read_bytes()
    except OSError:
        return False


def summarize(files: list[Path]) -> dict:
    """Per worker model: runs, tokens, what they cost, and what the same tokens cost at the chat model's price."""
    rows: dict[str, dict] = {}
    seen: set = set()  # an agent copied into a resumed session's file is still one run
    skipped = 0
    for path in filter(_mentions_worker, files):
        for run in worker_runs(transcript.entries(path), seen):
            worker, chat = catalog.find(run["worker"]), catalog.find(run["chat"])
            if not worker or not chat:
                skipped += 1
                continue
            row = rows.setdefault(worker.alias, {"runs": 0, "tokens": 0, "worker_usd": 0.0, "chat_usd": 0.0})
            usage = run["usage"]
            row["runs"] += 1
            row["tokens"] += sum(
                _count(usage, k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")
            )
            row["worker_usd"] += _cost(usage, worker)
            row["chat_usd"] += max(_cost(usage, chat), _cost(usage, worker))
    total = {k: sum(r[k] for r in rows.values()) for k in ("runs", "tokens", "worker_usd", "chat_usd")}
    return {"sessions": len(files), "workers": rows, "total": total, "skipped": skipped}


def render(data: dict, days: float) -> str:
    total = data["total"]
    span = f"the last {days:g} days"
    left_out = (
        f"{data['skipped']} workers were left out because their model or the chat model is missing from the catalog." if data["skipped"] else ""
    )
    if not total["runs"]:
        return "\n".join(filter(None, [f"No Token Beggar workers ran in {span} ({data['sessions']} sessions checked).", left_out]))

    def money(value: float) -> str:
        return f"${value:.2f}"

    def row(label: str, r: dict) -> str:
        return f"{label:<8}{r['runs']:>6}{r['tokens']:>12,}{money(r['worker_usd']):>10}{money(r['chat_usd']):>16}"

    out = [f"Token Beggar workers in {span}, {data['sessions']} sessions", f"{'worker':<8}{'runs':>6}{'tokens':>12}{'cost':>10}{'at chat price':>16}"]
    out += [row(alias, r) for alias, r in sorted(data["workers"].items())]
    out.append(row("total", total))
    out.append("")
    out.append("'At chat price' is the same tokens billed at the model that started each worker. It is an upper bound on what")
    out.append("delegation moved, not the net saving: the chat model would not have used identical tokens. The measured")
    out.append("net saving is in the README. List prices. Cached tokens at 0.1x read and 1.25x write.")
    if left_out:
        out.append(left_out)
    return "\n".join(out)
