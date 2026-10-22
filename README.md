<p align="center"><img src="assets/logo.svg" width="120" alt="Token Beggar logo"></p>

# Token Beggar

**Begs every token back. Same answers, a fraction of the bill.**

[English](README.md) | [Traditional Chinese](README.zh-TW.md)

![Token Beggar demo](assets/demo.gif)

I'm a skill for a terminal coding agent with one habit: before the big model does a job, I check whether a cheaper one can do it just as well. Reading logs, renaming things and running test loops go to a small model in a worker. Design and root causes stay with the model you picked.

```
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

Restart the agent or run `/reload-plugins`, then run `token-beggar doctor` to confirm the hooks run. Needs Python 3.10 or newer, standard library only.

## What it saves

Measured on 21 tasks in 7 classes, 3 runs each, with and without me. The chat model was Opus 5.5 at high effort. Cost is list price from the agent's own usage report.

| Class | Without | With | Cheaper | Quality without / with |
| --- | --- | --- | --- | --- |
| Multi-file feature | $2.47 | $1.58 | **1.56x** | 1.00 / 1.00 |
| Mechanical edits | $1.11 | $0.80 | **1.4x** | 1.00 / 1.00 |
| Reading and summarising | $0.91 | $0.75 | 1.21x | 0.89 / 0.86 |
| Design | $0.93 | $0.82 | 1.14x | 1.00 / 1.00 |
| Routine code | $1.47 | $1.32 | 1.12x | 1.00 / 1.00 |
| Bug root cause | $1.45 | $1.29 | 1.12x | 1.00 / 1.00 |
| Code review | $1.21 | $1.13 | 1.07x | 0.83 / 0.87 |
| **All 63 runs per arm** | **$9.56** | **$7.69** | **1.24x** | **0.96 / 0.96** |

The headline is 1.56x on multi-file work and 1.24x over a mixed day. It's not 10x. The tasks are small and every worker pays a fixed cost to start, so the saving grows with task size.

Read the small numbers with care. Design, bug root cause and review never go to a worker, yet they came out 1.07x to 1.14x cheaper. That's run to run variation, plus a shorter path the routing card seems to give the chat model. So I treat anything under about 1.15x as indistinguishable from no saving. Three classes clear that bar: multi-file work, mechanical edits and reading. Reading comes with a small quality dip, noted below.

I'm a beggar, not a magician. Where a cheaper model doesn't hold quality, I stay out. Review went to a worker in my first pass and came out at 0.86x, so it now stays inline. Reading still goes to a worker and quality was 0.86 against 0.89, one checklist item on average. That's inside the judge's noise, but it doesn't prove there's no loss. The routes were tuned on these same 21 tasks, so the table measures this setup. It doesn't forecast yours.

<p align="center"><img src="assets/chart-cost.svg" alt="Mean cost per task by class"><img src="assets/chart-quality.svg" alt="Mean quality per task by class"></p>

### How it was measured

- 21 tasks on a small Python shop project: 3 each for mechanical edits, reading, routine code, multi-file features, debugging, design and review.
- Two arms per task, same prompt, same allowed tools, same chat model (Opus 5.5, high effort). One arm has the plugin, one doesn't.
- Code tasks are scored by a hidden check plus the project tests. Answer tasks are scored against a checklist by a blind judge that doesn't see which arm produced the text.
- Cost and token counts come from the agent's JSON output in print mode. Raw runs are in [`benchmark/results/raw`](benchmark/results/raw), scores in [`scores.json`](benchmark/results/scores.json), the table in [`report.md`](benchmark/results/report.md).
- Reproduce it with `python3 benchmark/run.py && python3 benchmark/score.py && python3 benchmark/report.py`. A full pass costs about $18 in list price.

## Install

To try it for one session without installing, clone the repository and start the agent with `--plugin-dir ./Token-Beggar`.

<details>
<summary>Other hosts</summary>

The routing card, the worker and the hooks use features of the host above, so the plugin doesn't run in other agents. Two things do work. On a supported host, `codex`, `agy` and `gemini` are used as extra workers when they're installed. And `skills/token-beggar/SKILL.md` is plain Markdown you can copy into any agent that reads skills.
</details>

<details>
<summary>Turn it off</summary>

Start the agent with `TOKEN_BEGGAR=off` in its environment for one shell. Create a file named `off` in the state directory (`token-beggar env` prints it) for good. `/plugin uninstall token-beggar` removes it.
</details>

Details in [docs/install.md](docs/install.md).

## How I work

1. **Grade.** A hook adds a card with the 7 class table to the first real prompt of a session, and a one line reminder to the prompts after it. Very short prompts and slash commands get nothing. I grade the task before reading any code.
2. **Respect the ceiling.** The model and effort of your chat are the cap for models of the same vendor. If you run Sonnet at medium, I never send work to Opus or to high effort. Other providers aren't capped unless you say so, for example "agy max flash".
3. **Delegate only when it pays.** Many tool calls or large reads go to a worker with its own context. Short answers, design and the final word stay inline.
4. **Check cheaply.** One test run or `git diff --stat`, not a second read of everything.
5. **Report.** After a delegated reply I add one line, such as `Token Beggar: about 1.56x less spend than the top model at high effort alone (measured, multi_file)`. The multiplier comes only from the benchmark table above, only for classes at 1.15x or more, and only when your model and effort match the ones I was measured on. Otherwise the line states no number.

Say `/token-beggar` or "token beggar" to switch me on for a prompt that didn't trigger me on its own.

### Check it and see what it did

`token-beggar doctor` lists what can quietly stop routing: an unsupported Python, an unwritable state directory, a worker model forced by the environment, an unset compaction window, logged hook errors, and whether the hook entry point runs. It exits 1 when something is broken.

`token-beggar stats` reads your own recent sessions (7 days by default, `--days N` to change it). Per worker model it prints how many workers ran, the tokens they used, what that cost, and what the same tokens would have cost at the model that started them. The last column is an upper bound on what delegation moved, not a net saving, because the chat model wouldn't have used identical tokens. The measured net saving is still the table above.

### Models

`data/models.json` lists the model families by newest version with price and default effort. A GitHub Action refreshes it every week from the vendor's public models page, and a local weekly check does the same for installed copies. When a worker call fails with a usage limit, `token-beggar exhausted <alias>` marks that model so routing skips it for a few hours. The card also lists `codex`, `agy` and `gemini` when they're on your PATH.

### Compaction

When the conversation nears the compaction point I warn you. If you're in the middle of a step, I defer the compaction up to 3 times and ask you to finish the step and run the tests. Before any compaction I write a note with the goal, edited files and open steps to the state directory, and a session start hook reads it back afterwards.

The warning and the deferral need the host's compaction window variable to be set (`token-beggar env` names it), because I won't guess your model's window. Without it I only write the note. Edits made inside a worker are invisible to me, so I don't defer for them and they don't show up in the note. I can't change when the host compacts beyond deferring it, and the setting has a floor, so very small windows never trigger compaction. I tested 60k and 100k. See [docs/architecture.md](docs/architecture.md).

## Similar tools

I looked at these before building this and kept what they do well. The differences are factual, not a ranking.

| Tool | What it does | How I differ |
| --- | --- | --- |
| Local router proxies (for example the musistudio project) | A proxy that sends the agent's requests to other providers by scenario | I don't touch the API path. I route inside the session with the agent's own subagents, and keep the chat model as a cap |
| The subagent model variable and `model:` in agent files | Pin one model to subagents | Static: it doesn't grade the task or the ceiling, and it can't choose effort per call |
| ccusage style meters | Report spend after the fact | I act before the spend, and my multiplier comes from a benchmark rather than from your history |
| Token saving guides and context skills | Shorter prompts, smaller context, fewer reads | Compatible with me. I only change who does the work |

If I missed one, open an issue.

## Limits

- Savings on tasks under about $0.15 are small because of the worker start cost.
- The benchmark covers one project, one chat model and one effort. Other setups use a card without a measured number.
- Hooks can't see the chat model, so the model is read from the transcript first, then the launch flags of the running agent process, the environment and settings. Effort comes from the same flags, the environment and settings. If none says which model runs, the card says the ceiling is unknown and tells me never to go above my own model.
- Workers load your project memory file like any session. The benchmark project has none, so that cost isn't in the numbers.
- Each task ran 3 times per arm. Differences under about 15 percent are within the run to run spread I saw.
- One scoring bug turned up late: a stale bytecode file made a correct fix look broken in 5 of 6 runs of one debugging task. The scorer now clears bytecode before checking, and both arms were rescored.
- A task graded by a model can be graded wrong. The checks in the benchmark are there to catch that, not to remove it.

More in [docs/usage.md](docs/usage.md), [docs/config.md](docs/config.md) and [docs/architecture.md](docs/architecture.md). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). MIT license.

Assisted by Claude/Codex.
