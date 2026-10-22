"""Where Token Beggar keeps its files."""

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def home() -> Path:
    """Per-user state directory. TOKEN_BEGGAR_HOME overrides it (tests, CI)."""
    override = os.environ.get("TOKEN_BEGGAR_HOME")
    base = Path(override) if override else Path.home() / ".claude" / "token-beggar"
    base.mkdir(parents=True, exist_ok=True)
    return base


def data_file(name: str) -> Path:
    """A data file shipped with the plugin."""
    return PACKAGE_ROOT / "data" / name


def claude_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
