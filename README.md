<p align="center"><img src="assets/logo.svg" width="120" alt="Token Beggar logo"></p>

# Token Beggar

**Begs every token back. Same answers, less quota and money.**

[English](README.md) | [Traditional Chinese](README.zh-TW.md)

![Token Beggar demo](assets/demo.gif)

I'm a skill for a terminal coding agent with one habit: before the big model does a job, I check whether a cheaper route can do it just as well. The chat model splits your prompt into subtasks and sends each one to the cheapest provider, model and effort that keeps the quality: a small model in a worker, an outside tool's CLI such as `agy`, or itself. Design, root causes and the final answer stay with the model you picked.

I also know when to do nothing. For each model and effort I carry the measured cost with and without me. Where I can't save, I add no card, delegate nothing and print no footer.

```
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

Restart the agent or run `/reload-plugins`, then run `token-beggar doctor` to confirm the hooks run. Needs Python 3.10 or newer, standard library only.

At the end of a reply where I acted and a saving was measured, you get one line:

```
Token Beggar: about 1.3x less quota than Opus 5.5 high alone, saved about $0.06 (est.) | multi-file feature | routed 1: sonnet medium x1
```

The multiple is the measured ratio of list-price spend (the chat plus every worker, cache included) without me over with me, for your model, effort and kind of task. The dollars are the reply's own list-price cost times that ratio minus one. Both are estimates and say so. The line never counts tokens. Under 1.15x it states no multiple, since that's inside the run-to-run spread. If the ratio came from a cell I didn't run, the line says `interpolated`.

## What it saves

The honest result is a small one: 1.11x over a mixed set (about $0.014 a task, 9 percent), and 1.40x on multi-file work, with Opus 5.5 at high effort as the chat model. The interval for the mixed set is 1.08 to 1.14, which sits just under the 1.15x I need to call a saving a claim. On other chat models the picture differs, and on some I do nothing (see "Which models it helps").

How it was measured: 28 small tasks in 7 classes, 3 runs each, 84 runs per arm. 21 tasks are the ones I tuned on. 7 are held out, written after the tuning and never used for it. Three arms with the same prompt, tools, model and effort: the model alone, v0.2.0 (the previous release, commit 9b63cdb), and this release. A fourth arm, the full card, is this release with the full menu forced on at every ceiling. Cost is list-price spend of the chat and every worker. The multiple is alone over arm, with a 95 percent interval.

| Group | Alone | v0.2.0 | Full card | This release | This release vs alone | Quality alone / v0.2.0 / full / this |
| --- | --- | --- | --- | --- | --- | --- |
| All 28 tasks | $0.148 | $0.139 | $0.141 | **$0.134** | 1.11x (1.08 to 1.14) | 0.96 / 0.96 / 0.96 / 0.99 |
| The 21 tuning tasks | $0.153 | $0.140 | $0.141 | **$0.135** | 1.13x (1.09 to 1.16) | 0.95 / 0.96 / 0.95 / 0.98 |
| 7 held-out tasks | $0.134 | $0.136 | $0.142 | **$0.129** | 1.04x (0.99 to 1.11) | 0.98 / 0.99 / 0.98 / 1.00 |
| Mechanical edits | $0.120 | $0.112 | $0.112 | **$0.124** | 0.97x (0.92 to 1.02) | 1.00 / 1.00 / 1.00 / 1.00 |
| Reading and summarising | $0.092 | $0.095 | $0.099 | **$0.091** | 1.00x (0.94 to 1.07) | 0.94 / 0.90 / 0.90 / 0.98 |
| Routine code | $0.152 | $0.149 | $0.149 | **$0.132** | 1.15x (1.09 to 1.22) | 1.00 / 1.00 / 1.00 / 1.00 |
| Multi-file feature | $0.260 | $0.194 | $0.192 | **$0.185** | 1.40x (1.27 to 1.55) | 1.00 / 1.00 / 1.00 / 1.00 |
| Bug root cause | $0.153 | $0.154 | $0.163 | **$0.140** | 1.09x (1.02 to 1.17) | 1.00 / 1.00 / 1.00 / 1.00 |
| Design | $0.114 | $0.116 | $0.125 | **$0.114** | 1.00x (0.94 to 1.06) | 0.94 / 0.94 / 0.92 / 1.00 |
| Code review | $0.144 | $0.153 | $0.149 | **$0.148** | 0.97x (0.91 to 1.04) | 0.83 / 0.92 / 0.88 / 0.92 |

<p align="center"><img src="assets/chart-cost.svg" alt="Times less quota and money than the model alone, by class and arm"><img src="assets/chart-quality.svg" alt="Mean quality per task by class and arm"></p>

Read it plainly:

- This release is cheaper than v0.2.0 on the mixed set ($0.134 against $0.139) with equal or better quality. On the 7 held-out tasks both sit inside the spread of working alone (1.04x and 0.99x), so I can't say either one saves there. The 1.13x on the tuning tasks is what tuning on a set buys. Expect nearer 1.0x to 1.1x on work like the held-out set.
- Only multi-file work (1.40x) and routine code (1.15x) are clear of the noise. Everything else is a saving I can't tell from none.
- On mechanical edits this release is worse than v0.2.0 ($0.124 against $0.112) and no better than working alone. Lean mode sends only multi-file changes to a worker, and the full card did better on edits. I kept the lean card because it won on the mixed set. I didn't find a rule that wins on both.
- Review quality is 0.92 against 0.83 alone. The checklist is short and one item moves the score a lot, and the saving there is under 1.0x, so I don't claim an improvement.
- Speed: 24 seconds a task against 22 alone and 29 for v0.2.0.
- The small savings have one cause I can measure. Every invocation of the agent pays a fixed start cost of about $0.10, which is most of a $0.15 task. The saving grows with task size.
- I don't know why routine code (1.15x) and bug root cause (1.09x) gained. The lean card doesn't route those kinds, so I read them as run-to-run variation until a larger run says otherwise.

### The levers

Five changes aimed at cutting spend were each tested alone: remove one from the full card and compare, 16 tasks, 3 runs each. A lever stays only if quality is within the spread, and the one item of difference in the quality column (0.97 against 0.98) is inside it. The saving column is the cost of removing the lever, so a plus sign means the lever saves that much.

| Lever | Cost of removing it, per task | Quality with / without | Verdict |
| --- | --- | --- | --- |
| Lean worker (six tools instead of all of them) | +$0.011 (0.93x, 0.88 to 0.97) | 0.97 / 0.98 | Kept. The one lever with a saving clear of the noise |
| Batch dispatch (one worker for related jobs) | +$0.005 (0.97x, 0.93 to 1.01) | 0.97 / 0.98 | Kept. Quality holds, but the saving is inside the noise |
| Shorter output (short reports from workers, short answers) | +$0.003 (0.98x, 0.95 to 1.01) | 0.97 / 0.98 | Kept. Quality holds, but the saving is inside the noise |
| Bulk reading to `agy` | -$0.007 (1.05x, 1.02 to 1.09) | 0.97 / 0.98 | Reverted. It cost more. It stays a conditional rule: only when you name the tool or the read is about 100k tokens or more, which I did not measure |
| Early compaction on long sessions | -$0.12 on a $2.98 session, see below | 0.85 / 1.00 | Reverted. Off unless `TOKEN_BEGGAR_EARLY=1` |

For early compaction I ran a long session: 15 log files pasted one at a time until the context passed 300k, then questions about what was seen early and in each phase, exact matches only. Three runs per arm.

| Arm | Cost per session | Peak context | Compactions | Quality |
| --- | --- | --- | --- | --- |
| Alone | $2.978 | 306k | 0 | 1.00 |
| Skill, early suggestion off | $2.985 | 306k | 0 | 1.00 |
| Skill, early suggestion on | $3.102 | 192k | 2 to 3 | 0.85 (0.57 in one run) |

Compacting early did cut the peak context from 306k to 192k. But each compaction costs a summary and a re-read, the session cost 4 percent more, and in one run the recalled facts fell to 0.57. That isn't the saving I expected, so it's opt in. A longer session than this one might tip the other way, and I haven't measured one.

### Which models it helps

`data/measured.json` holds the measured ratio of spend alone over spend with me, for every model and effort I ran. What the skill does follows from it:

- `full` (ratio at or above 1.15): the whole menu, the reminder and the footer.
- `lean` (0.95 up to 1.15, and multi-file work measured to win): a one-line card that sends changes to three or more files to one worker, and a footer only for that kind.
- `off` (anything lower): no card, no delegation, no footer.

`token-beggar mode --all` prints the grid. `TOKEN_BEGGAR_MODE=full|lean|off` forces a mode. A model I haven't measured gets `full`.

| Model | low | medium | high | xhigh | max |
| --- | --- | --- | --- | --- | --- |
| Fable 5.1 | full 1.22x | full 1.16x | full 1.16x | full 1.16x | full 1.43x |
| Opus 5.5 | lean 1.02x | lean 1.06x | lean 1.11x | lean 0.99x | full 1.22x |
| Sonnet 5.5 | off 0.84x | off 0.89x | off 0.85x | off 0.82x | off 1.06x |
| Haiku 5.5 | off 0.75x | off 0.86x | off 0.83x | off 1.03x | off 0.89x |

So I help on Fable at any effort, and on Opus at max. On Opus at the other efforts I do little, and what I do is multi-file work. On Sonnet and Haiku I stand down, because a worker's start cost is larger than what a cheaper model saves on a task that's already cheap. Each cell is one small task per kind, run once alone and once with me, so a single cell is noisy. The Opus high cell is the exception, since it's the 84-run benchmark above. The matrix cells for Fable medium and xhigh weren't run. They take the nearest effort that was and say `interpolated`. The one deviation from the 1.15x rule is the 0.95x floor for lean. Below it, I stand down.

Spend by kind, pooled over the efforts measured for each model (ratio above 1 means less spend with me):

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

This is 288 runs in print mode, one per cell and arm. Things to know before you lean on a number:

- Without me, the median task cost about 4.7x as much at max effort as at medium, and 1.5x as much at xhigh. Running `max` for small jobs is the biggest single cost I saw, bigger than anything I can route away.
- The Fable multi-file figure (2.56x) is one cell per effort. It's the strongest number in the repository and the least repeated.
- The spread across efforts inside each pooled ratio is in the data (`cell_min`, `cell_max`).

### Outside tools

With `agy` on the PATH and logged in, I measured three jobs where handing bulk work to an outside tool should cut chat spend: reading every carrier module into one sorted list, a first draft, and a second opinion on a design. 3 runs per arm, Opus 5.5 high. Chat tokens are shown here because the outside tool's own quota is separate from your chat plan.

| Job | Chat tokens alone | With the skill | Ratio | Handed to agy | Quality alone / with |
| --- | --- | --- | --- | --- | --- |
| Read many files | 59,097 | 61,714 | 0.96x | 3 of 3 | 1.00 / 1.00 |
| First draft | 97,103 | 97,870 | 0.99x | 1 of 3 | 1.00 / 1.00 |
| Second opinion | 38,826 | 42,160 | 0.92x | 0 of 3 | 0.75 / 0.67 |

No saving on these. When the work was handed over (the reading job, every run), the chat total still came out level with working alone. The files are small, so the chat model pays for the dispatch, the brief and the check about as much as it would pay to read them. Behind that is the same fixed start cost of about $0.10. I expect the gap to open on inputs of hundreds of thousands of tokens, but I haven't measured it, so I don't claim it. That's why the rule now says to use an outside AI when you name it or the read is large, and otherwise stay inline. The Gemini CLI wasn't logged in on the machine I measured on, so Gemini isn't measured at all.

### How it was measured

- A small Python shop project. 28 tasks: 4 each for mechanical edits, reading, routine code, multi-file features, debugging, design and review, 3 of each in the tuning set and 1 of each held out.
- Same prompt, same allowed tools, same chat model and effort in every arm.
- Code tasks are scored by a hidden check plus the project tests. Answer tasks are scored against a checklist by a blind judge that doesn't see which arm wrote the text.
- Cost is the list-price total of the chat and every subagent, from the agent's own JSON (`modelUsage`), cache included. An outside tool's tokens are counted apart.
- Intervals are 95 percent, from a bootstrap over the runs of each task (2000 resamples). A saving is claimed only at 1.15x or more with the whole interval above 1.0x, because the run-to-run spread I saw was about that large.
- Raw runs: [`benchmark/results/final/raw`](benchmark/results/final/raw) (this table and the levers), [`long`](benchmark/results/long) (the long session), [`matrix/raw`](benchmark/results/matrix/raw) (the model and effort grid), [`agy/raw`](benchmark/results/agy/raw) (outside AIs). Tables: [`final/report.md`](benchmark/results/final/report.md) and [`levers/report.md`](benchmark/results/levers/report.md).
- Reproduce: `python3 benchmark/run.py --arms alone,v020,fullcard,final`, then `score.py` and `report.py --out final --arms alone,v020,fullcard,final`. The grid is `matrix.py run|score|fit`, the long session is `long_session.py` and the outside tool jobs are `agy_bench.py`. The final benchmark with its lever arms cost about $74 in list price, the grid about $46 and the long session about $27. Codex is never called by the benchmarks.

## Install

To try it for one session without installing, clone the repository and start the agent with `--plugin-dir ./Token-Beggar`.

<details>
<summary>Other hosts</summary>

The routing card, the worker and the hooks use features of the host above, so the plugin doesn't run in other agents. Two things do work. On a supported host, `agy`, `gemini` and `codex` are routing targets when they're installed. And `skills/token-beggar/SKILL.md` is plain Markdown you can copy into any agent that reads skills.
</details>

<details>
<summary>Turn it off</summary>

Start the agent with `TOKEN_BEGGAR=off` in its environment for one shell. Create a file named `off` in the state directory (`token-beggar env` prints it) for good. `/plugin uninstall token-beggar` removes it.
</details>

Details in [docs/install.md](docs/install.md).

## How I work

1. **Check the ceiling and the measured ratio.** From the chat's model and effort I look up the mode above. In `off` that's the end of it.
2. **Decompose.** In `full`, a hook adds a menu to the first real prompt of a session and a one line reminder after it. The menu lists every provider, model and effort you can use, with what each is good and weak at, a capability score and a price. In `lean` the card is one line. Very short prompts and slash commands get nothing. The chat model splits the prompt into subtasks.
3. **Choose per subtask.** Decision rules ask about size, ambiguity, risk, how much has to be read, and whether a test can verify the result. The cheapest combination that clears the bar wins. A one line answer or a short edit stays inline, since a worker starts with its own base context.
4. **Respect the ceiling.** The model and effort of your chat are the cap for models of the same vendor. If you run Sonnet at medium, nothing goes to Opus or to high effort. Other providers aren't capped unless you say so in the prompt: "agy max flash" keeps agy to its flash models and "no gemini" switches it off for the session.
5. **Check cheaply.** One test run or `git diff --stat`, not a second read of everything. Judgement and the final answer stay with the chat model.
6. **Report.** The Stop hook adds the footer above. The model doesn't write it. The hook counts the transcript, so the number can't be made up in prose.

Say `/token-beggar` or "token beggar" to switch me on for a prompt that didn't trigger me on its own.

### Outside tools as routes

`agy`, `gemini` and `codex` on the PATH, and MCP servers, appear on the menu. `token-beggar inventory` lists them and detects each tool's models (`agy models`). The prior is the host's own models first, then Codex, then Gemini. Bulk and first draft work can go out. Anything that needs this conversation, edits files or is risky can't. I never send secrets, and file names and text that look like keys are refused.

```
token-beggar ask agy --model gemini-3.8-flash-low --file 'src/**/*.py' "list every public function with its arguments"
token-beggar cap agy flash
```

`--file` takes globs and directories. When a tool answers with a usage limit I parse the error for the reset time and keep that tool (or that model) off the menu until then. If the text names no time, it's five hours for a quota and a day for a login problem. A chat vendor model that runs out is handled the same way (`token-beggar exhausted <alias>`). An outside answer is a draft. The chat model reads it before using it.

### Compaction

Works with no setup, in every mode. The host compacts at a point derived from the context window, 33k tokens short of it by default. I find that point myself (`token-beggar window` prints it), so you don't need to set the compaction window variable. If you do set it, or the percent override, it's yours and I never move it.

- **Check often.** On every prompt and after every tool call in a long turn.
- **Warn early.** At 87.5 percent of the point, or 30k tokens before it, whichever comes first, I ask the chat model to judge whether it's in the middle of a step (edits unverified, a change half done across files, a plan in progress) and to save a note with `token-beggar note`, a few lines on the goal, what is done and what is next. A mechanical extract (the request, edited files, the last commands) is the fallback if the model doesn't.
- **Defer a mid-step compaction.** Exit code 2 from the `PreCompact` hook postpones an automatic compaction. I do it up to 3 times by 5 percent of the window each, never closer than 5k tokens to the level where the host refuses requests, and only when the note says mid-step. A manual `/compact` is never blocked.
- **Read it back.** After a compaction the session start hook puts the note back with the menu. A note written long before the compaction is labelled as old.
- **Why not move the point.** The host reads its window only when it starts, and I write no settings, so I can't choose the point from inside a session. I can choose a moment to suggest `/compact`, and that suggestion is off by default for the reason in the levers section.

Tested in real sessions in print mode and a 100k window on 8 long documents read one by one: the warning arrived at 47k and 63k of a 67k point, the model wrote the note mid-step, two compactions were deferred, the host compacted once at 95k, and afterwards the model carried on from the note and listed all eight first words correctly. Limits: edits made inside a worker are invisible to me, so I neither defer for them nor list them. One tool result bigger than the margin before the point can jump past it. The host clamps the window to 100k to 1M. See [docs/architecture.md](docs/architecture.md).

### Check it and see what it did

`token-beggar doctor` lists what can quietly stop routing: an unsupported Python, an unwritable state directory, a worker model forced by the environment, logged hook errors, and whether the hook entry point runs. It exits 1 when something is broken.

`token-beggar stats` reads your own recent sessions (7 days by default, `--days N` to change it). Per worker model it prints how many workers ran, what they cost, and what the same work would have cost at the model that started them. That last column is an upper bound on what delegation moved, not a net saving.

### Models

`data/models.json` lists the model families with price and default effort. A GitHub Action refreshes it every week from the vendor's public models page, and a local weekly check does the same for installed copies. `data/profiles.json` holds the capability and cost profiles and the decision rules the menu is built from.

## Similar tools

I looked at these before building this and kept what they do well. The differences are facts, not a ranking.

| Tool | What it does | How I differ |
| --- | --- | --- |
| Local router proxies (for example the musistudio project) | A proxy that sends the agent's requests to other providers by scenario | I don't touch the API path. I route inside the session with the agent's own subagents, and keep the chat model as a cap |
| The subagent model variable and `model:` in agent files | Pin one model to subagents | Static: it doesn't grade the task or the ceiling, and it can't choose effort per call |
| ccusage style meters | Report spend after the fact | I act before the spend, and my multiplier comes from a benchmark rather than from your history |
| Token saving guides and context skills | Shorter prompts, smaller context, fewer reads | Compatible with me. I only change who does the work |

If I missed one, open an issue.

## Limits

- Savings on small tasks are small because of the worker start cost. Under about 1.15x I can't tell it from none, and the mixed-set result (1.11x) is under it.
- The release comparison covers one project and one chat model and effort (Opus 5.5, high). The grid covers four models and five efforts, one run per cell, so a single cell is noisy and some Fable cells are interpolated.
- On the held-out tasks I measured 1.04x. Treat the tuning-set figures as an upper bound.
- On Sonnet and Haiku, and on Opus below max except for multi-file work, I do nothing, because that's what the measurements support.
- On mechanical edits this release is no better than working alone and worse than v0.2.0.
- No saving from another AI is shown on the small files I tested, and the Gemini CLI wasn't measured. Large reads are unmeasured.
- Early compaction was tested on one long session design and did not pay, so it's opt in.
- The footer is estimated from a ratio. The dollar figure is real list-price cost times a measured ratio, and the ratio isn't a measurement of your task. When the host runs the Stop hook before the last message is written I wait up to 4 seconds for it, and print "at least" if it still isn't there.
- Hooks can't see the chat model, so the model is read from the transcript first, then the launch flags of the running agent process, the environment and settings. If none says which model runs, the card says the ceiling is unknown and tells me never to go above my own model.
- Workers load your project memory file like any session. The benchmark project has none, so that cost isn't in the numbers.
- A task graded by a model can be graded wrong. The checks in the benchmark are there to catch that, and they can't remove it.

More in [docs/usage.md](docs/usage.md), [docs/config.md](docs/config.md) and [docs/architecture.md](docs/architecture.md). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). MIT license.

Assisted by Claude/Codex.
