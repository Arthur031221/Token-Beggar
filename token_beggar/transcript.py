"""Read facts out of a Claude Code session transcript (JSON lines)."""

import json
import re
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
CHECK_COMMANDS = re.compile(
    r"^(?:(?:python3?|uv run|uvx)\s+(?:-m\s+)?)?(?:pytest|unittest|ruff|mypy|flake8|pylint|jest|vitest|tsc|eslint)\b"
    r"|^(?:go|cargo|dotnet|mvn|gradle)\s+(?:test|build|vet|check|clippy)\b"
    r"|^(?:npm|yarn|pnpm|bun)\s+(?:run\s+)?(?:test|build|lint|check)\b"
    r"|^make(?:\s+(?:test|check|build|lint))?\s*$"
    r"|^(?:python3?\s+)?\S*(?:selftest|run_tests?|runtests)\S*\.py\b"
)
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
ENV_ASSIGNMENT = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)+")


def entries(path: str | Path) -> list[dict]:
    out = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return out


def _blocks(entry: dict) -> list[dict]:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def main_chain(items: list[dict]) -> list[dict]:
    return [e for e in items if e.get("type") in ("user", "assistant") and not e.get("isSidechain")]


def context_tokens(items: list[dict]) -> int:
    """Prompt size of the latest main-chain request: fresh input plus cache reads and writes."""
    for entry in reversed(main_chain(items)):
        usage = (entry.get("message") or {}).get("usage")
        if entry["type"] == "assistant" and usage:
            return (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("output_tokens", 0)
            )
    return 0


def user_prompts(items: list[dict]) -> list[str]:
    """What the human typed, without tool results and without the compaction summary."""
    prompts = []
    for entry in main_chain(items):
        if entry["type"] != "user":
            continue
        for block in _blocks(entry):
            text = block.get("text", "") if block.get("type") == "text" else ""
            if text and not text.startswith(("This session is being continued", "<system-reminder>", "<command-")):
                prompts.append(text)
    return prompts


def tool_calls(items: list[dict]) -> list[tuple[int, dict]]:
    """Every tool call in order, with the position of its message."""
    calls = []
    for index, entry in enumerate(main_chain(items)):
        if entry["type"] == "assistant":
            for block in _blocks(entry):
                if block.get("type") == "tool_use":
                    calls.append((index, block))
    return calls


def last_assistant_text(items: list[dict]) -> str:
    for entry in reversed(main_chain(items)):
        if entry["type"] == "assistant":
            text = " ".join(b.get("text", "") for b in _blocks(entry) if b.get("type") == "text").strip()
            if text:
                return text
    return ""


def is_check_command(command: str) -> bool:
    """True when any step of a shell line runs a test runner, linter or build, not merely names one in a path."""
    for segment in SEGMENT_SPLIT.split(command):
        if CHECK_COMMANDS.match(ENV_ASSIGNMENT.sub("", segment.strip())):
            return True
    return False


def unverified_edits(items: list[dict]) -> list[str]:
    """Files edited after the last test, lint or build command."""
    last_check = -1
    for index, block in tool_calls(items):
        if block.get("name") == "Bash" and is_check_command(str((block.get("input") or {}).get("command", ""))):
            last_check = index
    files = []
    for index, block in tool_calls(items):
        if index > last_check and block.get("name") in EDIT_TOOLS:
            file = (block.get("input") or {}).get("file_path") or (block.get("input") or {}).get("notebook_path")
            if file and file not in files:
                files.append(file)
    return files


def todos(items: list[dict]) -> list[dict]:
    latest: list[dict] = []
    for _, block in tool_calls(items):
        if block.get("name") == "TodoWrite":
            latest = (block.get("input") or {}).get("todos") or latest
    return latest
