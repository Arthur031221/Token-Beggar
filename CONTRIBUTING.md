# Contributing

Issues and pull requests are welcome.

## Setup

Python 3.10 or newer, no dependencies.

```
python3 -m unittest discover -s tests -t .
uvx ruff check . && uvx ruff format --check .
cd benchmark && python3 selftest.py
```

## Changing the router

The router is only worth having if it saves money without changing the answer. So a change to `data/profiles.json`, the card text or the skill needs a benchmark run before and after:

```
cd benchmark
python3 run.py --top opus --effort high --arms alone,dynamic --force
python3 score.py && python3 report.py
```

A full run costs a few US dollars at list price. Put the numbers in the pull request. Report losses as well as wins.

## Adding a benchmark task

Add it to `benchmark/tasks.py` with either a hidden check script (code tasks) or a checklist of facts (answer tasks). Run `python3 selftest.py`: every code task must fail on the untouched fixture.

## Style

Standard library only. Small functions, a docstring that says why, no dead code. No emoji in code or docs.
