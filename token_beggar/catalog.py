"""The model catalog: which Claude models exist, how they rank and what they cost."""

import json
from dataclasses import dataclass

from . import paths

EFFORTS = ["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Model:
    alias: str
    id: str
    tier: int
    input_per_mtok: float
    output_per_mtok: float
    default_effort: str


def _load_json() -> dict:
    """The newer of the shipped file and the weekly refresh in the user's state directory."""
    found = []
    for candidate in (paths.home() / "models.json", paths.data_file("models.json")):
        try:
            found.append(json.loads(candidate.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    if not found:
        raise FileNotFoundError("no models.json found")
    return max(found, key=lambda data: data.get("updated", ""))


def load() -> dict:
    return _load_json()


def models() -> list[Model]:
    rows = _load_json()["claude"]
    return sorted(
        (Model(r["alias"], r["id"], r["tier"], r["input_per_mtok"], r["output_per_mtok"], r["default_effort"]) for r in rows),
        key=lambda m: m.tier,
    )


def find(model_id_or_alias: str | None) -> Model | None:
    """Match 'claude-opus-5-5', 'opus', or an id with a context suffix such as 'claude-opus-5-5[1m]'."""
    if not model_id_or_alias:
        return None
    text = model_id_or_alias.lower().split("[")[0]
    for m in models():
        if text in (m.id, m.alias):
            return m
    for m in models():
        if text.startswith(f"claude-{m.alias}"):
            return m
    return None


def effort_rank(effort: str) -> int:
    return EFFORTS.index(effort) if effort in EFFORTS else EFFORTS.index("high")


def cap_effort(wanted: str, ceiling: str) -> str:
    return wanted if effort_rank(wanted) <= effort_rank(ceiling) else ceiling
