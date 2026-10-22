"""The line at the end of a reply that says what Token Beggar did, in quota and money. It never shows a token count: a Haiku token
spends far less quota than an Opus token, so raw tokens hide the thing the user pays for.

Both numbers come from data, not from the chat model. The multiple is the measured price weighted ratio (cost alone over cost with
the skill) for this model, effort and kind of task (data/measured.json). The dollars are this reply's own list price cost, counted
from the transcript (main chain plus every subagent, each at its model's price), times (ratio - 1)."""

import json
import os
import re
from collections import Counter

from . import catalog, external, paths, usage
from . import ceiling as ceiling_mod

MIN_CLAIM = 1.15  # below this the benchmark cannot tell a saving from run to run spread
MODES = ("off", "sized", "full")
KINDS = {
    "edit": "exact edits",
    "read": "read and answer",
    "bulk-read": "summarise many files",
    "function": "one function with tests",
    "feature": "multi-file feature",
    "bugfix": "bug fix",
    "review": "review",
    "design": "design",
}
BULK = re.compile(r"\b(all|every|each|across|summari[sz]e|inventory|list the)\b", re.IGNORECASE)
EDITING = re.compile(r"\b(rename|replace|delete|remove|bump|reformat|add the line|change every)\b", re.IGNORECASE)
BUILDING = re.compile(r"\b(add|implement|create|write|build|support)\b", re.IGNORECASE)


def kind_of(prompt: str, edited: set[str]) -> str:
    """The kind of task, from the prompt and from what the reply edited. Rules, not a model, so it is the same every time."""
    text = prompt.lower()
    if re.search(r"\b(review|audit)\b", text):
        return "review"
    if re.search(r"\b(design|architecture|trade-?offs?|recommend)\b", text) and not edited:
        return "design"
    if re.search(r"\b(fix|bug|fails?|failing|broken|wrong|root cause|does not work|doesn'?t work)\b", text):
        return "bugfix"
    if not edited:
        return "bulk-read" if BULK.search(text) else "read"
    if EDITING.search(text) and not re.search(r"\b(feature|support)\b", text):
        return "edit"
    if len(edited) >= 3 or re.search(r"\b(feature|shipping|state|tier|support)\b", text):
        return "feature"
    return "function" if BUILDING.search(text) else "edit"


# ---- the measured ratios -----------------------------------------------------------------------------------------------


def _measured(key: str) -> dict:
    try:
        return json.loads(paths.data_file("measured.json").read_text()).get(key) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def matrix() -> dict:
    return _measured("matrix")


def effort_cost() -> dict:
    """What a small task costs at each effort relative to medium, alone, from the matrix (data/measured.json)."""
    return _measured("effort_cost_x")


def pooled() -> dict:
    return _measured("pooled")


def ratio_for(model_id: str, effort: str, kind: str, data: dict | None = None, pool: dict | None = None) -> tuple[float, str] | None:
    """(ratio, 'measured' | 'interpolated'). The ratio is the spend alone divided by the spend with the skill, same model and kind.

    One run per cell is too noisy to quote, so the number comes from 'pool': the spend of every measured effort of that model
    and kind added up. It is 'interpolated' when this effort was not one of the measured ones.
    Without a pool, the cell itself is used; a cell nobody ran is filled from the nearest efforts, then from the same effort
    and kind on the other models. It is marked interpolated, in the data and in the footer."""
    data = matrix() if data is None else data
    cell = ((data.get(model_id) or {}).get(effort) or {}).get(kind)
    pool_cell = ((pool or {}).get(model_id) or {}).get(kind)
    if pool_cell and pool_cell.get("ratio"):
        measured = bool(cell and cell.get("status", "measured") == "measured")
        return pool_cell["ratio"], "measured" if measured else "interpolated"
    if cell and cell.get("ratio"):
        return cell["ratio"], cell.get("status", "measured")
    own = data.get(model_id) or {}
    same_model = [(catalog.effort_rank(e), efforts[kind]["ratio"]) for e, efforts in own.items() if kind in efforts and efforts[kind].get("ratio")]
    if same_model:
        want = catalog.effort_rank(effort)
        nearest = sorted(same_model, key=lambda pair: abs(pair[0] - want))[:2]
        return round(sum(r for _, r in nearest) / len(nearest), 2), "interpolated"
    same_effort = [m.get(effort, {}).get(kind, {}).get("ratio") for m in data.values()]
    same_effort = [r for r in same_effort if r]
    if same_effort:
        return round(sum(same_effort) / len(same_effort), 2), "interpolated"
    return None


def overall(model_id: str, effort: str, data: dict | None = None) -> float | None:
    """The spend alone over the spend with the skill for this model and effort, every kind of task added up. The nearest measured
    effort of the same model stands in when this one was not run."""
    efforts = (_measured("overall") if data is None else data).get(model_id) or {}
    if effort in efforts:
        return efforts[effort]["ratio"]
    if not efforts:
        return None
    want = catalog.effort_rank(effort)
    near = min(efforts, key=lambda e: abs(catalog.effort_rank(e) - want))
    return efforts[near]["ratio"]


def large_ratio(model_id: str, effort: str, data: dict | None = None) -> tuple[float, str] | None:
    """(ratio, 'measured' | 'interpolated') from the hard task benchmark: spend alone over spend with the skill on large tasks."""
    efforts = (_measured("large") if data is None else data).get(model_id) or {}
    if not efforts:
        return None
    if effort in efforts:
        return efforts[effort]["ratio"], "measured"
    want = catalog.effort_rank(effort)
    near = min(efforts, key=lambda e: abs(catalog.effort_rank(e) - want))
    return efforts[near]["ratio"], "interpolated"


def mode(model_id: str | None, effort: str, data: dict | None = None) -> str:
    """How much of the skill acts for this ceiling model and effort. The task decides first, the model second.

    full   the small tasks measured a saving clear of the run to run spread: the whole menu and rules, small tasks included
    sized  everything else: small tasks stay inline with no card output, large tasks (several files, unfamiliar code, a test loop)
           go to workers. A worker's start cost eats the saving on a small task and is noise on a large one
    off    the chat is the cheapest model, so there is nothing cheaper to send work to
    TOKEN_BEGGAR_MODE overrides it, for benchmarks and for anyone who wants the full menu anyway. An unmeasured model gets full."""
    forced = os.environ.get("TOKEN_BEGGAR_MODE")
    if forced in MODES:
        return forced
    model = catalog.find(model_id) if model_id else None
    if model and model.tier == min(m.tier for m in catalog.models()):
        return "off"
    ratio = overall(model_id, effort, data) if model_id else None
    if ratio is None or ratio >= MIN_CLAIM:
        return "full"
    return "sized"


# ---- what was used --------------------------------------------------------------------------------------------------------


def _routed(dispatches: list[dict], ledger: list[dict]) -> list[str]:
    names = Counter()
    for d in dispatches:
        model = catalog.find(d["model"] or (d["input"].get("model") or ""))
        effort = d["input"].get("effort")
        names[f"{model.alias if model else (d['input'].get('model') or 'worker')}{' ' + effort if effort else ''}"] += 1
    for row in ledger:
        if row.get("kind") == "external":
            names[external.short_name(row["tool"], row.get("model"))] += 1
    return [f"{name} x{n}" for name, n in names.items()]


def _money(dollars: float) -> str:
    return f"${dollars:.2f}" if dollars >= 0.01 else "under $0.01"


def build(payload: dict, items: list[dict], complete: bool = True) -> str | None:
    """The footer for the reply that just ended, or None when Token Beggar did nothing in it."""
    window = usage.reply_window(items)
    tally = usage.tally(window, payload.get("transcript_path"))
    started = usage._seconds(window[0]) if window else 0.0
    outside = [row for row in usage.ledger(payload.get("session_id", ""), started) if row.get("kind") == "external"]
    if not tally["dispatches"] and not outside:
        return None
    top = ceiling_mod.resolve(payload.get("transcript_path"), payload.get("cwd"))
    effort = ((payload.get("effort") or {}).get("level")) or top["effort"]
    model = catalog.find(top["model"])
    shown = mode(model.id if model else None, effort)
    if shown == "off":
        return None
    name = usage.display_name(model)
    prompt = usage.prompt_text(window)
    edited = usage.edited_files(window)
    if not edited and tally["dispatches"] and (EDITING.search(prompt) or BUILDING.search(prompt)):
        edited = {"(edited by a worker)"}  # the workers' edits are in their own transcripts, not in the main chain
    kind = kind_of(prompt, edited)
    spent = tally["main_cost"] + tally["agents_cost"]  # outside AIs spend no Claude quota, so they are not in it
    lead = "about" if complete else "at least"  # an unfinished transcript gives a lower bound
    routed = _routed(tally["dispatches"], outside)
    detail = f"{'large task' if shown == 'sized' else KINDS[kind]} | routed {sum(int(r.rsplit('x', 1)[1]) for r in routed)}: {', '.join(routed)}"
    if outside:
        detail += " | outside AI calls cost no Claude quota"
    # a sized reply that routed anything was a large task, which the small task ratios do not describe
    found = None
    if model:
        found = large_ratio(model.id, effort) if shown == "sized" else ratio_for(model.id, effort, kind, pool=pooled())
    if not found:
        unmeasured = f"no measured ratio for {name} {effort} on {'large tasks' if shown == 'sized' else 'this kind'}"
        return f"Token Beggar: this reply cost {lead} {_money(spent)} (est.; {unmeasured}) | {detail}"
    ratio, status = found
    note = ", interpolated" if status == "interpolated" else ""
    if ratio >= MIN_CLAIM:
        saved = spent * (ratio - 1)
        multiple = f"about {ratio:.1f}x less quota than {name} {effort} alone"
        return f"Token Beggar: {multiple}, saved {lead} {_money(saved)} (est.{note}) | {detail}"
    if ratio >= 1 / MIN_CLAIM:
        return f"Token Beggar: no measurable saving over {name} {effort} alone for this kind (est.{note}) | {detail}"
    return f"Token Beggar: for this kind {name} {effort} alone would likely cost less (est.{note}) | {detail}"
