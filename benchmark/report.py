"""Turns results/<out>/scores.json into results/<out>/summary.json and report.md, and optionally the README charts.

    python3 report.py --out final --arms alone,v020,final [--base alone] [--charts]

Money is the list price cost of a run (every model the run used, each at its own price, cache included), so the multiple
`cost of base / cost of arm` is also the multiple of quota spent. Spread comes from a bootstrap over the runs of each task
(2000 resamples, fixed seed). A multiple is claimed only when it is at least 1.15x and the 95 percent interval stays above 1.0x.
data/measured.json is written by matrix.py and agy_bench.py, not here.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "benchmark" / "results"
ASSETS = ROOT / "assets"
ORDER = ["mechanical", "reading", "routine_code", "multi_file", "debugging", "design", "review"]
LABELS = {"alone": "alone", "v020": "v0.2.0", "fullcard": "full card", "final": "this release"}
INK, PAPER, COPPER, SAND, MUTED, SLATE = "#2b2118", "#fbf3e4", "#c8742b", "#d9c3a0", "#7a6a58", "#8a9a8c"
COLORS = {"alone": SAND, "v020": SLATE, "fullcard": MUTED, "final": COPPER}
MIN_CLAIM = 1.15
QUALITY_DROP = 0.10  # a class mean this far below the base arm is called a drop


def load(out: str) -> list[dict]:
    rows = json.loads((RESULTS / out / "scores.json").read_text()).values()
    return [r for r in rows if not r.get("error") and r.get("cost") is not None]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def by_task(rows: list[dict], arm: str) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for r in rows:
        if r["arm"] == arm:
            out[r["task"]].append(r)
    return out


def ratio_ci(rows: list[dict], base: str, arm: str, draws: int = 2000) -> tuple[float, float, float]:
    """(multiple, low, high) of base cost over arm cost for these rows, resampling the runs inside each task."""
    a, b = by_task(rows, base), by_task(rows, arm)
    tasks = sorted(set(a) & set(b))
    if not tasks:
        return 0.0, 0.0, 0.0

    def multiple(pick) -> float:
        top = sum(mean([r["cost"] for r in pick(a[t])]) for t in tasks)
        bottom = sum(mean([r["cost"] for r in pick(b[t])]) for t in tasks)
        return top / bottom if bottom else 0.0

    rng = random.Random(11)
    boots = sorted(multiple(lambda rs: [rng.choice(rs) for _ in rs]) for _ in range(draws))
    return multiple(lambda rs: rs), boots[int(0.025 * draws)], boots[int(0.975 * draws) - 1]


def arm_stats(rows: list[dict], arm: str) -> dict:
    chosen = [r for r in rows if r["arm"] == arm]
    return {
        "runs": len(chosen),
        "tasks": len({r["task"] for r in chosen}),
        "cost": mean([r["cost"] for r in chosen]),
        "quality": mean([r["quality"] for r in chosen]),
        "seconds": mean([r["seconds"] for r in chosen]),
        "turns": mean([r["turns"] or 0 for r in chosen]),
    }


def summarise(rows: list[dict], base: str, arms: list[str]) -> dict:
    groups = {"all": rows}
    for name, flag in (("seen tasks", False), ("held-out tasks", True)):
        picked = [r for r in rows if bool(r.get("held_out")) == flag]
        if picked:
            groups[name] = picked
    for cls in ORDER:
        picked = [r for r in rows if r["class"] == cls]
        if picked:
            groups[cls] = picked
    out = {}
    for name, picked in groups.items():
        entry = {}
        for arm in arms:
            stats = arm_stats(picked, arm)
            if not stats["runs"]:
                continue
            if arm != base:
                multiple, low, high = ratio_ci(picked, base, arm)
                base_stats = arm_stats(picked, base)
                stats.update(
                    multiple=round(multiple, 2),
                    low=round(low, 2),
                    high=round(high, 2),
                    claim=multiple >= MIN_CLAIM and low > 1.0,
                    saved_per_task=round(base_stats["cost"] - stats["cost"], 4),
                    quality_delta=round(stats["quality"] - base_stats["quality"], 3),
                )
                stats["quality_drop"] = stats["quality_delta"] < -QUALITY_DROP
            entry[arm] = stats
        out[name] = entry
    return out


def multiple_text(s: dict) -> str:
    if s["claim"]:
        return f"{s['multiple']:.2f}x ({s['low']:.2f} to {s['high']:.2f})"
    return f"no claim ({s['multiple']:.2f}x, {s['low']:.2f} to {s['high']:.2f})"


def render(summary: dict, base: str, arms: list[str]) -> str:
    lines = []
    others = [a for a in arms if a != base]
    head = ["group", f"cost per task {LABELS.get(base, base)}"]
    for a in others:
        head += [
            f"{LABELS.get(a, a)} cost",
            f"{LABELS.get(a, a)} multiple (95% interval)",
            "saved per task",
            "quality (base / arm)",
            "seconds (base / arm)",
        ]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for name, entry in summary.items():
        if base not in entry:
            continue
        b = entry[base]
        row = [name, f"${b['cost']:.3f}"]
        for a in others:
            s = entry.get(a)
            if not s:
                row += ["-"] * 5
                continue
            flag = " DROP" if s["quality_drop"] else ""
            row += [
                f"${s['cost']:.3f}",
                multiple_text(s),
                f"${s['saved_per_task']:.3f}",
                f"{b['quality']:.2f} / {s['quality']:.2f}{flag}",
                f"{b['seconds']:.0f} / {s['seconds']:.0f}",
            ]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def bars(path: Path, title: str, rows: list[tuple[str, dict]], arms: list[str], fmt: str, scale_max: float, note: str, mark=None) -> None:
    width, left, top, row_h = 800, 170, 70, 18 * len(arms) + 18
    height = top + row_h * len(rows) + 54
    inner = width - left - 120
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Georgia, serif">',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        f'<text x="24" y="34" font-size="20" fill="{INK}" font-weight="bold">{title}</text>',
    ]
    x = left
    for arm in arms:
        label = LABELS.get(arm, arm)
        parts.append(
            f'<rect x="{x}" y="46" width="12" height="12" fill="{COLORS.get(arm, MUTED)}"/><text x="{x + 18}" y="57" font-size="12" fill="{MUTED}">{label}</text>'
        )
        x += 40 + 7 * len(label)
    for i, (label, values) in enumerate(rows):
        y = top + i * row_h
        parts.append(f'<text x="{left - 10}" y="{y + row_h / 2 - 2}" font-size="13" fill="{INK}" text-anchor="end">{label}</text>')
        for k, arm in enumerate(arms):
            if arm not in values:
                continue
            value = values[arm]
            w = max(2, inner * value / scale_max)
            parts.append(f'<rect x="{left}" y="{y + 6 + k * 16}" width="{w:.1f}" height="13" rx="2" fill="{COLORS.get(arm, MUTED)}"/>')
            tag = fmt.format(value) + (mark(label, arm) if mark else "")
            parts.append(f'<text x="{left + w + 6:.1f}" y="{y + 17 + k * 16}" font-size="11" fill="{MUTED}">{tag}</text>')
    parts.append(f'<text x="24" y="{height - 16}" font-size="11" fill="{MUTED}">{note}</text></svg>')
    path.write_text("\n".join(parts) + "\n")


def charts(summary: dict, base: str, arms: list[str], note: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "chart-tokens.svg").unlink(missing_ok=True)
    others = [a for a in arms if a != base]
    names = [c for c in ORDER if c in summary] + ["all"]
    multiples = [(c, {a: summary[c][a]["multiple"] for a in others if a in summary[c]}) for c in names]
    bars(
        ASSETS / "chart-cost.svg",
        "Times less quota and money than the model alone",
        multiples,
        others,
        "{:.2f}x",
        max(1.5, max(max(v.values()) for _, v in multiples)),
        note,
        mark=lambda c, a: "" if summary[c][a]["claim"] else " (within noise)",
    )
    quality = [(c, {a: summary[c][a]["quality"] for a in arms if a in summary[c]}) for c in names]
    bars(
        ASSETS / "chart-quality.svg",
        "Mean quality score (1.0 is perfect)",
        quality,
        arms,
        "{:.2f}",
        1.0,
        "Code tasks: hidden check plus tests. Answer tasks: blind judge against a checklist.",
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="final")
    ap.add_argument("--base", default="alone")
    ap.add_argument("--arms", default="alone,v020,final")
    ap.add_argument("--charts", action="store_true")
    args = ap.parse_args()
    arms = args.arms.split(",")
    rows = load(args.out)
    summary = summarise(rows, args.base, arms)
    runs = {a: arm_stats(rows, a)["runs"] for a in arms}
    note = f"{min(runs.values())} to {max(runs.values())} runs per arm, Opus 5.5 at high effort as the chat model."
    (RESULTS / args.out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    table = render(summary, args.base, arms)
    per_task = ["", "## Per task", "", "| task | arm | cost | quality | turns | seconds |", "|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (ORDER.index(r["class"]) if r["class"] in ORDER else 9, r["task"], r["arm"], r["rep"])):
        per_task.append(f"| {r['task']} | {r['arm']} | ${r['cost']:.3f} | {r['quality']:.2f} | {r['turns']} | {r['seconds']} |")
    (RESULTS / args.out / "report.md").write_text(f"# Benchmark results: {args.out}\n\n{note}\n\n{table}\n" + "\n".join(per_task) + "\n")
    if args.charts:
        charts(summary, args.base, arms, note)
    print(table)


if __name__ == "__main__":
    main()
