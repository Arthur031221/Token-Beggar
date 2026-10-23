"""A blind review of the diffs of the hard benchmark: one packet per task with the issue and every diff under a random id.

    python3 blind.py pack [--dir /tmp/tb-blind] [--arms alone,main,scoped]   write one packet per task and key.json (id to run)
    python3 blind.py parse --dir /tmp/tb-blind                               read the answers (<task>.answer.txt) into blind.json

The reviewer never sees which setup wrote a diff, nor the hidden tests. Each answer line is `id score reason` with score 0 (wrong or
does not address the issue), 1 (right idea but narrow or with a defect) or 2 (a correct and complete fix). Lines of the diff for
documentation files and the change log are left out, and test files are named but not shown and the code is cut at 14000 characters. In this run the reviewer was Gemini
Flash through agy, so the review costs no Claude quota. It is a second opinion beside the hidden tests, not a replacement for them.
"""

import argparse
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "results" / "hard" / "raw"
OUT = HERE.parent / "results" / "hard" / "blind.json"
SKIP = re.compile(r"^(CHANGES|CHANGELOG|HISTORY|NEWS)|\.(rst|md|txt)$|^docs?/", re.I)
ASK = (
    "You review candidate fixes for one issue of an open source Python project, blind: you do not know who wrote them. For every diff below "
    "give one line `id score reason` (reason under 15 words). Score 0 = wrong, or does not address the issue. 1 = the right idea but narrow "
    "(leaves out a place where the same bug shows) or with a defect. 2 = a correct, complete fix of the issue. Judge only the code and the tests in the diff "
    "against the issue. Output only those lines, one per diff id."
)


def keep(diff: str) -> str:
    """Code hunks only, whole files at a time; test files are named with their size, never cut in the middle."""
    out, size = [], 0
    for part in re.split(r"(?m)^(?=diff --git )", diff):
        m = re.match(r"diff --git a/(\S+)", part)
        if not m or SKIP.search(m.group(1)):
            continue
        if re.search(r"(^|/)(tests?/|test_|conftest)", m.group(1)):
            part = f"diff --git a/{m.group(1)} (test file, {part.count(chr(10) + '+')} lines added, not shown)\n"
        elif size + len(part) > 14000:
            part = part[: max(0, 14000 - size)] + "\n(rest of this diff not shown)\n"
        size += len(part)
        out.append(part)
    return "".join(out)


def pack(directory: Path, arms: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(5)
    key = {}
    for ti, data in enumerate(sorted((HERE / "data").glob("*.json"))):
        info = json.loads(data.read_text())
        runs = [p for p in sorted(RAW.glob(f"{info['id']}.*.diff")) if p.name.split(".")[1] in arms]
        if not runs:
            continue
        rng.shuffle(runs)
        text = [ASK, f"\n# Issue: {info['issue_title']}\n\n{info['issue_body'][:5000]}\n"]
        for i, path in enumerate(runs):
            rid = f"t{ti:02d}d{i + 1:02d}"
            key[rid] = path.name.removesuffix(".diff")
            text.append(f"\n# Diff {rid}\n\n{keep(path.read_text()) or '(empty)'}\n")
        (directory / f"{info['id']}.md").write_text("".join(text))
    (directory / "key.json").write_text(json.dumps(key, indent=1))
    print(len(key), "diffs in", directory)


def parse(directory: Path) -> None:
    key = json.loads((directory / "key.json").read_text())
    scores, missing = {}, set(key)
    for answer in sorted(directory.glob("*.answer.txt")):
        for line in answer.read_text().splitlines():
            m = re.match(r"\W*(t\d{2}d\d{2})\W+([012])\b", line)
            if m and m.group(1) in key:
                scores[key[m.group(1)]] = int(m.group(2))
                missing.discard(m.group(1))
    OUT.write_text(json.dumps(dict(sorted(scores.items())), indent=1) + "\n")
    print(len(scores), "scored,", len(missing), "missing", sorted(missing)[:10])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pack", "parse"])
    ap.add_argument("--dir", default="/tmp/tb-blind")
    ap.add_argument("--arms", default="alone,main,scoped")
    args = ap.parse_args()
    pack(Path(args.dir), args.arms.split(",")) if args.cmd == "pack" else parse(Path(args.dir))


if __name__ == "__main__":
    main()
