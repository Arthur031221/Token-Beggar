"""The footer matrix: one small task per kind, every model and effort, alone against with the skill.

    python3 matrix.py run [--models haiku,sonnet] [--efforts low,high] [--kinds edit,read] [--workers 8] [--limit-seconds 540]
    python3 matrix.py score
    python3 matrix.py fit

Raw claude -p JSON goes to results/matrix/raw/, scores to results/matrix/scores.json, and 'fit' writes data/measured.json.
The runs are resumable: a finished run is skipped. TOKEN_BEGGAR_EXTERNAL=none keeps outside AIs out of this matrix.
"""

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import run
import score
from tasks import TASKS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "benchmark" / "results" / "matrix"
KIND_TASK = {
    "edit": "m1-rename",
    "read": "r2-toprate",
    "bulk-read": "r1-tracking",
    "function": "c2-split",
    "feature": "f3-tier",
    "bugfix": "d1-cents",
    "review": "v2-diff",
    "design": "g2-store",
}
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5", "fable": "claude-fable-5-1"}
EFFORTS = ["low", "medium", "high", "xhigh", "max"]
FABLE_EFFORTS = ["low", "high", "max"]  # the other fable cells are interpolated: a fable run costs about ten opus runs
ARMS = ("alone", "dynamic")
BY_ID = {t["id"]: t for t in TASKS}


def cells(models: list[str], efforts: list[str], kinds: list[str]) -> list[tuple]:
    out = []
    for m in models:
        for e in efforts:
            if m == "fable" and e not in FABLE_EFFORTS:
                continue
            for k in kinds:
                for a in ARMS:
                    out.append((m, e, k, a))
    return out


def do_run(args: argparse.Namespace) -> None:
    run.RAW = OUT / "raw"
    models = args.models.split(",") if args.models else list(MODELS)
    efforts = args.efforts.split(",") if args.efforts else EFFORTS
    kinds = args.kinds.split(",") if args.kinds else list(KIND_TASK)
    jobs = [c for c in cells(models, efforts, kinds) if not (run.RAW / f"{KIND_TASK[c[2]]}.{c[3]}.{c[0]}-{c[1]}.json").exists()]
    random.Random(11).shuffle(jobs)
    print(f"{len(jobs)} runs left", flush=True)
    deadline = time.time() + args.limit_seconds

    def go(job):
        if time.time() > deadline:
            return
        m, e, k, a = job
        rec = run.run_one(BY_ID[KIND_TASK[k]], a, MODELS[m], e, f"{m}-{e}")
        print(f"{m:7} {e:6} {k:10} {a:8} cost={(rec['result'] or {}).get('total_cost_usd')}", flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(go, jobs))


def do_score() -> None:
    score.RAW = OUT / "raw"
    score.OUT = OUT / "scores.json"
    score.main()


def do_fit() -> None:
    from collections import defaultdict

    rows = json.loads((OUT / "scores.json").read_text())
    by_cell: dict = defaultdict(dict)
    for key, r in rows.items():
        raw = json.loads((OUT / "raw" / f"{key}.json").read_text())
        by_cell[(raw["top"], raw["effort"], r["task"])][r["arm"]] = r
    kind_of = {v: k for k, v in KIND_TASK.items()}
    matrix: dict = {}
    for (model, effort, task), arms in by_cell.items():
        if set(arms) != set(ARMS) or any(a.get("error") for a in arms.values()):
            continue
        a, d = arms["alone"], arms["dynamic"]
        cell = {
            "ratio": round(a["cost"] / d["cost"], 2),  # quota and money: the price weighted spend of the run alone over the run with the skill
            "token_ratio": round(a["total_tokens"] / d["total_tokens"], 2),
            "alone_tokens": a["total_tokens"],
            "with_tokens": d["total_tokens"],
            "alone_cost": round(a["cost"], 4),
            "with_cost": round(d["cost"], 4),
            "quality_alone": a["quality"],
            "quality_with": d["quality"],
            "status": "measured",
        }
        matrix.setdefault(MODELS.get(model, model), {}).setdefault(effort, {})[kind_of[task]] = cell
    kinds = sorted({k for efforts in matrix.values() for cells in efforts.values() for k in cells})
    pooled: dict = {}
    for model, efforts in matrix.items():
        for kind in kinds:
            cells = [c[kind] for c in efforts.values() if kind in c]
            if not cells:
                continue
            alone, with_ = sum(c["alone_cost"] for c in cells), sum(c["with_cost"] for c in cells)
            pooled.setdefault(model, {})[kind] = {
                "ratio": round(alone / with_, 2),
                "token_ratio": round(sum(c["alone_tokens"] for c in cells) / sum(c["with_tokens"] for c in cells), 2),
                "runs_per_arm": len(cells),
                "cell_min": min(c["ratio"] for c in cells),
                "cell_max": max(c["ratio"] for c in cells),
                "quality_alone": round(sum(c["quality_alone"] for c in cells) / len(cells), 2),
                "quality_with": round(sum(c["quality_with"] for c in cells) / len(cells), 2),
                "status": "measured",
            }
    for model, by_kind in pooled.items():  # an effort nobody ran takes the model's pooled ratio and says so
        for effort in EFFORTS:
            for kind, cell in by_kind.items():
                if kind not in matrix[model].get(effort, {}):
                    matrix[model].setdefault(effort, {})[kind] = {"ratio": cell["ratio"], "status": "interpolated"}
    base = {}  # spend at each effort relative to medium, from the runs without the skill
    for effort in EFFORTS:
        ratios = []
        for efforts in matrix.values():
            for kind in kinds:
                here, mid = efforts.get(effort, {}).get(kind, {}), efforts.get("medium", {}).get(kind, {})
                if here.get("alone_cost") and mid.get("alone_cost"):
                    ratios.append(here["alone_cost"] / mid["alone_cost"])
        if ratios:
            base[effort] = round(sorted(ratios)[len(ratios) // 2], 2)
    path = ROOT / "data" / "measured.json"
    data = json.loads(path.read_text())
    data["matrix"] = matrix
    data["pooled"] = pooled
    data["effort_cost_x"] = base
    data.pop("effort_tokens_x", None)
    data["matrix_note"] = (
        "ratio is the price weighted spend (list price, cache included) of the run alone over the run with the skill, which is what the quota and the bill follow; "
        "token_ratio is kept for reference only. One run per cell and arm, so a single cell is noisy; the footer uses 'pooled' (spend summed over every measured effort of that model and kind). "
        "Cells marked interpolated were not run and carry the pooled ratio."
    )
    path.write_text(json.dumps(data, indent=1) + "\n")
    print(sum(len(k) for m in matrix.values() for k in m.values()), "cells,", sum(len(k) for k in pooled.values()), "pooled")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score", "fit"])
    ap.add_argument("--models", default="")
    ap.add_argument("--efforts", default="")
    ap.add_argument("--kinds", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-seconds", type=int, default=540)
    a = ap.parse_args()
    os.environ.setdefault("TOKEN_BEGGAR_EXTERNAL", "none")
    {"run": lambda: do_run(a), "score": do_score, "fit": do_fit}[a.cmd]()
