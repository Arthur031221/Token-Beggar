"""Turns results/scores.json into results/summary.json, results/report.md, two SVG charts and data/measured.json."""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORES = ROOT / "benchmark" / "results" / "scores.json"
SUMMARY = ROOT / "benchmark" / "results" / "summary.json"
REPORT = ROOT / "benchmark" / "results" / "report.md"
MEASURED = ROOT / "data" / "measured.json"
ASSETS = ROOT / "assets"
ORDER = ["mechanical", "reading", "routine_code", "multi_file", "debugging", "design", "review"]
QUALITY_SLACK = 0.05  # a class only earns a multiplier when quality held
INK, PAPER, COPPER, SAND, MUTED = "#2b2118", "#fbf3e4", "#c8742b", "#d9c3a0", "#7a6a58"


def load() -> list[dict]:
    return list(json.loads(SCORES.read_text()).values())


def stats(rows: list[dict]) -> dict:
    out = {}
    for arm in ("alone", "beggar"):
        chosen = [r for r in rows if r["arm"] == arm]
        n = len(chosen) or 1
        out[arm] = {
            "runs": len(chosen),
            "cost": sum(r["cost"] or 0 for r in chosen),
            "top_tokens": sum(r["top_tokens"] for r in chosen),
            "total_tokens": sum(r["total_tokens"] for r in chosen),
            "quality": sum(r["quality"] for r in chosen) / n,
            "seconds": sum(r["seconds"] for r in chosen),
        }
    a, b = out["alone"], out["beggar"]
    out["cost_x"] = round(a["cost"] / b["cost"], 2) if b["cost"] else None
    out["top_token_x"] = round(a["top_tokens"] / b["top_tokens"], 2) if b["top_tokens"] else None
    out["quality_delta"] = round(b["quality"] - a["quality"], 3)
    return out


def summarise(rows: list[dict]) -> dict:
    by_class = defaultdict(list)
    for row in rows:
        by_class[row["class"]].append(row)
    classes = {c: stats(by_class[c]) for c in ORDER if c in by_class}
    return {"overall": stats(rows), "classes": classes}


def bars(path: Path, title: str, rows: list[tuple[str, float, float]], unit: str, scale_max: float, note: str) -> None:
    width, left, top, row_h = 760, 170, 70, 46
    height = top + row_h * len(rows) + 54
    inner = width - left - 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Georgia, serif">',
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        f'<text x="24" y="34" font-size="20" fill="{INK}" font-weight="bold">{title}</text>',
        f'<rect x="{left}" y="46" width="12" height="12" fill="{SAND}"/><text x="{left + 18}" y="57" font-size="12" fill="{MUTED}">alone</text>',
        f'<rect x="{left + 70}" y="46" width="12" height="12" fill="{COPPER}"/><text x="{left + 88}" y="57" font-size="12" fill="{MUTED}">with Token Beggar</text>',
    ]
    for i, (label, a, b) in enumerate(rows):
        y = top + i * row_h
        parts.append(f'<text x="{left - 10}" y="{y + 25}" font-size="13" fill="{INK}" text-anchor="end">{label}</text>')
        for k, (value, color) in enumerate(((a, SAND), (b, COPPER))):
            w = max(2, inner * value / scale_max)
            parts.append(f'<rect x="{left}" y="{y + 6 + k * 15}" width="{w:.1f}" height="13" rx="2" fill="{color}"/>')
            parts.append(f'<text x="{left + w + 6:.1f}" y="{y + 17 + k * 15}" font-size="11" fill="{MUTED}">{value:.2f}{unit}</text>')
    parts.append(f'<text x="24" y="{height - 16}" font-size="11" fill="{MUTED}">{note}</text></svg>')
    path.write_text("\n".join(parts) + "\n")


def main() -> None:
    rows = load()
    summary = summarise(rows)
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n")
    classes = summary["classes"]
    runs = summary["overall"]["alone"]["runs"]
    note = f"{runs} runs per arm ({len({r['task'] for r in rows})} tasks), Opus 5.5 at high effort as the chat model. Cost at list price."
    ASSETS.mkdir(exist_ok=True)
    cost_rows = [(c, v["alone"]["cost"] / max(v["alone"]["runs"], 1), v["beggar"]["cost"] / max(v["beggar"]["runs"], 1)) for c, v in classes.items()]
    bars(ASSETS / "chart-cost.svg", "Mean cost per task (USD)", cost_rows, "", max(max(a, b) for _, a, b in cost_rows) * 1.0, note)
    quality_rows = [(c, v["alone"]["quality"], v["beggar"]["quality"]) for c, v in classes.items()]
    bars(
        ASSETS / "chart-quality.svg",
        "Mean quality score (1.0 is perfect)",
        quality_rows,
        "",
        1.0,
        "Code tasks: hidden check plus tests. Answer tasks: blind judge against a checklist.",
    )

    bench = {
        "top_model": "claude-opus-5-5",
        "top_effort": "high",
        "runs_per_arm": runs,
        "overall": {"cost_x": summary["overall"]["cost_x"], "quality_delta": summary["overall"]["quality_delta"]},
        "classes": {
            c: {"cost_x": v["cost_x"], "quality_delta": v["quality_delta"]}
            for c, v in classes.items()
            if v["cost_x"] and v["cost_x"] >= 1.1 and v["quality_delta"] >= -QUALITY_SLACK
        },
    }
    MEASURED.write_text(json.dumps({"benchmark": bench}, indent=1) + "\n")

    lines = [
        "# Benchmark results",
        "",
        note,
        "",
        "| class | cost alone | cost with | x cheaper | top-model tokens x | quality alone | quality with |",
        "|---|---|---|---|---|---|---|",
    ]
    for c, v in classes.items():
        lines.append(
            f"| {c} | ${v['alone']['cost']:.2f} | ${v['beggar']['cost']:.2f} | {v['cost_x']}x | {v['top_token_x']}x | "
            f"{v['alone']['quality']:.2f} | {v['beggar']['quality']:.2f} |"
        )
    o = summary["overall"]
    lines.append(
        f"| **all** | ${o['alone']['cost']:.2f} | ${o['beggar']['cost']:.2f} | {o['cost_x']}x | {o['top_token_x']}x | {o['alone']['quality']:.2f} | {o['beggar']['quality']:.2f} |"
    )
    lines += ["", "## Per task", "", "| task | arm | cost | quality | turns | seconds |", "|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (ORDER.index(r["class"]), r["task"], r["arm"], r["rep"])):
        lines.append(f"| {r['task']} | {r['arm']} | ${r['cost']:.3f} | {r['quality']:.2f} | {r['turns']} | {r['seconds']} |")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:14]))


if __name__ == "__main__":
    main()
