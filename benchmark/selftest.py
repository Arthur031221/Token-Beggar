"""Checks that every code task fails on the untouched fixture, so a pass means the work was done."""

import subprocess
import sys
from pathlib import Path

import fixture
from tasks import ALL as TASKS

bad = 0
for task in TASKS:
    if not task["check"]:
        continue
    work = Path("/tmp/tb-selftest") / task["id"]
    fixture.build(work)
    if task["setup"]:
        task["setup"](work)
    res = subprocess.run(
        [sys.executable, "-c", task["check"]], cwd=work, capture_output=True, text=True, env={"PYTHONPATH": str(work), "PATH": "/usr/bin:/bin"}
    )
    status = "ok (fails before work)" if res.returncode else "PROBLEM: passes untouched"
    bad += not res.returncode
    print(f"{task['id']:12} {status}")
sys.exit(1 if bad else 0)
