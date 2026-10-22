"""Other AIs as routing targets: detect their models, keep to the user's caps, call them headless, count their tokens,
and notice when one has run out of quota."""

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import inventory, paths, profiles, usage

SECRET_NAME = re.compile(
    r"(\.env|token|pass|secret|credential|\.ssh/|id_rsa|\.pem$|\.key$|netrc|kubeconfig|pgpass|\.aws/|\.docker/config\.json)", re.IGNORECASE
)
SECRET_TEXT = re.compile(
    r"(sk-[A-Za-z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[bp]-[A-Za-z0-9\-]{10,})"
)
QUOTA = re.compile(
    r"(quota|usage limit|rate.?limit|resource[_ ]exhausted|too many requests|\b429\b|limit (reached|exceeded)|out of credits|capacity)", re.IGNORECASE
)
AUTH = re.compile(
    r"(not logged in|authenticat|unauthori[sz]ed|ineligible|login required|please log ?in|invalid api key|\b401\b|\b403\b)", re.IGNORECASE
)
RESET = re.compile(
    r"(?:resets?|retry|try again|available)\s*(?:again\s*)?(?:in|after)\s*"
    r"(?:(\d+)\s*h(?:ours?|rs?)?)?\s*(?:(\d+)\s*m(?:in(?:ute)?s?)?)?\s*(?:(\d+)\s*s(?:ec(?:ond)?s?)?)?",
    re.IGNORECASE,
)
DEFAULT_QUOTA_HOURS = 5.0
AUTH_HOURS = 24.0
CAP_PHRASE = re.compile(r"\b(agy|gemini|codex)\s+(?:max|up to|at most|no more than|limited to)\s+([\w.\-]+)", re.IGNORECASE)
OFF_PHRASE = re.compile(r"\b(?:no|without|not|never|don'?t use|do not use|skip)\s+(?:use\s+)?(?:of\s+)?(agy|gemini|codex)\b", re.IGNORECASE)
TIMEOUT = int(os.environ.get("TOKEN_BEGGAR_EXTERNAL_TIMEOUT", "600"))
WRAPPER = (
    "You are a helper for one step of a larger task. Do only this step and answer plainly and briefly. You have no tools: "
    "work only from the text below. Do not invent anything that is not in the text; say so when the text does not answer.\n\nTASK: "
)


# ---- the user's caps -----------------------------------------------------------------------------------------------------


def parse_caps(prompt: str) -> dict[str, str]:
    """'agy max flash' caps agy at the flash models; 'no gemini' switches gemini off for the session."""
    caps = {m.group(1).lower(): m.group(2).lower() for m in CAP_PHRASE.finditer(prompt)}
    for match in OFF_PHRASE.finditer(prompt):
        caps.setdefault(match.group(1).lower(), "off")
    return caps


def _caps_file(session_id: str) -> Path:
    folder = paths.home() / "sessions"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session_id}.caps.json"


def load_caps(session_id: str | None) -> dict[str, str]:
    if not session_id:
        return {}
    try:
        return json.loads(_caps_file(session_id).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_caps(session_id: str, new: dict[str, str]) -> dict[str, str]:
    """Later prompts add to or replace earlier caps. 'agy max none' lifts one."""
    merged = {**load_caps(session_id), **new}
    merged = {k: v for k, v in merged.items() if v not in ("none", "any")}
    _caps_file(session_id).write_text(json.dumps(merged))
    return merged


LEVELS = ("low", "medium", "high")


def allowed(tool: str, model_id: str, caps: dict[str, str]) -> bool:
    """False when the user switched the tool off or capped it below this model.

    A family word ('flash') allows the models that carry it in their id. A level word ('medium') allows that level and the
    levels below it. A word nobody recognises allows only the lowest-capability model of the tool."""
    cap = caps.get(tool)
    if not cap:
        return True
    if cap == "off":
        return False
    model_id = model_id.lower()
    if cap in LEVELS:
        found = re.search(r"-(low|medium|high)\b", model_id)
        return bool(found) and LEVELS.index(found.group(1)) <= LEVELS.index(cap)
    if cap in model_id:
        return True
    spec = profiles.load()["external"].get(tool, {})
    if any(cap in row["match"] or cap in row["label"] for row in spec.get("models", [])):
        return False
    return profiles.external_model(tool, model_id)["capability"] <= 1


# ---- detecting models ----------------------------------------------------------------------------------------------------


def detect_models(tool: str) -> list[str]:
    """Model ids the tool reports. Only agy has a listing command; the others use their default model."""
    if tool != "agy" or os.environ.get("TOKEN_BEGGAR_OFFLINE") == "1":
        return []
    try:
        out = subprocess.run(["agy", "models"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.split("\t")[0].strip() for line in out.splitlines() if "\t" in line and not line.startswith("Fetching")]


# ---- calling ------------------------------------------------------------------------------------------------------------


def _refuse_secret(files: list[str], prompt: str) -> str | None:
    for name in files:
        if SECRET_NAME.search(name):
            return f"refusing {name}: it looks like a secret. Read it yourself and send only what is safe."
    if SECRET_TEXT.search(prompt):
        return "refusing: the prompt contains something that looks like a key or token."
    return None


MAX_FILES = 200


def _skipped(relative: Path) -> bool:
    return any(part.startswith(".") or part == "__pycache__" for part in relative.parts)


def expand(names: list[str]) -> list[str]:
    """Globs and directories become the plain files in them (hidden files and caches left out), in a stable order."""
    out: list[str] = []
    for name in names:
        hits = sorted(glob.glob(name, recursive=True)) or [name]
        for hit in hits:
            path = Path(hit)
            found = sorted(p for p in path.rglob("*") if p.is_file() and not _skipped(p.relative_to(path))) if path.is_dir() else [path]
            out += [str(p) for p in found if str(p) not in out]
    return out[:MAX_FILES]


def _body(files: list[str]) -> tuple[str, str | None]:
    out = []
    for name in files:
        try:
            text = Path(name).read_text(errors="replace")[-120_000:]
        except OSError as error:
            return "", f"cannot read {name}: {error.strerror}"
        out.append(f"\n===== FILE {name} =====\n{text}")
    return "".join(out), None


def build_command(tool: str, prompt: str, model: str | None) -> list[str]:
    if tool == "agy":
        return ["agy", "-p", prompt, *(["--model", model] if model and model != "default" else []), "--output-format", "json"]
    if tool == "gemini":
        return ["gemini", *(["-m", model] if model and model != "default" else []), "-o", "json", "-p", prompt]
    if tool == "codex":
        return ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", *(["-m", model] if model and model != "default" else []), prompt]
    raise ValueError(f"unknown tool {tool}")


def parse_output(tool: str, raw: str) -> tuple[str, int | None]:
    """(text, total tokens or None when the tool does not report them)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip(), None
    if tool == "agy":
        used = data.get("usage") or {}
        return str(data.get("response", "")).strip(), used.get("total_tokens") or (used.get("input_tokens", 0) + used.get("output_tokens", 0)) or None
    if tool == "gemini":
        models = ((data.get("stats") or {}).get("models") or {}).values()
        tokens = sum(((m.get("tokens") or {}).get("total") or 0) for m in models) or None
        return str(data.get("response", "")).strip(), tokens
    return raw.strip(), None


def reset_hours(text: str) -> float:
    """Hours until the quota comes back, read from the error text. Falls back to five hours."""
    for match in RESET.finditer(text):
        hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
        total = hours * 3600 + minutes * 60 + seconds
        if total:
            return max(total / 3600, 1 / 60)
    return DEFAULT_QUOTA_HOURS


def classify(text: str) -> tuple[str, float]:
    """('quota' | 'auth' | 'error', hours to wait)."""
    if QUOTA.search(text):
        return "quota", reset_hours(text)
    if AUTH.search(text):
        return "auth", AUTH_HOURS
    return "error", 0.0


def ask(tool: str, prompt: str, model: str | None = None, files: list[str] | None = None, session_id: str | None = None) -> dict:
    """Run one headless call. Returns {ok, text, tokens, tokens_source, error, kind}. Marks the tool or model out of quota when it says so."""
    files = expand(files or [])
    if not shutil.which(tool):
        return {"ok": False, "kind": "missing", "error": f"{tool} is not installed", "text": "", "tokens": 0}
    caps = load_caps(session_id)
    if not allowed(tool, model or "default", caps):
        return {"ok": False, "kind": "capped", "error": f"the user capped {tool} ('{caps.get(tool)}'); pick another route", "text": "", "tokens": 0}
    key = f"{tool}:{model}" if model and model != "default" else tool
    if key in profiles.exhausted(inventory.load()) or tool in profiles.exhausted(inventory.load()):
        return {"ok": False, "kind": "quota", "error": f"{key} is marked out of quota", "text": "", "tokens": 0}
    refused = _refuse_secret(files, prompt)
    if refused:
        return {"ok": False, "kind": "secret", "error": refused, "text": "", "tokens": 0}
    body, problem = _body(files)
    if problem:
        return {"ok": False, "kind": "error", "error": problem, "text": "", "tokens": 0}
    full = WRAPPER + prompt + body
    with tempfile.TemporaryDirectory() as empty:  # an empty directory: the helper cannot reach anything else
        try:
            proc = subprocess.run(
                build_command(tool, full, model), cwd=empty, capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL
            )
            raw, err, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired:
            return {"ok": False, "kind": "error", "error": f"{tool} timed out after {TIMEOUT}s", "text": "", "tokens": 0}
    text, tokens = parse_output(tool, raw)
    if code != 0 or not text:
        kind, hours = classify(f"{err}\n{raw}")
        if hours:
            inventory.mark_exhausted(key, hours)
        return {
            "ok": False,
            "kind": kind,
            "error": (err.strip() or raw.strip() or f"exit {code}")[-300:],
            "text": "",
            "tokens": 0,
            "wait_hours": hours,
        }
    source = "reported"
    if tokens is None:
        tokens, source = (len(full) + len(text)) // 4, "estimated"
    if session_id:
        usage.record(session_id, kind="external", tool=tool, model=model or "default", tokens=tokens, source=source)
    return {"ok": True, "kind": "ok", "text": text, "tokens": tokens, "tokens_source": source}


def short_name(tool: str, model: str | None) -> str:
    """'agy flash' for the footer."""
    if not model or model == "default":
        return tool
    label = profiles.external_model(tool, model)["label"]
    return f"{tool} {label}"
