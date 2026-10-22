"""Scores raw runs. Code tasks: hidden check plus the repo's own tests. Answer tasks: a blind judge.

The judge sees the task, the list of required facts and the answer text. It is never told which arm
produced the answer. Output: results/scores.json
"""

import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

from tasks import ALL

BY_ID = {t["id"]: t for t in ALL}
ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "benchmark" / "results"
RAW = RESULTS / "raw"  # main() points RAW and OUT at results/<out>/
OUT = RESULTS / "scores.json"
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
SCRATCH = Path(os.environ.get("TB_SCRATCH", "/tmp/tb-bench"))
JUDGE_MODEL = "sonnet"

JUDGE = """You grade an answer against a checklist. Be strict and literal.

Task given to the assistant:
{task}

Checklist. For each item say whether the answer clearly satisfies it:
{facts}

Answer to grade:
<answer>
{answer}
</answer>

Reply with JSON only: {{"items": [true or false for each checklist item, in order]}}"""


def code_ok(record: dict, task: dict) -> dict:
    work = SCRATCH / record["workdir"]
    # An edit that keeps the file size, such as == to !=, can leave a stale .pyc that still passes the mtime test.
    for cache in work.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    env = {"PYTHONPATH": str(work), "PATH": "/usr/bin:/bin"}
    check = subprocess.run([sys.executable, "-B", "-c", task["check"]], cwd=work, capture_output=True, text=True, env=env)
    tests = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=work, capture_output=True, text=True, env=env
    )
    return {"check": check.returncode == 0, "tests": tests.returncode == 0, "detail": (check.stderr or "")[-200:]}


def strip_footer(answer: str) -> str:
    """The plugin's savings footer names the arm, so the judge never sees it."""
    return "\n".join(line for line in answer.splitlines() if not line.lstrip().startswith("Token Beggar:")).strip()


def judge(task: dict, answer: str) -> list[bool]:
    facts = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(task["facts"]))
    prompt = JUDGE.format(task=task["prompt"], facts=facts, answer=strip_footer(answer))
    cmd = [
        CLAUDE,
        "-p",
        prompt,
        "--model",
        JUDGE_MODEL,
        "--effort",
        "low",
        "--setting-sources",
        "project",
        "--strict-mcp-config",
        "--output-format",
        "json",
        "--tools",
        "",
    ]
    for _ in range(3):
        out = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd="/tmp", timeout=300).stdout
        try:
            text = json.loads(out)["result"]
            items = json.loads(text[text.index("{") : text.rindex("}") + 1])["items"]
            if len(items) == len(task["facts"]):
                return [bool(x) for x in items]
        except (ValueError, KeyError, json.JSONDecodeError):
            continue
    raise RuntimeError("judge failed for " + task["id"])


def usage(result: dict, top: str) -> dict:
    models = result.get("modelUsage") or {}
    total_tokens = top_tokens = 0
    for name, u in models.items():
        n = u.get("inputTokens", 0) + u.get("outputTokens", 0) + u.get("cacheReadInputTokens", 0) + u.get("cacheCreationInputTokens", 0)
        total_tokens += n
        if top in name:
            top_tokens += n
    return {
        "cost": result.get("total_cost_usd"),
        "total_tokens": total_tokens,
        "top_tokens": top_tokens,
        "turns": result.get("num_turns"),
        "seconds": round((result.get("duration_ms") or 0) / 1000, 1),
        "models": sorted(models),
    }


def main() -> None:
    global RAW, OUT
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "final"
    RAW, OUT = RESULTS / out / "raw", RESULTS / out / "scores.json"
    scores = json.loads(OUT.read_text()) if OUT.exists() else {}
    files = sorted(RAW.glob("*.json"))
    random.Random(3).shuffle(files)  # judge order carries no arm information
    for path in files:
        record = json.loads(path.read_text())
        key = path.stem
        if key in scores:
            continue
        task = BY_ID[record["task"]]
        result = record["result"]
        row = {
            "task": task["id"],
            "class": task["class"],
            "held_out": bool(task.get("held_out")),
            "arm": record["arm"],
            "rep": record["rep"],
            **usage(result, record["top"]),
            "error": result.get("is_error") or "error" in result,
        }
        if task["check"]:
            row.update(code_ok(record, task))
            row["quality"] = 1.0 if row["check"] and row["tests"] else 0.0
        else:
            items = judge(task, result.get("result", ""))
            row["items"] = items
            row["quality"] = sum(items) / len(items)
        scores[key] = row
        OUT.write_text(json.dumps(scores, indent=1, sort_keys=True))
        print(key, row["quality"], row["cost"], flush=True)


if __name__ == "__main__":
    main()
