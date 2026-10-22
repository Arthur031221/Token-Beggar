"""Runs the benchmark: each task twice (alone, with Token Beggar), same model, same effort, same prompt.

    python3 run.py --top opus --effort high --workers 4 [--only m1-rename,r1-tracking] [--rep 1]

Raw claude -p JSON goes to results/raw/. Scoring is done by score.py.
"""

import argparse
import json
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fixture
from tasks import TASKS

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
SCRATCH = Path(os.environ.get("TB_SCRATCH", "/tmp/tb-bench"))
RAW = ROOT / "benchmark" / "results" / "raw"
# Both arms get the same tool permissions. Without Bash allowed, headless subagents are denied their shell and the run measures permission prompts instead of routing.
FLAGS = [
    "--setting-sources",
    "project",
    "--strict-mcp-config",
    "--permission-mode",
    "acceptEdits",
    "--allowedTools",
    "Bash",
    "Read",
    "Edit",
    "Write",
    "Glob",
    "Grep",
    "--output-format",
    "json",
]


def scrub(text: str) -> str:
    return text.replace(str(Path.home()), "~").replace(str(SCRATCH), "<work>")


def run_one(task: dict, arm: str, top: str, effort: str, rep: int) -> dict:
    name = f"{task['id']}.{arm}.{rep}"
    work = SCRATCH / name
    fixture.build(work)
    if task["setup"]:
        task["setup"](work)
        subprocess.run(["git", "add", "-A"], cwd=work, check=True)
        subprocess.run(["git", "-c", "user.name=b", "-c", "user.email=b@b", "commit", "-qm", "seed"], cwd=work, check=True)
    cmd = [CLAUDE, "-p", task["prompt"], "--model", top, "--effort", effort, *FLAGS]
    env = dict(os.environ, TOKEN_BEGGAR_HOME=str(SCRATCH / "home" / name), TOKEN_BEGGAR_OFFLINE="1")
    if arm == "beggar":
        cmd += ["--plugin-dir", str(ROOT)]
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1500)
        out, err = proc.stdout, proc.stderr[-400:]
    except subprocess.TimeoutExpired:
        out, err = "{}", "timeout"
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        data = {"error": "unparsable", "stdout_tail": out[-300:]}
    diff = subprocess.run(["git", "diff", "HEAD", "--stat"], cwd=work, capture_output=True, text=True).stdout
    record = {
        "task": task["id"],
        "class": task["class"],
        "arm": arm,
        "rep": rep,
        "top": top,
        "effort": effort,
        "result": data,
        "stderr": err,
        "diff_stat": diff,
        "workdir": name,
    }
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(scrub(json.dumps(record, indent=1)))
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", default="opus")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--arms", default="alone,beggar")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    only = set(filter(None, args.only.split(",")))
    jobs = [(t, a) for t in TASKS if not only or t["id"] in only or t["class"] in only for a in args.arms.split(",")]
    jobs = [(t, a) for t, a in jobs if args.force or not (RAW / f"{t['id']}.{a}.{args.rep}.json").exists()]
    random.Random(7).shuffle(jobs)
    print(f"{len(jobs)} runs", flush=True)

    def go(job):
        task, arm = job
        rec = run_one(task, arm, args.top, args.effort, args.rep)
        cost = (rec["result"] or {}).get("total_cost_usd")
        print(f"{task['id']:12} {arm:7} cost={cost}", flush=True)
        return rec

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(go, jobs))


if __name__ == "__main__":
    main()
