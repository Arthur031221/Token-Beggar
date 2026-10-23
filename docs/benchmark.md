# Benchmarks

Everything here is cost at list price, from the agent's own JSON (`modelUsage`), cache included, for the chat and every worker it started. The multiple is the cost without Token Beggar divided by the cost with it, with a 95 percent interval from a bootstrap over the runs of each task (2000 resamples). A saving is claimed only at 1.15x or more with the whole interval above 1.0x, because the run to run spread was about that large.

The three setups are named the same way everywhere:

- **Without Token Beggar**: the chat model working alone.
- **v0.2.0 (previous release)**: the plugin as released at commit 9b63cdb. A version here is a tagged release of this repository.
- **v0.3.0 (this release)**: the plugin as released in this version.

The hard benchmark has no run of the released v0.2.0. Its comparison is **Main before v0.3.0 (commit b761ce6)**, the card on the main branch just before the size-aware change. It is close to v0.2.0 in spirit and not identical to it. The small benchmark was run before v0.3.0 existed, so its last column is also Main before v0.3.0. v0.3.0 was not re-run on the small tasks. The two cards give the same instruction for a small task (do it inline), so the small result is expected to carry over, but that is a reading and not a measurement.

Every raw run is committed under `benchmark/results/`.

## Hard tasks

18 real bugs from the history of 12 open source Python projects. Each task is one merged pull request: the chat starts from the commit before the fix, gets the issue text, and has to make the fix. It is scored by the tests the maintainers added in that pull request (the hidden tests, which the chat never sees) plus the tests that passed before. Opus 5.5 at high effort is the chat model, 3 runs per task and setup, 54 runs per setup. All setups get the same prompt, the same tools and the same permissions.

| Setup | Runs | Cost per run | Multiple vs Without Token Beggar (95% interval) | Resolved | Regressions | Turns | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Without Token Beggar | 54 | $0.69 | 1.00x | 70% | 0 | 23 | 187 |
| Main before v0.3.0 (commit b761ce6) | 54 | $0.45 | 1.54x (1.46 to 1.64) | 65% | 0 | 13 | 163 |
| v0.3.0 (this release) | 54 | $0.49 | 1.42x (1.33 to 1.51) | 69% | 0 | 10 | 168 |

"Resolved" means every test that should flip from failing to passing does, and no test that passed before fails. Two further card drafts were run and are in the raw data. They are marked "not shipped" in `benchmark/results/hard/report.md`.

What the table says, and does not say:

- v0.3.0 costs about 29 percent less than working alone ($0.49 against $0.69) and resolves 69 percent against 70 percent. The difference of one task in a hundred is inside the run to run spread (the per repetition values are in the report: 67, 67, 72 for v0.3.0 and 67, 78, 67 for working alone).
- Main before v0.3.0 was cheaper still (1.54x) and resolved fewer (65 percent). On click-format-filename it finished in 2 turns with a wrong fix, 0 of 3 against 3 of 3 working alone. v0.3.0 spends more, on reviewing the whole diff and listing every site that shares the symptom, to avoid that. The cost of that review is the gap between 1.54x and 1.42x. It was a trade, chosen for quality at equal cost.
- Claim: equal hidden-test results. Not claimed: equal code quality. A blind review (below) rated the v0.3.0 diffs lower.
- Three tasks were not resolved in any of their 9 runs (django-aggregate-count, rich-inspect-methods, structlog-exception-outside), and pylint-pyreverse-hints and werkzeug-rule-methods almost never. They count in every setup alike, which is why no setup resolves much above two thirds.
- Time is level with working alone (168 seconds against 187), not faster.

### Blind review

For 162 of the diffs, a separate model (Gemini Flash, through the `agy` CLI) read the issue, the maintainers' diff and one candidate diff, without knowing which setup wrote it, and scored it from 0 to 2. The scores were 1.33 for working alone, 1.15 for Main before v0.3.0 and 0.94 for v0.3.0.

Two cautions. This is one small model as the judge, and its scores agree only weakly with the hidden tests. It is reported because it points the wrong way for v0.3.0, not because it is a clean measurement. Packets and scores: `benchmark/hard/blind.py`, `benchmark/results/hard/blind.json`.

### The tasks

| Task | Repository | Pull request | Base commit | Install command (in a fresh virtual environment) |
| --- | --- | --- | --- | --- |
| click-format-filename | pallets/click | 2553 | 0c8f301d2a | `-e . pytest` |
| django-aggregate-count | django/django | 16263 | 321ecb40f4 | `-e .` (Python 3.11) |
| django-constraint-violation | django/django | 16560 | 51c9bb7cd1 | `-e .` (Python 3.11) |
| django-prefetch-sliced | django/django | 15957 | f387d024fc | `-e .` (Python 3.11) |
| django-remake-table-index | django/django | 15629 | 694cf458f1 | `-e .` (Python 3.10) |
| jinja-namespace-tuple | pallets/jinja | 1664 | 1d55cddbb2 | `-e . pytest trio` |
| md-backslash-smarty | Python-Markdown/markdown | 1272 | 77fb7f1b51 | `-e . pytest pyyaml` |
| md-footnote-order | Python-Markdown/markdown | 1546 | 23c301de28 | `-e . pytest pyyaml` |
| packaging-extras-marker | pypa/packaging | 888 | 8e49b43737 | `-e . pytest pretend` |
| pylint-pyreverse-hints | pylint-dev/pylint | 4551 | 14731ad97a | `-e . pytest` (Python 3.9) |
| pylint-regexp-csv | pylint-dev/pylint | 8898 | 1f8c4d9eb1 | `-e . pytest pytest-timeout` (Python 3.10) |
| pytest-mark-mro | pytest-dev/pytest | 10356 | 15ac0349b2 | `-e . hypothesis setuptools<70` (Python 3.10) |
| rich-inspect-methods | Textualize/rich | 2294 | 5ccf4ed376 | `-e . pytest attrs` |
| sphinx-include-source-read | sphinx-doc/sphinx | 11510 | 6cb783c002 | `-e .[test]` (Python 3.10) |
| sphinx-property-type | sphinx-doc/sphinx | 9461 | 445c340cbd | `-e .[test]` plus pinned older dependencies, see the data file (Python 3.9) |
| structlog-exception-outside | hynek/structlog | 680 | 234b6fe02d | `-e .[dev] pytest` |
| sympy-permutation-subclass | sympy/sympy | 12489 | 56bf637b93 | `-e . pytest mpmath` (Python 3.9) |
| werkzeug-rule-methods | pallets/werkzeug | 3109 | bf7529e626 | `-e . pytest pytest-timeout ephemeral-port-reserve watchdog cryptography` |

The pull request is at `https://github.com/<repository>/pull/<number>`. The fix commit, the failing and passing tests and the run paths are in `benchmark/hard/data/<task>.json`.

A 19th task, sympy-power-assumptions, was dropped before the final runs: its test suite takes longer than the 40 minute limit on one run. Runs that were set aside, this task's among them, are kept in `benchmark/results/hard/dropped`, and no table counts them.

### Reproduce

```
cd benchmark/hard
python3 hard.py prepare            # clone, check out the base commits, build the environments
python3 hard.py run --arms alone,main,scoped --reps 3
python3 hard.py rescore
python3 report_hard.py --out hard --blind ../results/hard/blind.json
```

The arm names `alone`, `main` and `scoped` are script names and exist only in `benchmark/`. In the reports they print as Without Token Beggar, Main before v0.3.0 and v0.3.0 (this release). The 229 runs of the hard benchmark, with the draft arms, cost about $125 in list price.

## Small tasks

28 small tasks on a Python shop project, in 7 classes (mechanical edits, reading, routine code, several files, debugging, design, review), 4 each, 3 runs per setup, 84 runs per setup. 21 tasks are the ones the card was tuned on. 7 are held out: written after the tuning and never used for it. Opus 5.5 at high effort is the chat model.

Code tasks are scored by a hidden check plus the project tests. Answer tasks are scored against a checklist by a judge that does not see which setup wrote the text.

| Group | Without Token Beggar | v0.2.0 (previous release) | Main before v0.3.0 | Main before v0.3.0 vs without (95% interval) | Quality: without / v0.2.0 / main |
| --- | --- | --- | --- | --- | --- |
| All 28 tasks | $0.148 | $0.139 | $0.134 | 1.11x (1.08 to 1.14) | 0.96 / 0.96 / 0.99 |
| The 21 tuning tasks | $0.153 | $0.140 | $0.135 | 1.13x (1.09 to 1.16) | 0.95 / 0.96 / 0.98 |
| The 7 held-out tasks | $0.134 | $0.136 | $0.129 | 1.04x (0.99 to 1.11) | 0.98 / 0.99 / 1.00 |
| Mechanical edits | $0.120 | $0.112 | $0.124 | 0.97x (0.92 to 1.02) | 1.00 / 1.00 / 1.00 |
| Reading and summarising | $0.092 | $0.095 | $0.091 | 1.00x (0.94 to 1.07) | 0.94 / 0.90 / 0.98 |
| Routine code | $0.152 | $0.149 | $0.132 | 1.15x (1.09 to 1.22) | 1.00 / 1.00 / 1.00 |
| Several files | $0.260 | $0.194 | $0.185 | 1.40x (1.27 to 1.55) | 1.00 / 1.00 / 1.00 |
| Debugging | $0.153 | $0.154 | $0.140 | 1.09x (1.02 to 1.17) | 1.00 / 1.00 / 1.00 |
| Design | $0.114 | $0.116 | $0.114 | 1.00x (0.94 to 1.06) | 0.94 / 0.94 / 1.00 |
| Review | $0.144 | $0.153 | $0.148 | 0.97x (0.91 to 1.04) | 0.83 / 0.92 / 0.92 |

Read it plainly:

- The mixed-set result (1.11x) is under the 1.15x line, so it is not a claimed saving. Only work on several files (1.40x) and routine code (1.15x) are clear of the noise.
- On the 7 held-out tasks both cards sit inside the spread of working alone (1.04x and 0.99x). The 1.13x on the tuning tasks is what tuning on a set buys. Expect 1.0x to 1.1x on work like the held-out set.
- A fixed start cost of about $0.10 per agent invocation is most of a $0.15 task. That is the one cause of the small savings that was measured, and it is why small tasks stay inline.
- Review quality is 0.92 against 0.83 alone. The checklist is short and one item moves the score a lot, and the cost ratio there is under 1.0x, so no improvement is claimed.
- I did not find why routine code (1.15x) and debugging (1.09x) gained. The card does not route those kinds, so they are read as run to run variation until a larger run says otherwise.

A fourth setup, the full card forced on at every ceiling, cost $0.141 (1.05x, 1.02 to 1.07). It is in the raw data and was never shipped as the default.

Raw runs: `benchmark/results/final/raw`. Table: `benchmark/results/final/report.md`. To reproduce: `python3 benchmark/run.py --arms alone,v020,fullcard,final`, then `score.py` and `report.py --out final --arms alone,v020,fullcard,final`. The run cost about $74 in list price including the lever arms.

## Levers

Each change aimed at cutting spend was tested alone: remove one from the card and compare, 16 tasks, 3 runs each (`benchmark/results/levers`). A lever stays only if quality is within the spread. The cost column is the cost of removing the lever, so a plus sign means the lever saves that much.

| Lever | Cost of removing it, per task | Quality with / without | Verdict |
| --- | --- | --- | --- |
| Lean worker (six tools instead of all of them) | +$0.011 (0.93x, 0.88 to 0.97) | 0.97 / 0.98 | Kept. The one lever with a saving clear of the noise |
| Batch dispatch (one worker for related jobs) | +$0.005 (0.97x, 0.93 to 1.01) | 0.97 / 0.98 | Kept. Quality holds, the saving is inside the noise |
| Shorter output (short worker reports, short answers) | +$0.003 (0.98x, 0.95 to 1.01) | 0.97 / 0.98 | Kept. Quality holds, the saving is inside the noise |
| Bulk reading to `agy` | -$0.007 (1.05x, 1.02 to 1.09) | 0.97 / 0.98 | Reverted. It cost more. It stays a conditional rule: only when you name the tool or the read is large, which was not measured |
| Early compaction on long sessions | -$0.12 on a $2.98 session | 0.85 / 1.00 | Reverted. Off unless `TOKEN_BEGGAR_EARLY=1` |

## Long session

15 log files pasted one at a time until the context passed 300k, then questions about what was seen early and in each phase, exact matches only. 3 runs per setup (`benchmark/results/long`).

| Setup | Cost per session | Peak context | Compactions | Quality |
| --- | --- | --- | --- | --- |
| Without Token Beggar | $2.978 | 306k | 0 | 1.00 |
| Token Beggar, early compaction off | $2.985 | 306k | 0 | 1.00 |
| Token Beggar, early compaction on | $3.102 | 192k | 2 to 3 | 0.85 (0.57 in one run) |

Compacting early cut the peak context from 306k to 192k. Each compaction costs a summary and a re-read, the session cost 4 percent more, and in one run the recalled facts fell to 0.57. So it is opt in. A longer session might tip the other way, but none was measured.

## Models and efforts

`data/measured.json` holds the measured ratio of cost alone over cost with the plugin for each model and effort (`benchmark/results/matrix`). 288 runs in print mode, one per cell and setup, small tasks of each kind. A single cell is noisy. Fable medium and xhigh were not run and use the nearest effort that was, marked `interpolated`.

| Model | low | medium | high | xhigh | max |
| --- | --- | --- | --- | --- | --- |
| Fable 5.1 | full 1.22x | full 1.16x | full 1.16x | full 1.16x | full 1.43x |
| Opus 5.5 | sized 1.02x | sized 1.06x | sized 1.11x | sized 0.99x | full 1.22x |
| Sonnet 5.5 | sized 0.84x | sized 0.89x | sized 0.85x | sized 0.82x | sized 1.06x |
| Haiku 5.5 | off 0.75x | off 0.86x | off 0.83x | off 1.03x | off 0.89x |

The ratios are for small tasks. The Opus high cell is the 84 run benchmark above. For large tasks, the one measured ratio is Opus 5.5 at high effort: 1.42x (1.33 to 1.51), from the hard benchmark, stored under `large` in `data/measured.json`. Sonnet and Haiku were not measured on large tasks. Haiku is off because it is already the cheapest model. Sonnet runs in sized mode, which keeps small tasks inline and sends large ones to one worker, and its large-task saving is unmeasured.

Where the thresholds came from: 1.15x is the run to run spread seen in the repeated runs, so smaller ratios are not claimed. A model whose small-task ratio is at or above 1.15x gets the full card. Anything else gets the sized card, since the hard benchmark showed a saving on large tasks even where small tasks show none. The cheapest model gets nothing, because there is nothing cheaper to send work to.

Spend by kind, pooled over the efforts measured for each model (above 1 means less spend with the plugin):

| Kind | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 | Fable 5.1 |
| --- | --- | --- | --- | --- |
| Multi-file feature | 1.34 | 0.72 | 0.80 | 2.56 |
| Exact edits | 1.04 | 1.15 | 1.01 | 1.36 |
| One function with tests | 1.15 | 1.02 | 0.86 | 1.00 |
| Design | 1.24 | 1.51 | 1.39 | 1.28 |
| Read and answer | 0.92 | 0.95 | 0.76 | 0.91 |
| Review | 0.97 | 1.15 | 1.06 | 1.04 |
| Bug fix | 1.07 | 1.00 | 0.70 | 1.26 |
| Summarise many files | 0.86 | 0.68 | 0.83 | 1.01 |

- Without the plugin, the median task cost about 4.7x as much at max effort as at medium, and 1.5x as much at xhigh. Running `max` for small jobs is the biggest single cost seen, bigger than anything routing can remove.
- The Fable multi-file figure (2.56x) is one cell per effort. It is the strongest number here and the least repeated.
- The spread across efforts inside each pooled ratio is in the data (`cell_min`, `cell_max`).

Reproduce with `matrix.py run|score|fit`. The grid cost about $46.

## Outside tools

With `agy` on the PATH and logged in, three jobs where handing bulk work to an outside tool should cut chat spend: reading every carrier module into one sorted list, a first draft, and a second opinion on a design. 3 runs per setup, Opus 5.5 high. Chat tokens are shown here because the outside tool's own quota is separate from the chat plan (`benchmark/results/agy`).

| Job | Chat tokens without | With Token Beggar | Ratio | Handed to agy | Quality without / with |
| --- | --- | --- | --- | --- | --- |
| Read many files | 59,097 | 61,714 | 0.96x | 3 of 3 | 1.00 / 1.00 |
| First draft | 97,103 | 97,870 | 0.99x | 1 of 3 | 1.00 / 1.00 |
| Second opinion | 38,826 | 42,160 | 0.92x | 0 of 3 | 0.75 / 0.67 |

No saving on these. When the work was handed over, the chat total still came out level with working alone: the files are small, so the dispatch, the brief and the check cost about what reading them would. The gap may open on inputs of hundreds of thousands of tokens. That was not measured, so it is not claimed, and the rule says to use an outside AI only when you name it or the read is large. The Gemini CLI was not logged in on the measuring machine, so Gemini is not measured at all.

## Not measured

- Large tasks on Sonnet, Haiku and Fable. Fable has a full card and a small-task ratio only.
- v0.3.0 on the small tasks (see the top).
- Anything other than Python projects.
- Your own project: workers load your project memory file like any session. The benchmark projects have none, so that cost is not in the numbers.
- Gemini, and large reads sent to an outside tool.
