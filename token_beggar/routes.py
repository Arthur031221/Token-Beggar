"""Turn a task class and the session ceiling into a concrete model, effort and mode."""

import json

from . import catalog, paths

SMALLEST = "haiku"
MID = "sonnet"


def classes() -> list[dict]:
    return json.loads(paths.data_file("routes.json").read_text())["classes"]


def _pick(alias_wanted: str, ceiling_tier: int, unavailable: set[str]) -> catalog.Model | None:
    """The wanted model, or the nearest lower one when it is out of quota. Never above the ceiling. None when all are out."""
    by_alias = {m.alias: m for m in catalog.models()}
    wanted = by_alias[alias_wanted]
    tier = min(wanted.tier, ceiling_tier)
    for model in sorted(catalog.models(), key=lambda m: -m.tier):
        if model.tier <= tier and model.alias not in unavailable:
            return model
    return None


def route(task_class: str, ceiling: dict, unavailable: set[str] | None = None) -> dict:
    """Pick model and effort for a class. The ceiling model and effort are never exceeded."""
    unavailable = unavailable or set()
    spec = next(c for c in classes() if c["id"] == task_class)
    top = catalog.find(ceiling.get("model")) or catalog.find("sonnet")
    if spec["tier"] == "ceiling":
        model = top
    else:
        model = _pick(SMALLEST if spec["tier"] == "smallest" else MID, top.tier, unavailable) or top
    wanted = ceiling["effort"] if spec["effort"] == "ceiling" else spec["effort"]
    effort = catalog.cap_effort(wanted, ceiling["effort"])
    same_as_chat = model.id == top.id and effort == ceiling["effort"]
    mode = "inline" if same_as_chat else spec["mode"]
    return {"class": task_class, "model": model.alias, "model_id": model.id, "effort": effort, "mode": mode}


def table(ceiling: dict, unavailable: set[str] | None = None) -> list[dict]:
    return [route(c["id"], ceiling, unavailable) for c in classes()]
