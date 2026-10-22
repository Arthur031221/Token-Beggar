"""List every model the user can already reach, without asking for any new key."""

import json
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
    sources = [Path.home() / ".claude.json"]
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


def discover(cwd: str | None = None) -> dict:
    external = []
    for tool in catalog.load()["external"]:
        if shutil.which(tool["binary"]):
            external.append({"name": tool["name"], "kind": "cli", "note": tool["note"]})
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
