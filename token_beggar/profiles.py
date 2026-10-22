"""The capability and cost profile of every combination of provider, model and effort the chat model can route to."""

import json
import time

from . import catalog, paths

EFFORT_TOKENS_X = {"low": 0.6, "medium": 1.0, "high": 1.5, "xhigh": 2.0, "max": 2.5}  # replaced by measured.json when present
LISTED_EFFORTS = ("low", "medium", "high")


def load() -> dict:
    return json.loads(paths.data_file("profiles.json").read_text())


def rules() -> list[str]:
    return load()["rules"]


def external_rules() -> list[str]:
    return load().get("external_rules", [])


def effort_x() -> dict:
    try:
        measured = json.loads(paths.data_file("measured.json").read_text())
        return {**EFFORT_TOKENS_X, **(measured.get("effort_tokens_x") or {})}
    except (OSError, json.JSONDecodeError):
        return dict(EFFORT_TOKENS_X)


def external_model(tool: str, model_id: str) -> dict:
    """capability, label and vendor of an external model, matched by substring against the profile."""
    spec = load()["external"].get(tool, {})
    for row in spec.get("models", []):
        if row["match"] in model_id:
            return {"capability": row["capability"], "label": row["label"], "vendor": row.get("vendor")}
    return {"capability": spec.get("default_capability", 2), "label": model_id, "vendor": None}


def claude_combos(ceiling: dict, unavailable: set[str] | None = None) -> list[dict]:
    """Every Claude model and effort at or under the ceiling, cheapest first. `unavailable` holds aliases that are out of quota."""
    unavailable = unavailable or set()
    top = catalog.find(ceiling.get("model"))
    profiles = load()["claude"]
    rows = []
    for model in catalog.models():
        if top and model.tier > top.tier or model.alias in unavailable:
            continue
        for effort in catalog.EFFORTS:
            if effort not in LISTED_EFFORTS and effort != ceiling.get("effort"):
                continue
            if catalog.effort_rank(effort) > catalog.effort_rank(ceiling.get("effort", "high")):
                continue
            weight = effort_x().get(effort, 1.0)
            rows.append(
                {
                    "provider": "claude",
                    "model": model.alias,
                    "effort": effort,
                    "capability": profiles.get(model.alias, {}).get("capability", model.tier + 1),
                    "price_out": model.output_per_mtok,
                    "cost_index": round(model.output_per_mtok * weight, 2),
                }
            )
    return sorted(rows, key=lambda r: r["cost_index"])


def external_combos(inventory: dict, caps: dict | None = None, unavailable: set[str] | None = None, ceiling_tier: int | None = None) -> list[dict]:
    """Every external tool and model that is installed, under the user's cap and not out of quota.
    A Claude model reached through another tool is still a Claude model: the ceiling applies to it."""
    from . import external  # late import: external uses this module

    unavailable = unavailable or set()
    rows = []
    for tool in inventory.get("external", []):
        name = tool["name"]
        if name in unavailable or tool.get("usable") is False:
            continue
        for model_id in tool.get("models") or ["default"]:
            if f"{name}:{model_id}" in unavailable or not external.allowed(name, model_id, caps or {}):
                continue
            info = external_model(name, model_id)
            if info["vendor"] == "anthropic" and ceiling_tier is not None:
                family = catalog.find(model_id)
                if family and family.tier > ceiling_tier:
                    continue
            rows.append(
                {
                    "provider": name,
                    "model": model_id,
                    "label": info["label"],
                    "capability": info["capability"],
                    "prior": load()["external"].get(name, {}).get("prior", 1),
                }
            )
    return sorted(rows, key=lambda r: (r["capability"], r["model"]))


def exhausted(inventory: dict) -> set[str]:
    now = time.time()
    return {key for key, until in (inventory.get("exhausted") or {}).items() if until > now}
