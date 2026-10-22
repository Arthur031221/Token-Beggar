"""The model catalog: which Claude models exist, how they rank and what they cost."""

import json
from dataclasses import dataclass

from . import paths

EFFORTS = ["low", "medium", "high", "xhigh", "max"]
CACHE_READ_X, CACHE_WRITE_X = 0.05, 2.0  # when the price page gives no cache prices: the multiples of the input price seen on 5.5 models


@dataclass(frozen=True)
class Model:
    alias: str
    id: str
    tier: int
    input_per_mtok: float
    output_per_mtok: float
    default_effort: str
    context_window: int = 1_000_000
    cache_read_per_mtok: float = 0.0
    cache_write_per_mtok: float = 0.0

    def cost(self, usage: dict | None) -> float:
        """List price in dollars of one usage record: input, output, cache read and cache write each at this model's own price."""
        usage = usage or {}

        def count(key: str) -> float:
            value = usage.get(key)
            return float(value) if isinstance(value, int | float) else 0.0

        return (
            count("input_tokens") * self.input_per_mtok
            + count("output_tokens") * self.output_per_mtok
            + count("cache_read_input_tokens") * self.cache_read_per_mtok
            + count("cache_creation_input_tokens") * self.cache_write_per_mtok
        ) / 1e6


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
    newest = max(found, key=lambda data: data.get("updated", ""))
    for row in newest.get("claude", []):  # a refreshed file has no cache prices: take them from another copy with the same input price
        for other in found:
            for old in other.get("claude", []):
                if old.get("id") == row.get("id") and old.get("input_per_mtok") == row.get("input_per_mtok"):
                    for key in ("cache_read_per_mtok", "cache_write_per_mtok"):
                        if key in old:
                            row.setdefault(key, old[key])
    return newest


def load() -> dict:
    return _load_json()


def models() -> list[Model]:
    rows = _load_json()["claude"]
    return sorted(
        (
            Model(
                r["alias"],
                r["id"],
                r["tier"],
                r["input_per_mtok"],
                r["output_per_mtok"],
                r["default_effort"],
                r.get("context_window", 1_000_000),
                r.get("cache_read_per_mtok", round(r["input_per_mtok"] * CACHE_READ_X, 4)),
                r.get("cache_write_per_mtok", round(r["input_per_mtok"] * CACHE_WRITE_X, 4)),
            )
            for r in rows
        ),
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
