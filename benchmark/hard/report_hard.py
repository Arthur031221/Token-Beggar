"""Turns benchmark/results/hard/raw/*.json into summary.json and report.md for the hard task benchmark.

    python3 report_hard.py [--out hard] [--base alone] [--arms alone,main,sized] [--blind blind.json]

Cost is the list price of a run (every model used, each at its own price, cache included), so the multiple
`cost of base / cost of arm` is also the multiple of quota spent. The spread is a bootstrap over the runs of each task
(2000 resamples, fixed seed). Quality is the share of runs that resolved the task: every test the fix added passes and
no test that passed before fails. `--blind` is an optional json {"task.arm.rep": score 0 to 2} from the diff review.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
MIN_CLAIM = 1.15


def load(out: str) -> list[dict]:
    rows = []
    for path in sorted((RESULTS / out / "raw").glob("*.json")):
        d = json.loads(path.read_text())
        r, s = d["result"], d["score"]
        if not isinstance(r, dict) or r.get("total_cost_usd") is None:
            continue
        rows.append({
            "task": d["task"], "arm": d["arm"], "rep": d["rep"], "cost": r["total_cost_usd"], "turns": r.get("num_turns") or 0,
            "seconds": (r.get("duration_ms") or 0) / 1000, "resolved": bool(s["resolved"]), "f2p": s["f2p_passed"] / max(1, s["f2p_total"]),
            "regressions": s["regressions"], "ran": s.get("suite_ran", True),
        })
    return rows


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def group(rows, arm):
    out = defaultdict(list)
    for r in rows:
        if r["arm"] == arm:
            out[r["task"]].append(r)
    return out


def ratio(rows, base, arm, draws=2000, tasks=None):
    """(multiple, low, high): cost of base over cost of arm, summed over tasks, resampling the runs inside each task."""
    a, b = group(rows, base), group(rows, arm)
    names = sorted(set(a) & set(b)) if tasks is None else [t for t in tasks if t in a and t in b]
    if not names:
        return 0.0, 0.0, 0.0

    def multiple(pick):
        top = sum(mean(r["cost"] for r in pick(a[t])) for t in names)
        bottom = sum(mean(r["cost"] for r in pick(b[t])) for t in names)
        return top / bottom if bottom else 0.0

    rng = random.Random(11)
    boots = sorted(multiple(lambda rs: [rng.choice(rs) for _ in rs]) for _ in range(draws))
    return multiple(lambda rs: rs), boots[int(0.025 * draws)], boots[int(0.975 * draws) - 1]


def claim(m, lo) -> bool:
    return m >= MIN_CLAIM and lo > 1.0


def stats(rows, arm, tasks=None):
    chosen = [r for r in rows if r["arm"] == arm and (tasks is None or r["task"] in tasks)]
    return {
        "runs": len(chosen), "cost": mean(r["cost"] for r in chosen), "resolved": mean(r["resolved"] for r in chosen),
        "f2p": mean(r["f2p"] for r in chosen), "regressions": sum(1 for r in chosen if r["regressions"]),
        "seconds": mean(r["seconds"] for r in chosen), "turns": mean(r["turns"] for r in chosen),
    }


def rep_spread(rows, arm):
    """Share of tasks resolved in each rep of one arm: the run-to-run spread of a single arm."""
    by_rep = defaultdict(list)
    for r in rows:
        if r["arm"] == arm:
            by_rep[r["rep"]].append(r["resolved"])
    return {rep: mean(v) for rep, v in sorted(by_rep.items())}


def summarise(rows, base, arms, blind):
    tasks = sorted({r["task"] for r in rows})
    out = {"tasks": tasks, "arms": {}, "per_task": {}, "rep_spread": {a: rep_spread(rows, a) for a in arms}}
    for arm in arms:
        s = stats(rows, arm)
        if arm != base:
            m, lo, hi = ratio(rows, base, arm)
            s |= {"multiple": m, "low": lo, "high": hi, "claim": claim(m, lo)}
        s["blind"] = mean(blind[k] for k in blind if k.split(".")[1] == arm) if blind else None
        out["arms"][arm] = s
    for t in tasks:
        row = {}
        for arm in arms:
            s = stats(rows, arm, {t})
            if arm != base:
                m, lo, hi = ratio(rows, base, arm, tasks=[t])
                s |= {"multiple": m, "low": lo, "high": hi}
            row[arm] = s
        out["per_task"][t] = row
    return out


def render(summary, base, arms, label):
    lines = ["| setup | runs | cost per run | multiple vs " + label[base] + " (95% interval) | resolved | regressions | turns | seconds |", "|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        s = summary["arms"][arm]
        mult = "1.00x" if arm == base else f"{s['multiple']:.2f}x ({s['low']:.2f} to {s['high']:.2f})" + ("" if s["claim"] else " within noise")
        lines.append(f"| {label[arm]} | {s['runs']} | ${s['cost']:.2f} | {mult} | {s['resolved'] * 100:.0f}% | {s['regressions']} | {s['turns']:.0f} | {s['seconds']:.0f} |")
    lines += ["", "## Per task", "", "| task | setup | runs | cost per run | multiple | resolved | tests fixed | turns | seconds |", "|---|---|---|---|---|---|---|---|---|"]
    for t, row in summary["per_task"].items():
        for arm in arms:
            s = row[arm]
            if not s["runs"]:
                continue
            mult = "1.00x" if arm == base else f"{s['multiple']:.2f}x"
            lines.append(f"| {t} | {label[arm]} | {s['runs']} | ${s['cost']:.2f} | {mult} | {s['resolved'] * 100:.0f}% | {s['f2p'] * 100:.0f}% | {s['turns']:.0f} | {s['seconds']:.0f} |")
    lines += ["", "## Run to run spread of the resolved share (one value per rep)", ""]
    for arm in arms:
        lines.append(f"- {label[arm]}: " + ", ".join(f"rep {k} {v * 100:.0f}%" for k, v in summary["rep_spread"][arm].items()))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="hard")
    ap.add_argument("--base", default="alone")
    ap.add_argument("--arms", default="alone,main,verify")
    ap.add_argument("--blind", default="")
    args = ap.parse_args()
    arms = args.arms.split(",")
    label = {"alone": "Without Token Beggar", "main": "v0.2.0 (previous release)", "sized": "Size-aware draft (first wording, not shipped)", "verify": "v0.3.0 (this release)"}
    rows = [r for r in load(args.out) if r["arm"] in arms]
    blind = json.loads(Path(args.blind).read_text()) if args.blind else {}
    summary = summarise(rows, args.base, arms, blind)
    (RESULTS / args.out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    text = f"# Hard task benchmark results\n\n{len(rows)} runs, {len(summary['tasks'])} tasks, Opus 5.5 at high effort as the chat model.\n\n" + render(summary, args.base, arms, label)
    (RESULTS / args.out / "report.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
