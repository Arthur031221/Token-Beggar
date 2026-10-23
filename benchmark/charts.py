"""Draws the one README chart from the hard benchmark summary: cost on real bug fixes, Without against With Token Beggar.

    python3 charts.py

Each chart answers one question, prints its values on the bars, and sits on its own paper coloured card so it reads the same in
light and dark mode. The cost charts carry a dashed line at 1.0x, marked "no saving". The setups carry one plain name everywhere
(WITHOUT, V020, MAIN, V030). Script arm names stay in benchmark/.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "benchmark" / "results"
ASSETS = ROOT / "assets"
WITHOUT, V020, MAIN, V030 = "Without Token Beggar", "v0.2.0 (previous release)", "Main before v0.3.0", "With Token Beggar (v0.3.0)"
INK, PAPER, COPPER, SAND, MUTED, SLATE, LINE, MOSS = "#2b2118", "#fbf3e4", "#c8742b", "#c9b18a", "#6f5f4d", "#6f8574", "#a8553a", "#8b8aa6"
COLORS = {WITHOUT: SAND, V020: MOSS, MAIN: SLATE, V030: COPPER}
HARD_NAMES = {"base": WITHOUT, "previous": MAIN, "this": V030}


def text(x, y, s, size=12, fill=INK, anchor="start", weight="normal", halo=False):
    ring = f' stroke="{PAPER}" stroke-width="4" paint-order="stroke"' if halo else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{ring}>{s}</text>'


def bars(path, title, caption, rows, setups, fmt, scale, names, line=None):
    """rows: [(label, {setup: value})]. line: draw a dashed marker at 1.0x with the words no saving."""
    width, left, top = 860, 220, 92
    bar_h, gap = 15, 3
    row_h = len(setups) * (bar_h + gap) + 14
    lines = caption if isinstance(caption, list) else [caption]
    height = top + row_h * len(rows) + 38 + 20 * len(lines)
    inner = width - left - 90
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Georgia, serif" role="img" aria-label="{title}">',
        f'<rect width="{width}" height="{height}" rx="14" fill="{PAPER}"/>',
        text(24, 36, title, 20, INK, weight="bold"),
    ]
    x = 24
    for key in setups:
        out.append(f'<rect x="{x}" y="52" width="12" height="12" rx="2" fill="{COLORS[names[key]]}"/>')
        out.append(text(x + 18, 63, names[key], 12, MUTED))
        x += 48 + 6.4 * len(names[key])
    if line:
        lx = left + inner * line / scale
        out.append(
            f'<line x1="{lx:.1f}" y1="{top - 8}" x2="{lx:.1f}" y2="{top + row_h * len(rows)}" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="5 4"/>'
        )
        out.append(text(lx, top - 14, "1.0x = Without Token Beggar, no saving", 11, LINE, "middle", "bold"))
    for i, (label, values) in enumerate(rows):
        y = top + i * row_h
        out.append(text(left - 12, y + row_h / 2 + 1, label, 13, INK, "end", "bold" if label.startswith("All ") else "normal"))
        for k, key in enumerate(setups):
            if key not in values:
                continue
            value = values[key]
            w = max(2.0, inner * value / scale)
            by = y + 4 + k * (bar_h + gap)
            out.append(f'<rect x="{left}" y="{by}" width="{w:.1f}" height="{bar_h}" rx="2" fill="{COLORS[names[key]]}"/>')
            out.append(text(left + w + 6, by + 12, fmt(value), 12, INK, halo=True))
    for n, line_text in enumerate(lines):
        out.append(text(24, height - 14 - 20 * (len(lines) - 1 - n), line_text, 12, MUTED if n else INK))
    out.append("</svg>")
    path.write_text("\n".join(out) + "\n")


def percent(v):
    return f"{v * 100:.0f}%"


def times(v):
    return f"{v:.2f}x"


def hard(name_of):
    """The one README chart: cost on the hard bug fixes, with Token Beggar against working without it (the 1.0x line)."""
    s = json.loads((RESULTS / "hard" / "summary.json").read_text())
    key = "this"
    rows = [(t, {key: s["per_task"][t][name_of[key]]["multiple"]}) for t in s["tasks"]]
    rows.insert(0, ("All tasks", {key: s["arms"][name_of[key]]["multiple"]}))
    scale = max(1.5, max(r[key] for _, r in rows) * 1.08)
    runs = s["arms"][name_of[key]]["runs"]
    bars(
        ASSETS / "chart-hard-cost.svg",
        "Real bug fixes: how much less does it cost?",
        [
            f"Cost without Token Beggar divided by cost with it, list price, 3 runs per task ({runs} per setup). Higher is cheaper.",
        ],
        rows,
        [key],
        times,
        scale,
        HARD_NAMES,
        line=1.0,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard-map", default="base:alone,previous:main,this:scoped")
    args = ap.parse_args()
    ASSETS.mkdir(exist_ok=True)
    hard(dict(p.split(":") for p in args.hard_map.split(",")))


if __name__ == "__main__":
    main()
