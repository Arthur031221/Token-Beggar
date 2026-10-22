"""Runs the benchmark: each task once per arm, same model, effort and prompt. Arms are defined in arms.py.

    python3 run.py --top opus --effort high --workers 4 --arms alone,v020,final [--only m1-rename,heldout] [--rep 1] [--out final]

Raw claude -p JSON goes to results/<out>/raw/. Scoring is done by score.py --out <out>.
"""

import argparse
import json
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arms
import fixture
from tasks import ALL as TASKS

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
SCRATCH = Path(os.environ.get("TB_SCRATCH", "/tmp/tb-bench"))
RESULTS = ROOT / "benchmark" / "results"
RAW = RESULTS / "raw"  # main() points this at results/<out>/raw
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


def run_one(task: dict, arm: str, top: str, effort: str, rep, extra_env: dict | None = None) -> dict:
    name = f"{task['id']}.{arm}.{rep}"
    work = SCRATCH / name
    fixture.build(work)
    if task["setup"]:
        task["setup"](work)
        subprocess.run(["git", "add", "-A"], cwd=work, check=True)
        subprocess.run(["git", "-c", "user.name=b", "-c", "user.email=b@b", "commit", "-qm", "seed"], cwd=work, check=True)
    cmd = [CLAUDE, "-p", task["prompt"], "--model", top, "--effort", effort, *FLAGS]
    env = dict(os.environ, TOKEN_BEGGAR_HOME=str(SCRATCH / "home" / name), TOKEN_BEGGAR_OFFLINE="1", **(extra_env or {}))
    plugin = arms.plugin_dir(arm)
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
        env.update(arms.extra_env(arm))
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
        "ledger": [json.loads(line) for f in (SCRATCH / "home" / name / "ledger").glob("*.jsonl") for line in f.read_text().splitlines()],
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
    ap.add_argument("--arms", default="alone,v020,final")
    ap.add_argument("--out", default="final", help="results subfolder")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    global RAW
    RAW = RESULTS / args.out / "raw"
    arm_list = args.arms.split(",")
    arms.prepare(arm_list)
    only = set(filter(None, args.only.split(",")))

    def wanted(t):
        return (
            not only
            or t["id"] in only
            or t["class"] in only
            or ("heldout" in only and t.get("held_out"))
            or ("seen" in only and not t.get("held_out"))
        )

    jobs = [(t, a) for t in TASKS if wanted(t) for a in arm_list]
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
