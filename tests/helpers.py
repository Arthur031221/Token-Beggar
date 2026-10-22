"""Shared test setup: an isolated state directory and builders for transcript entries."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from token_beggar import ceiling

ENV_KEYS = ("ANTHROPIC_MODEL", "CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_AUTO_COMPACT_WINDOW", "TOKEN_BEGGAR")


class Isolated(unittest.TestCase):
    """Own state dir, own Claude config dir, no inherited model or effort settings."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
        env.update(TOKEN_BEGGAR_HOME=str(self.tmp / "tb"), CLAUDE_CONFIG_DIR=str(self.tmp / "claude"), TOKEN_BEGGAR_OFFLINE="1", TOKEN_BEGGAR_MODE="full")
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        ancestors = mock.patch.object(ceiling, "_ancestor_args", return_value=[])
        ancestors.start()
        self.addCleanup(ancestors.stop)
        (self.tmp / "claude").mkdir()

    def settings(self, **values) -> None:
        (self.tmp / "claude" / "settings.json").write_text(json.dumps(values))


def user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def assistant(text: str = "", tools: list[dict] | None = None, model: str = "claude-opus-5-5", tokens: int = 1000, sidechain: bool = False) -> dict:
    content = ([{"type": "text", "text": text}] if text else []) + [
        {"type": "tool_use", "id": f"t{i}", "name": name, "input": data} for i, (name, data) in enumerate(tools or [])
    ]
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {"role": "assistant", "model": model, "content": content, "usage": {"input_tokens": tokens, "output_tokens": 10}},
    }


def edit(path: str) -> tuple[str, dict]:
    return "Edit", {"file_path": path}


def bash(command: str) -> tuple[str, dict]:
    return "Bash", {"command": command}


def write_transcript(path: Path, items: list[dict]) -> str:
    path.write_text("\n".join(json.dumps(i) for i in items) + "\n")
    return str(path)
