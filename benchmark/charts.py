"""Draws the four README charts from the benchmark summaries: cost and quality, for hard tasks and for small tasks.

    python3 charts.py [--small small] [--small-map alone:alone,v020:previous,sized:this]

Each chart answers one question, prints its values on the bars, and sits on its own paper coloured card so it reads the same in
light and dark mode. The cost charts carry a dashed line at 1.0x, marked "no saving". The setups carry one plain name everywhere
(NAMES). Script arm names stay in benchmark/.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "benchmark" / "results"
ASSETS = ROOT / "assets"
NAMES = {"base": "Without Token Beggar", "previous": "v0.2.0 (previous release)", "this": "v0.3.0 (this release)"}
INK, PAPER, COPPER, SAND, MUTED, SLATE, LINE = "#2b2118", "#fbf3e4", "#c8742b", "#c9b18a", "#6f5f4d", "#6f8574", "#a8553a"
COLORS = {"base": SAND, "previous": SLATE, "this": COPPER}
SMALL_CLASSES = [("mechanical", "Mechanical edits"), ("reading", "Reading"), ("routine_code", "Routine code"), ("multi_file", "Several files"), ("debugging", "Debugging"), ("design", "Design"), ("review", "Review")]


def text(x, y, s, size=12, fill=INK, anchor="start", weight="normal"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'


def bars(path, title, caption, rows, setups, fmt, scale, line=None):
    """rows: [(label, {setup: value})]. line: draw a dashed marker at 1.0x with the words no saving."""
    width, left, top = 860, 220, 92
    bar_h, gap = 15, 3
    row_h = len(setups) * (bar_h + gap) + 14
    height = top + row_h * len(rows) + 62
    inner = width - left - 90
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Georgia, serif" role="img" aria-label="{title}">',
        f'<rect width="{width}" height="{height}" rx="14" fill="{PAPER}"/>',
        text(24, 36, title, 20, INK, weight="bold"),
    ]
    x = 24
    for key in setups:
        out.append(f'<rect x="{x}" y="52" width="12" height="12" rx="2" fill="{COLORS[key]}"/>')
        out.append(text(x + 18, 63, NAMES[key], 12, MUTED))
        x += 48 + 6.4 * len(NAMES[key])
    if line:
        lx = left + inner * line / scale
        out.append(f'<line x1="{lx:.1f}" y1="{top - 8}" x2="{lx:.1f}" y2="{height - 52}" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        out.append(text(lx, top - 14, "1.0x: no saving", 11, LINE, "middle", "bold"))
    for i, (label, values) in enumerate(rows):
        y = top + i * row_h
        out.append(text(left - 12, y + row_h / 2 + 1, label, 13, INK, "end"))
        for k, key in enumerate(setups):
            if key not in values:
                continue
            value = values[key]
            w = max(2.0, inner * value / scale)
            by = y + 4 + k * (bar_h + gap)
            out.append(f'<rect x="{left}" y="{by}" width="{w:.1f}" height="{bar_h}" rx="2" fill="{COLORS[key]}"/>')
            out.append(text(left + w + 6, by + 12, fmt(value), 12, INK))
    out.append(text(24, height - 24, caption, 12, MUTED))
    out.append("</svg>")
    path.write_text("\n".join(out) + "\n")


def percent(v):
    return f"{v * 100:.0f}%"


def times(v):
    return f"{v:.2f}x"


def hard(name_of):
    s = json.loads((RESULTS / "hard" / "summary.json").read_text())
    setups = [k for k in ("base", "previous", "this") if name_of[k] in s["arms"]]
    cost_setups = [k for k in setups if k != "base"]
    rows_cost = [(t, {k: s["per_task"][t][name_of[k]]["multiple"] for k in cost_setups}) for t in s["tasks"]]
    rows_cost.append(("All tasks", {k: s["arms"][name_of[k]]["multiple"] for k in cost_setups}))
    scale = max(1.5, max(v for _, r in rows_cost for v in r.values()) * 1.08)
    runs = min(s["arms"][name_of[k]]["runs"] for k in setups)
    bars(ASSETS / "chart-hard-cost.svg", "Hard tasks: how much less quota and money?",
         f"Cost of working without Token Beggar divided by cost with it, list price, {runs} or more runs per setup. Higher is cheaper.",
         rows_cost, cost_setups, times, scale, line=1.0)
    rows_q = [(t, {k: s["per_task"][t][name_of[k]]["resolved"] for k in setups}) for t in s["tasks"]]
    rows_q.append(("All tasks", {k: s["arms"][name_of[k]]["resolved"] for k in setups}))
    bars(ASSETS / "chart-hard-quality.svg", "Hard tasks: how often was the issue fixed?",
         "Share of runs where the fix's own hidden tests pass and no existing test breaks.", rows_q, setups, percent, 1.0)


def small(out, name_of):
    s = json.loads((RESULTS / out / "summary.json").read_text())
    setups = [k for k in ("base", "previous", "this") if name_of[k] in s["all"]]
    cost_setups = [k for k in setups if k != "base"]
    names = [(c, label) for c, label in SMALL_CLASSES if c in s]
    rows_cost = [(label, {k: s[c][name_of[k]]["multiple"] for k in cost_setups if name_of[k] in s[c]}) for c, label in names]
    rows_cost.append(("All small tasks", {k: s["all"][name_of[k]]["multiple"] for k in cost_setups}))
    scale = max(1.5, max(v for _, r in rows_cost for v in r.values()) * 1.08)
    runs = min(s["all"][name_of[k]]["runs"] for k in setups)
    bars(ASSETS / "chart-small-cost.svg", "Small tasks: how much less quota and money?",
         f"Cost of working without Token Beggar divided by cost with it, list price, {runs} runs per setup. Higher is cheaper.",
         rows_cost, cost_setups, times, scale, line=1.0)
    rows_q = [(label, {k: s[c][name_of[k]]["quality"] for k in setups if name_of[k] in s[c]}) for c, label in names]
    rows_q.append(("All small tasks", {k: s["all"][name_of[k]]["quality"] for k in setups}))
    bars(ASSETS / "chart-small-quality.svg", "Small tasks: how good were the answers?",
         "Score from 0 to 1: hidden checks and tests for code tasks, a blind judge against a checklist for answers.", rows_q, setups, lambda v: f"{v:.2f}", 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard-map", default="base:alone,previous:main,this:sized")
    ap.add_argument("--small", default="")
    ap.add_argument("--small-map", default="base:alone,previous:final,this:sized")
    args = ap.parse_args()
    ASSETS.mkdir(exist_ok=True)
    hard(dict(p.split(":") for p in args.hard_map.split(",")))
    if args.small:
        small(args.small, dict(p.split(":") for p in args.small_map.split(",")))


if __name__ == "__main__":
    main()
