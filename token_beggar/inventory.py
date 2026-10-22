"""List every model the user can already reach, without asking for any new key."""

import json
import os
import re
import shutil
import time
from pathlib import Path

from . import catalog, paths

REFRESH_SECONDS = 7 * 24 * 3600


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _mcp_servers(cwd: str | None) -> list[str]:
    names: set[str] = set()
    sources = [(paths.claude_dir() / ".claude.json") if os.environ.get("CLAUDE_CONFIG_DIR") else Path.home() / ".claude.json"]
    if cwd:
        sources.append(Path(cwd) / ".mcp.json")
    for source in sources:
        names.update((_json(source).get("mcpServers") or {}).keys())
    return sorted(names)


def _denied_aliases(cwd: str | None) -> set[str]:
    """Aliases the user's settings block with deniedModels, or leave out of availableModels."""
    denied: set[str] = set()
    files = [paths.claude_dir() / "settings.json"]
    if cwd:
        files.append(Path(cwd) / ".claude" / "settings.json")
    for file in files:
        settings = _json(file)
        listed = settings.get("availableModels")
        for model in catalog.models():
            if listed is not None and not any(model.alias in e or model.id in e for e in listed):
                denied.add(model.alias)
        for entry in settings.get("deniedModels") or []:
            found = catalog.find(entry)
            if found:
                denied.add(found.alias)
    return denied


AI_SERVER = re.compile(r"(gemini|codex|openai|gpt|llm|ollama|agy|antigravity|deepseek|mistral|grok|perplexity)", re.IGNORECASE)


def discover(cwd: str | None = None) -> dict:
    from . import external as external_ais  # late import: external uses this module

    external = []
    only = os.environ.get("TOKEN_BEGGAR_EXTERNAL")  # a comma list of the external tools routing may use; "none" turns them all off
    allowed = None if only is None else {n.strip() for n in only.split(",") if n.strip()}
    for tool in catalog.load()["external"]:
        if allowed is not None and tool["name"] not in allowed:
            continue
        if shutil.which(tool["binary"]):
            external.append({"name": tool["name"], "kind": "cli", "note": tool["note"], "models": external_ais.detect_models(tool["name"])})
    for server in _mcp_servers(cwd):  # an MCP server that fronts another AI is a route too
        if allowed is None and AI_SERVER.search(server) and not any(server in e["name"] for e in external):
            external.append({"name": server, "kind": "mcp", "note": f"MCP server {server}: call its tools directly", "models": []})
    return {
        "checked_at": int(time.time()),
        "claude": [m.alias for m in catalog.models() if m.alias not in _denied_aliases(cwd)],
        "external": external,
        "mcp_servers": _mcp_servers(cwd),
    }


def _file() -> Path:
    return paths.home() / "inventory.json"


def load(cwd: str | None = None, max_age: int = REFRESH_SECONDS) -> dict:
    """The stored inventory, rebuilt on first run and when older than max_age."""
    stored = _json(_file())
    if stored and time.time() - stored.get("checked_at", 0) < max_age:
        return stored
    fresh = discover(cwd)
    fresh["exhausted"] = stored.get("exhausted", {})
    _file().write_text(json.dumps(fresh, indent=2))
    return fresh


def exhausted_aliases(inventory: dict, now: float | None = None) -> set[str]:
    now = now or time.time()
    return {alias for alias, until in (inventory.get("exhausted") or {}).items() if until > now}


def mark_exhausted(alias: str, hours: float = 5.0) -> dict:
    """Remember that a model hit its quota. Routing skips it until the time passes."""
    inventory = load()
    inventory.setdefault("exhausted", {})[alias] = time.time() + hours * 3600
    _file().write_text(json.dumps(inventory, indent=2))
    return inventory


def clear_exhausted(alias: str | None = None) -> dict:
    inventory = load()
    if alias:
        inventory.get("exhausted", {}).pop(alias, None)
    else:
        inventory["exhausted"] = {}
    _file().write_text(json.dumps(inventory, indent=2))
    return inventory
