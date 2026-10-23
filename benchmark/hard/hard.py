"""The hard task benchmark: real closed issues from open source Python projects, fixed upstream by a merged pull request with tests.

    python3 hard.py prepare [--only id,id]      clone the repositories, read the issues, run the reference fix (once per task)
    python3 hard.py run --arms alone,main,sized --reps 1,2,3 [--only id] [--workers 3] [--top opus] [--effort high] [--out hard]
    python3 hard.py rescore --only task.arm.rep   score a saved run again from its diff (when the test suite did not run)

An agent starts from the parent of the fixing commit with the issue text as the prompt. After it stops, the tests that the fix added or
changed are put back (the agent never saw them) and the whole test suite runs. fail_to_pass: tests that fail on the parent with those
tests and pass on the fix. pass_to_pass: tests that pass on both. A run is resolved when every fail_to_pass test passes and no
pass_to_pass test fails.

Setup of one task, so anyone can rerun it: clone the repository, `git fetch` the base commit into an empty repository, create `.venv`,
`pip install <install>` in it, then `.venv/bin/python -m pytest -q -rA <run paths>`. The commits and commands are in data/<id>.json.
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent))
import arms  # noqa: E402
from hard_tasks import TASKS  # noqa: E402

ROOT = HERE.parent.parent
CACHE = Path(os.environ.get("TB_HARD_CACHE", "/tmp/tbhard/repos"))
SCRATCH = Path(os.environ.get("TB_HARD_SCRATCH", "/tmp/tb-hard"))
DATA = HERE / "data"
RESULTS = ROOT / "benchmark" / "results" / "hard"
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
# The same permissions in every arm, as in the small benchmark.
FLAGS = [
    "--setting-sources", "project", "--strict-mcp-config", "--permission-mode", "acceptEdits",
    "--allowedTools", "Bash", "Read", "Edit", "Write", "Glob", "Grep", "--output-format", "json",
]  # fmt: skip
PYTEST = [".venv/bin/python", "-m", "pytest", "-q", "-rA", "--no-header", "-p", "no:cacheprovider", "--continue-on-collection-errors"]
RESULT_LINE = re.compile(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED)\s+(\S+)", re.MULTILINE)
# Django's own runner (unittest, verbose): "test_x (module.Class.test_x) ... ok", with the docstring on a second line when there is one
DJANGO_LINE = re.compile(r"^(\w+) \(([\w.]+)\)(?:\n[^\n]*?)? \.\.\. (ok|FAIL|ERROR|skipped|expected failure|unexpected success)", re.MULTILINE)
DJANGO_STATUS = {"ok": "PASSED", "FAIL": "FAILED", "ERROR": "ERROR", "skipped": "SKIPPED", "expected failure": "XFAIL", "unexpected success": "XPASS"}


def sh(cmd, cwd=None, check=True, timeout=900, **kw):
    pipes = {"stdout": subprocess.PIPE} if "stderr" in kw else {"capture_output": True}
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, timeout=timeout, **pipes, **kw)


def info(task: dict) -> dict:
    return json.loads((DATA / f"{task['id']}.json").read_text())


def cached(repo: str) -> Path:
    path = CACHE / repo.split("/")[1]
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        sh(["git", "clone", "-q", f"https://github.com/{repo}", str(path)], timeout=1200)
    return path


def checkout(task: dict, commit: str, dest: Path) -> Path:
    """An empty repository holding only the history up to `commit`, so the agent cannot read the fix from git. Installs the project in .venv."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    sh(["git", "init", "-q"], cwd=dest)
    sh(["git", "fetch", "-q", "--no-tags", str(cached(task["repo"])), commit], cwd=dest, timeout=1200)
    sh(["git", "checkout", "-q", "FETCH_HEAD"], cwd=dest)
    (dest / ".git" / "info" / "exclude").write_text(".venv\n__pycache__\n*.egg-info\n.pytest_cache\n")
    if task.get("python"):  # an older interpreter for projects that predate Python 3.12
        sh(["uv", "venv", "-q", "--seed", "--python", task["python"], ".venv"], cwd=dest)
    else:
        sh([sys.executable, "-m", "venv", ".venv"], cwd=dest)
    sh([".venv/bin/pip", "install", "-q", "--disable-pip-version-check", *task["install"].split()], cwd=dest, timeout=1200,
       env=dict(os.environ, SETUPTOOLS_SCM_PRETEND_VERSION="9.9.9"))  # projects that take their version from git tags have none here
    return dest


def restore_tests(task: dict, commit: str, work: Path) -> None:
    """Replace the test directories with the ones at the fixing commit."""
    for path in task["tests"]:
        shutil.rmtree(work / path, ignore_errors=True)
    archive = subprocess.run(["git", "archive", commit, *task["tests"]], cwd=cached(task["repo"]), capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(work)], input=archive, check=True)


def run_tests(task: dict, work: Path) -> dict[str, str]:
    """{test id: PASSED | FAILED | ERROR ...} for the task's test paths."""
    django = task.get("runner") == "django"
    cmd = [".venv/bin/python", "tests/runtests.py", "--parallel", "1", "-v", "2", *task["run"]] if django else [*PYTEST, *task["run"]]
    try:
        proc = sh(cmd, cwd=work, check=False, timeout=1500, stderr=subprocess.STDOUT) if django else sh(cmd, cwd=work, check=False, timeout=900)
    except subprocess.TimeoutExpired:
        return {}
    if django:
        return {(m[1] if m[1].endswith("." + m[0]) else f"{m[1]}.{m[0]}"): DJANGO_STATUS[m[2]] for m in DJANGO_LINE.findall(proc.stdout)}
    return {name: status for status, name in RESULT_LINE.findall(proc.stdout)}


def swe_issue(instance: str) -> dict:
    """The problem statement of a SWE-bench Verified instance, read from the parquet file named by TB_SWE_PARQUET (needs pyarrow)."""
    import pyarrow.parquet as pq

    row = next(r for r in pq.read_table(os.environ["TB_SWE_PARQUET"]).to_pylist() if r["instance_id"] == instance)
    title, _, body = row["problem_statement"].strip().partition("\n")
    return {"title": title.strip(), "body": body.strip(), "url": f"https://github.com/{row['repo']}/pull/{instance.rsplit('-', 1)[1]}"}


def prepare(task: dict) -> None:
    DATA.mkdir(exist_ok=True)
    repo = cached(task["repo"])
    pr = json.loads(sh(["gh", "pr", "view", str(task["pr"]), "-R", task["repo"], "--json", "mergeCommit,title,url,files"]).stdout)
    if task.get("swe"):  # the issue text of a SWE-bench Verified instance; only needed here, the text is stored in data/<id>.json
        issue = swe_issue(task["swe"])
    else:
        issue = json.loads(sh(["gh", "issue", "view", str(task["issue"]), "-R", task["repo"], "--json", "title,body,url"]).stdout)
    fix = pr["mergeCommit"]["oid"]
    base = sh(["git", "rev-parse", f"{fix}^1"], cwd=repo).stdout.strip()
    files = [f["path"] for f in pr["files"]]
    work = SCRATCH / "prepare" / task["id"]
    checkout(task, fix, work)
    after = run_tests(task, work)  # the fix, with its own tests
    checkout(task, base, work)
    restore_tests(task, fix, work)
    before = run_tests(task, work)  # the parent, with the fix's tests
    ok = {"PASSED", "XFAIL", "SKIPPED"}
    skip = task.get("exclude", [])  # tests that need a name only the fix contains (a new option, a new function): the issue cannot tell
    after = {t: s for t, s in after.items() if not any(x in t for x in skip)}
    f2p = sorted(t for t, s in after.items() if s == "PASSED" and before.get(t, "FAILED") != "PASSED")
    p2p = sorted(t for t, s in after.items() if s == "PASSED" and before.get(t) == "PASSED")
    record = {
        **{k: task[k] for k in ("id", "repo", "pr", "issue", "install", "tests", "run") if k in task}, "python": task.get("python", ""),
        "pr_url": pr["url"], "pr_title": pr["title"], "issue_url": issue["url"], "issue_title": issue["title"], "issue_body": issue["body"],
        "exclude": skip, "base": base, "fix": fix, "files_changed": files, "fail_to_pass": f2p, "pass_to_pass": p2p,
        "reference_failing_after_fix": sorted(t for t, s in after.items() if s not in ok),
    }  # fmt: skip
    (DATA / f"{task['id']}.json").write_text(json.dumps(record, indent=1) + "\n")
    print(f"{task['id']}: base {base[:9]} fix {fix[:9]} f2p {len(f2p)} p2p {len(p2p)} files {len(files)}")


def prompt_for(task: dict) -> str:
    data = info(task)
    return (
        "Resolve the issue below in this repository (the current directory) by changing the library code, and add or update tests for it. "
        "A Python virtualenv with the project installed in editable mode is at .venv; run tests with "
        + (".venv/bin/python tests/runtests.py --parallel 1 <test module, for example queries.tests>" if task.get("runner") == "django" else ".venv/bin/python -m pytest <path>")
        + ". "
        "Do not commit.\n\n"
        f"Issue: {data['issue_title']}\n\n{data['issue_body']}"
    )


def score_work(task: dict, work: Path) -> dict:
    data = info(task)
    restore_tests(task, data["fix"], work)
    got = run_tests(task, work)
    f2p = [t for t in data["fail_to_pass"] if got.get(t) == "PASSED"]
    broken = [t for t in data["pass_to_pass"] if got.get(t) != "PASSED"]
    return {
        "f2p_passed": len(f2p), "f2p_total": len(data["fail_to_pass"]), "regressions": len(broken), "regressed_tests": broken[:20],
        "resolved": len(f2p) == len(data["fail_to_pass"]) and not broken, "suite_ran": bool(got),
    }  # fmt: skip


def run_one(task: dict, arm: str, rep: int, top: str, effort: str, out: Path) -> dict:
    name = f"{task['id']}.{arm}.{rep}"
    data = info(task)
    work = SCRATCH / name / "repo"
    checkout(task, data["base"], work)
    cmd = [CLAUDE, "-p", prompt_for(task), "--model", top, "--effort", effort, *FLAGS]
    env = dict(os.environ, TOKEN_BEGGAR_HOME=str(SCRATCH / name / "home"), TOKEN_BEGGAR_OFFLINE="1")
    plugin = arms.plugin_dir(arm)
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
        env.update(arms.extra_env(arm))
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=2400)
        result, err = json.loads(proc.stdout or "{}"), proc.stderr[-400:]
    except subprocess.TimeoutExpired:
        result, err = {"error": "timeout"}, "timeout"
    except json.JSONDecodeError:
        result, err = {"error": "unparsable"}, proc.stdout[-300:]
    sh(["git", "add", "-A", "-N", "."], cwd=work, check=False)
    diff = sh(["git", "diff", "HEAD"], cwd=work, check=False).stdout
    record = {
        "task": task["id"], "arm": arm, "rep": rep, "top": top, "effort": effort, "result": result, "stderr": err,
        "ledger": [json.loads(line) for f in (SCRATCH / name / "home" / "ledger").glob("*.jsonl") for line in f.read_text().splitlines()],
        "score": score_work(task, work),
    }  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    scrub = lambda text: text.replace(str(Path.home()), "~").replace(str(SCRATCH), "<work>")  # noqa: E731
    (out / f"{name}.json").write_text(scrub(json.dumps(record, indent=1)))
    (out / f"{name}.diff").write_text(scrub(diff))
    shutil.rmtree(SCRATCH / name, ignore_errors=True)
    return record


def rescore(name: str) -> None:
    """Score a saved run again from its diff, for a run whose test suite did not run (a harness failure, not the agent's)."""
    task_id, arm, rep = name.split(".")
    task = next(t for t in TASKS if t["id"] == task_id)
    raw = RESULTS / "raw"
    work = SCRATCH / f"rescore-{name}" / "repo"
    checkout(task, info(task)["base"], work)
    sh(["git", "apply", "--whitespace=nowarn", str(raw / f"{name}.diff")], cwd=work)
    record = json.loads((raw / f"{name}.json").read_text())
    record["score"] = score_work(task, work)
    (raw / f"{name}.json").write_text(json.dumps(record, indent=1))
    shutil.rmtree(SCRATCH / f"rescore-{name}", ignore_errors=True)
    print(name, record["score"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "run", "rescore"])
    ap.add_argument("--only", default="")
    ap.add_argument("--arms", default="alone,main,sized")
    ap.add_argument("--reps", default="1")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--top", default="opus")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--out", default="hard")
    ap.add_argument("--max-cost", type=float, default=0.0, help="stop starting runs once the raw files add up to this many dollars")
    args = ap.parse_args()
    only = set(filter(None, args.only.split(",")))
    if args.cmd == "rescore":
        for name in only:
            rescore(name)
        return
    chosen = [t for t in TASKS if not only or t["id"] in only]
    if args.cmd == "prepare":
        for task in chosen:
            prepare(task)
        return
    out = RESULTS.parent / args.out / "raw"
    arm_list = args.arms.split(",")
    arms.prepare(arm_list)
    jobs = [(t, a, int(r)) for r in args.reps.split(",") for t in chosen for a in arm_list if not (out / f"{t['id']}.{a}.{r}.json").exists()]
    random.Random(11).shuffle(jobs)
    print(f"{len(jobs)} runs", flush=True)

    def spent() -> float:
        return sum((json.loads(f.read_text()).get("result") or {}).get("total_cost_usd") or 0 for f in out.glob("*.json"))

    def go(job):
        task, arm, rep = job
        if args.max_cost and spent() >= args.max_cost:
            print(f"budget reached, skipping {task['id']} {arm} {rep}", flush=True)
            return
        rec = run_one(task, arm, rep, args.top, args.effort, out)
        res = rec["result"]
        print(f"{task['id']:24} {arm:6} rep{rep} cost={res.get('total_cost_usd')} turns={res.get('num_turns')} resolved={rec['score']['resolved']}", flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(go, jobs))


if __name__ == "__main__":
    main()
