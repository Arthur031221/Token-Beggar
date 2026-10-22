"""Measures the hand off to agy: Claude Opus alone against Claude with Token Beggar allowed to call agy.

    python3 agy_bench.py run [--reps 3] [--workers 3]
    python3 agy_bench.py score
    python3 agy_bench.py fit

Claude cost comes from the claude -p JSON. What agy used is on its own quota and is reported apart, never added in.
The Gemini CLI is not logged in on the machine that ran this, so it is not measured. Codex is not called.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fixture
import run
import score
import tasks as base
from tasks import task

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "benchmark" / "results" / "agy"
T = fixture.truth()
RATES = sorted(T["rates"].items(), key=lambda kv: -kv[1])

TASKS = [
    task(
        "a1-rates",
        "bulk-read",
        "For every module in shop/carriers/ (not __init__.py) write one line: carrier name, BASE_RATE and whether it quotes by grams or kg. Sort the lines by BASE_RATE, highest first.",
        facts=[
            f"The first line is {RATES[0][0]} with BASE_RATE {RATES[0][1]}",
            f"The second line is {RATES[1][0]} with BASE_RATE {RATES[1][1]}",
            f"The last line is {RATES[-1][0]} with BASE_RATE {RATES[-1][1]}",
            f"{T['grams']} is the only carrier marked as grams",
            "There are 20 lines, one per carrier",
        ],
        needs_tests=False,
    ),
    task(
        "a2-draft",
        "draft",
        "Write a first draft of a short Carriers section for the README of this repo, under 120 words. Say where carriers live, that each defines BASE_RATE, and which carrier quotes by grams.",
        facts=[
            "Says carriers live in shop/carriers/",
            "Says each carrier defines BASE_RATE",
            f"Names {T['grams']} as the carrier that quotes by grams",
            "Is under about 140 words",
        ],
        needs_tests=False,
    ),
    task(
        "a3-second",
        "second-opinion",
        "Give me a second opinion on shop/cache.py for use from many threads in a long running service. Do not write code. List the problems and the fix you would choose. Under 250 words.",
        facts=base.DESIGN_CACHE,
        needs_tests=False,
    ),
]
KIND = {"a1-rates": "bulk-read", "a2-draft": "draft", "a3-second": "second-opinion"}
BY_ID = {t["id"]: t for t in TASKS}


def prepare_home(name: str) -> dict:
    home = run.SCRATCH / "home" / name
    shutil.rmtree(home, ignore_errors=True)
    env = dict(os.environ, TOKEN_BEGGAR_HOME=str(home), TOKEN_BEGGAR_EXTERNAL="agy")
    env.pop("TOKEN_BEGGAR_OFFLINE", None)
    subprocess.run(
        [sys.executable, "-m", "token_beggar", "inventory", "--refresh"],
        cwd=ROOT,
        env=dict(env, PYTHONPATH=str(ROOT)),
        capture_output=True,
        timeout=120,
    )
    return {"TOKEN_BEGGAR_EXTERNAL": "agy"}


def do_run(args) -> None:
    run.RAW = OUT / "raw"
    jobs = [(t, a, r) for t in TASKS for a in ("alone", "final") for r in range(1, args.reps + 1)]
    jobs = [j for j in jobs if not (run.RAW / f"{j[0]['id']}.{j[1]}.{j[2]}.json").exists()]
    random.Random(5).shuffle(jobs)

    def go(job):
        t, a, r = job
        extra = prepare_home(f"{t['id']}.{a}.{r}") if a == "final" else {}
        rec = run.run_one(t, a, "opus", "high", r, extra)
        used = sum(row.get("tokens", 0) for row in rec["ledger"] if row.get("kind") == "external")
        print(t["id"], a, r, "cost", (rec["result"] or {}).get("total_cost_usd"), "agy tokens", used, flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(go, jobs))


def do_score() -> None:
    score.BY_ID = BY_ID
    score.RAW = OUT / "raw"
    score.OUT = OUT / "scores.json"
    score.main()


def do_fit() -> None:
    scores = json.loads((OUT / "scores.json").read_text())
    out = {}
    for tid in BY_ID:
        arms = {"alone": [], "final": []}
        for key, row in scores.items():
            if row["task"] == tid and not row.get("error"):
                raw = json.loads((OUT / "raw" / f"{key}.json").read_text())
                row["agy_tokens"] = sum(r.get("tokens", 0) for r in raw["ledger"] if r.get("kind") == "external")
                row["used_agy"] = row["agy_tokens"] > 0
                arms[row["arm"]].append(row)
        if not all(arms.values()):
            continue
        mean = lambda rows, k: sum(r[k] or 0 for r in rows) / len(rows)  # noqa: E731
        out[KIND[tid]] = {
            "task": tid,
            "runs": {a: len(r) for a, r in arms.items()},
            "cost_alone": round(mean(arms["alone"], "cost"), 4),
            "cost_with": round(mean(arms["final"], "cost"), 4),
            "ratio": round(mean(arms["alone"], "cost") / mean(arms["final"], "cost"), 2),
            "handed_to_agy": sum(r["used_agy"] for r in arms["final"]),
            "quality_alone": round(mean(arms["alone"], "quality"), 2),
            "quality_with": round(mean(arms["final"], "quality"), 2),
            "status": "measured",
        }
    path = ROOT / "data" / "measured.json"
    data = json.loads(path.read_text())
    data["agy"] = out
    data["agy_note"] = (
        "Claude Opus 5.5 high, 3 runs per arm; ratios are Claude list-price cost, agy runs on its own quota and is not added in. The Gemini CLI was not logged in, so it was not measured."
    )
    path.write_text(json.dumps(data, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score", "fit"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    {"run": lambda: do_run(a), "score": do_score, "fit": do_fit}[a.cmd]()
