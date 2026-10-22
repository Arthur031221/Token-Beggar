"""A long multi-turn session: logs are pasted into the chat until the context passes 200k, then the model is asked for what it learned early and in each phase.

    python3 long_session.py --arms alone,final-no-early,final --reps 3 [--files 15] [--top opus --effort high] [--out long]

One claude process per run, kept alive with stream-json input so the turns share one session. The harness plays the user:
it sends the next prompt when a reply ends, and types /compact when (and only when) the reply it just read suggests that.
Every arm gets the same rule, so an arm that never suggests it never compacts, except when the host does it by itself.

Score: one point per correct line count and slowest request id in each file turn, per recalled early fact, and per
aggregate answer, all matched exactly. Cost is the list price total_cost_usd of the whole process (every model, every turn,
compactions included). Output: results/<out>/long.json
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arms as arm_defs
import run

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from token_beggar import transcript  # noqa: E402

PHASE = 3  # file turns per phase
FACTS = {"codename": "heron", "window": "tuesday 03:00", "oncall": "priya"}
EARLY = (
    "Before we start, remember these three facts for later: the release codename is heron, the deploy window is Tuesday 03:00 UTC, "
    "and the on-call engineer is Priya. Reply with the word ok."
)
FILE_ASK = "Here is log part {n:02d}, pasted whole:\n\n{body}\n\nReply in one line: the number of lines with status=500, and the req id with the highest ms.{phase}"
PHASE_DONE = " That completes phase {k} of the log review; the next phase covers the next three parts."
RECALL = "Without opening any file: what are the release codename, the deploy window and the on-call engineer? One line."
TOTAL = "Using what you found in all the log files so far: the total number of status=500 lines across all of them, and the req id with the highest ms overall. One line."


def build_logs(work: Path, files: int, seed: int = 5) -> list[dict]:
    """Deterministic log files, ~20k tokens each. Returns the truth per file."""
    rng = random.Random(seed)
    (work / "logs").mkdir()
    truth = []
    for n in range(1, files + 1):
        rows = []
        slow = rng.randrange(400)
        errors = set(rng.sample(range(400), rng.randint(3, 9)))
        top_id = f"r{n:02d}x{rng.randrange(10**5):05d}"
        for i in range(400):
            ms = rng.randint(5, 900)
            req = top_id if i == slow else f"r{n:02d}x{rng.randrange(10**5):05d}"
            ms = 9000 + n if i == slow else ms
            status = 500 if i in errors else rng.choice([200, 200, 200, 201, 204, 301, 404])
            rows.append(
                f"2026-03-{n:02d}T{i // 15:02d}:{i % 15 * 4:02d}:00Z req={req} status={status} ms={ms} "
                f"path=/api/{rng.choice(['cart', 'order', 'item', 'user', 'quote'])}/{rng.randrange(1000)} bytes={rng.randint(100, 9000)}"
            )
        (work / "logs" / f"part-{n:02d}.txt").write_text("\n".join(rows) + "\n")
        truth.append({"errors": len(errors), "top": top_id, "ms": 9000 + n})
    return truth


def turns(work: Path, files: int) -> list[tuple[str, str]]:
    """The log text is pasted into the prompt, as a user would, so it sits in the chat's own context whatever the routing."""

    def ask(n: int) -> str:
        phase = PHASE_DONE.format(k=n // PHASE) if n % PHASE == 0 and n < files else ""
        return FILE_ASK.format(n=n, body=(work / "logs" / f"part-{n:02d}.txt").read_text().rstrip(), phase=phase)

    plan = [("early", EARLY)] + [(f"file{n}", ask(n)) for n in range(1, files + 1)]
    return plan + [("recall", RECALL), ("total", TOTAL)]


class Session:
    def __init__(self, cmd: list[str], work: Path, env: dict):
        self.proc = subprocess.Popen(
            cmd, cwd=work, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1
        )

    def send(self, text: str, timeout: int = 1500) -> dict:
        message = {"type": "user", "message": {"role": "user", "content": text}}
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                return {"error": "process ended"}
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                return event
        return {"error": "timeout"}

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            self.proc.kill()


def score_file(text: str, truth: dict) -> int:
    return int(bool(re.search(rf"\b{truth['errors']}\b", text))) + int(truth["top"] in text)


def score_recall(text: str) -> int:
    low = text.lower()
    return int(FACTS["codename"] in low) + int("tuesday" in low and "03:00" in low) + int(FACTS["oncall"] in low)


def score_total(text: str, truth: list[dict]) -> int:
    best = max(truth, key=lambda t: t["ms"])["top"]
    return int(bool(re.search(rf"\b{sum(t['errors'] for t in truth)}\b", text))) + int(best in text)


def context_profile(session_id: str) -> dict:
    path = None
    for found in (Path.home() / ".claude" / "projects").glob(f"*/{session_id}.jsonl"):
        path = found
    if not path:
        return {}
    items = [json.loads(line) for line in path.read_text().splitlines() if line.strip().startswith("{")]
    sizes = []
    for entry in items:
        if entry.get("type") == "assistant" and not entry.get("isSidechain") and (entry.get("message") or {}).get("usage"):
            sizes.append(transcript.context_tokens([entry]))
    return {"peak_context": max(sizes, default=0), "mean_context": round(sum(sizes) / len(sizes)) if sizes else 0, "requests": len(sizes)}


def run_one(arm: str, rep: int, args, outdir: Path) -> dict:
    name = f"long.{arm}.{rep}"
    work = run.SCRATCH / name
    import fixture

    fixture.build(work)
    truth = build_logs(work, args.files)
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    subprocess.run(["git", "-c", "user.name=b", "-c", "user.email=b@b", "commit", "-qm", "logs"], cwd=work, check=True)
    flags = [f for f in run.FLAGS[:-2]]
    cmd = [
        run.CLAUDE,
        "-p",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--verbose",
        "--model",
        args.top,
        "--effort",
        args.effort,
        *flags,
    ]
    plugin = arm_defs.plugin_dir(arm)
    env = dict(os.environ, TOKEN_BEGGAR_HOME=str(run.SCRATCH / "home" / name), TOKEN_BEGGAR_OFFLINE="1")
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
        env.update(arm_defs.extra_env(arm))
    session = Session(cmd, work, env)
    log, points, max_points, compactions, session_id, last, started = [], 0, 0, 0, "", {}, time.time()
    try:
        for label, prompt in turns(work, args.files):
            result = session.send(prompt)
            last = result if "total_cost_usd" in result else last
            session_id = result.get("session_id", session_id)
            text = str(result.get("result", result.get("error", "")))
            if label.startswith("file"):
                got, top = score_file(text, truth[int(label[4:]) - 1]), 2
            elif label == "recall":
                got, top = score_recall(text), 3
            elif label == "total":
                got, top = score_total(text, truth), 2
            else:
                got, top = 0, 0
            points, max_points = points + got, max_points + top
            log.append({"turn": label, "text": text[:300], "points": got, "of": top, "cost_so_far": result.get("total_cost_usd")})
            if "/compact" in text and label not in ("recall", "total"):
                compacted = session.send("/compact")
                compactions += 1
                log.append({"turn": "compact", "text": str(compacted.get("result", ""))[:120], "cost_so_far": compacted.get("total_cost_usd")})
                last = compacted if "total_cost_usd" in compacted else last
    finally:
        session.close()
    record = {
        "arm": arm,
        "rep": rep,
        "top": args.top,
        "effort": args.effort,
        "cost": last.get("total_cost_usd"),
        "seconds": round(time.time() - started, 1),
        "points": points,
        "of": max_points,
        "quality": round(points / max_points, 3) if max_points else 0,
        "compactions": compactions,
        "models": sorted(last.get("modelUsage") or {}),
        "log": log,
        **context_profile(session_id),
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{name}.json").write_text(run.scrub(json.dumps(record, indent=1)))
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="alone,final-no-early,final")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--files", type=int, default=15)
    ap.add_argument("--top", default="opus")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", default="long")
    args = ap.parse_args()
    arm_list = args.arms.split(",")
    arm_defs.prepare(arm_list)
    outdir = run.RESULTS / args.out
    jobs = [(a, r) for r in range(1, args.reps + 1) for a in arm_list if not (outdir / f"long.{a}.{r}.json").exists()]
    print(f"{len(jobs)} runs", flush=True)

    def go(job):
        record = run_one(*job, args, outdir)
        print(
            f"{job[0]:16} rep{job[1]} cost={record['cost']} quality={record['quality']} peak={record.get('peak_context')} compactions={record['compactions']}",
            flush=True,
        )

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(go, jobs))


if __name__ == "__main__":
    main()
