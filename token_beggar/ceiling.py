"""Find the model and effort of the user's own chat. These are the upper limit for routing."""

import json
import os
import subprocess
from pathlib import Path

from . import catalog, paths


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _settings_files(cwd: str | None) -> list[Path]:
    """Highest precedence first, as Claude Code reads them."""
    files = []
    if cwd:
        files += [Path(cwd) / ".claude" / "settings.local.json", Path(cwd) / ".claude" / "settings.json"]
    files.append(paths.claude_dir() / "settings.json")
    return files


def model_from_transcript(transcript_path: str | None) -> str | None:
    """The model of the last main-chain assistant message, read from the tail of the transcript."""
    if not transcript_path:
        return None
    path = Path(transcript_path)
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(0, size - 400_000))
            tail = handle.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return None
    for line in reversed(tail):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message") or {}
        if entry.get("type") == "assistant" and not entry.get("isSidechain") and message.get("model"):
            model = message["model"]
            if catalog.find(model):
                return model
    return None


def _ancestor_args(depth: int = 5) -> list[list[str]]:
    """Command lines of the parent processes. A hook runs as a child of the claude process."""
    out, pid = [], os.getppid()
    for _ in range(depth):
        if pid <= 1:
            break
        try:
            raw = Path(f"/proc/{pid}/cmdline").read_bytes()
            args = [a for a in raw.decode("utf-8", "ignore").split("\0") if a]
            ppid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            try:
                args = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout.split()
                ppid = int(subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout)
            except (OSError, ValueError, subprocess.SubprocessError):
                break
        out.append(args)
        pid = ppid
    return out


def _flag(args: list[str], name: str) -> str | None:
    for i, arg in enumerate(args):
        if arg == name and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith(name + "="):
            return arg.split("=", 1)[1]
    return None


def launch_flag(name: str) -> str | None:
    """Value of a launch flag such as --model or --effort on the claude process that started this hook."""
    for args in _ancestor_args():
        if any(Path(a).name in ("claude", "claude.exe") for a in args[:3]) or any("claude" in a for a in args[:2]):
            value = _flag(args, name)
            if value:
                return value
    return None


def model_from_settings(cwd: str | None) -> str | None:
    flag = launch_flag("--model")
    if flag:
        return flag
    if os.environ.get("ANTHROPIC_MODEL"):
        return os.environ["ANTHROPIC_MODEL"]
    for file in _settings_files(cwd):
        model = _read_json(file).get("model")
        if model:
            return model
    return None


def effort_from_settings(cwd: str | None) -> tuple[str | None, str]:
    """Effort is not exposed to hooks, so read the places the user can set it."""
    flag = launch_flag("--effort")
    if flag:
        return flag, "--effort"
    env = os.environ.get("CLAUDE_CODE_EFFORT_LEVEL")
    if env and env != "auto":
        return env, "CLAUDE_CODE_EFFORT_LEVEL"
    for file in _settings_files(cwd):
        level = _read_json(file).get("effortLevel")
        if level:
            return level, str(file)
    return None, "default"


def resolve(transcript_path: str | None, cwd: str | None, effort_hint: str | None = None) -> dict:
    """Best known ceiling. `known` is False when the model had to be guessed. A hook payload that carries the effort wins."""
    raw = model_from_transcript(transcript_path) or model_from_settings(cwd)
    model = catalog.find(raw)
    effort, source = effort_from_settings(cwd)
    if effort_hint in catalog.EFFORTS:
        effort, source = effort_hint, "hook payload"
    if effort is None:
        effort = model.default_effort if model else "high"
    return {
        "model": model.id if model else None,
        "alias": model.alias if model else None,
        "tier": model.tier if model else None,
        "effort": effort,
        "effort_source": source,
        "known": model is not None,
    }
