# Token Beggar 🪙: same answers, a smaller bill

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: same answers, a smaller bill. Sends each task to the cheapest model that still does it right." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="Release"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Zero dependencies"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="License"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar is a plugin for Claude Code. Before the big model does a job, it checks whether a cheaper model can do it just as well. Small tasks stay in the chat. A large task, such as fixing a bug in a repository you have not read yet, goes to one cheaper worker, and the chat then checks the whole diff and runs the tests. Design, root causes and the final answer stay with the model you picked.

**On 18 real bug fixes it cost 1.42x less quota and money than working alone, with the same share of hidden tests passing (69% against 70%).**

It runs on your machine, in your Claude Code session. It uses the Claude Code you are already signed in to, sends nothing about you anywhere, and writes only to its own folder. [Exactly what it does](docs/on-your-machine.md).

[Install](#install) · [Quick start](#quick-start) · [Results](#results) · [How it works](#how-it-works) · [FAQ](#faq) · [Docs](#documentation) · [Changelog](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> Not sure it is working? Run `token-beggar doctor`. It lists what can quietly stop routing and exits 1 when something is broken.

## Install

Needs Claude Code and Python 3.10 or newer. It uses the standard library only.

```
# From the marketplace in this repository (inside Claude Code)
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

```
# Try it for one session without installing
git clone https://github.com/Arthur031221/Token-Beggar
claude --plugin-dir ./Token-Beggar
```

```
# From a shell, the same two steps as the first block
claude plugin marketplace add Arthur031221/Token-Beggar
claude plugin install token-beggar@token-beggar
```

Restart the agent or run `/reload-plugins`. More in [docs/install.md](docs/install.md), including how to use the skill in another agent that reads skills.

## Quick start

Work as you always do. On the first real prompt of a session a hook adds a short routing card, and the chat model sizes the task. At the end of a reply where something was routed and a saving was measured, you get one line:

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

The multiple is the measured ratio of list price cost without Token Beggar over with it, for your model and effort. The dollars are the reply's own cost times that ratio minus one. Both are estimates and say so. The line never counts tokens, and under 1.15x it states no multiple, because that is inside the run to run spread.

To switch it on for a prompt that did not trigger it, say `/token-beggar`. Then confirm the hooks run:

```
token-beggar doctor
```

## Results

Two setups, and only two. **Without Token Beggar** is the chat model working alone, the way you use it normally. **With Token Beggar** is the card shipped in this release, version 0.3.0. Opus 5.5 at high effort is the chat model. Cost is list price for the chat and every worker, cache included. Intervals are 95 percent.

Hard tasks are 18 merged pull requests from 12 open source Python projects (Django, Sphinx, pylint, sympy, click and others). The chat starts from the commit before the fix with the issue text, and is scored by the tests the maintainers added, which it never sees. 3 runs per task, 54 per setup.

| Setup | Cost per task | Multiple | Issues resolved |
| --- | --- | --- | --- |
| Without Token Beggar | $0.69 | 1.00x | 70% |
| With Token Beggar | $0.49 | 1.42x less (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="Bar chart: times less quota and money with Token Beggar than without it, per hard task. All tasks: 1.42x. A dashed line marks 1.0x, the cost without Token Beggar."></p>

<p align="center"><em>17 of the 18 tasks cost less with Token Beggar. The one that cost more (structlog-exception-outside) cost about 10% more.</em></p>

Cost is down by 29 percent and the share of issues resolved is level (69% against 70% is a tie within the spread). Time is level too (168 seconds against 187), not faster.

Small tasks were measured only with an earlier card, not with 0.3.0. They saved little there (1.11x, under the 1.15x line at which a saving is claimed), and they stay in the chat, so expect close to no change on small one-file edits.

Full benchmark details, the task list and how to reproduce everything: [docs/benchmark.md](docs/benchmark.md). Every raw run is in [`benchmark/results`](benchmark/results).

> [!IMPORTANT]
> **Where it helps and where it does not.** It helps on large tasks with Opus 5.5 at high effort (1.42x, measured), and on every effort of Fable 5.1 and Opus at max, where small tasks measure a saving too. On Opus at other efforts and on Sonnet 5.5 it keeps small tasks in the chat and sends large ones to a worker. The large task saving is measured for Opus high only, so on Sonnet it is unmeasured and the footer then states the cost without a multiple. On Haiku 5.5, the cheapest model, it does nothing. If you mostly run small one-file edits, expect close to no change.

## How it works

1. **Look up the mode.** The model and effort of your chat select one of three modes from `data/measured.json`. `full` (the whole menu of models, efforts and outside tools) where small tasks measured a saving of 1.15x or more, or the model was never measured. `sized` everywhere else. `off` for the cheapest model. `token-beggar mode --all` prints the grid, and `TOKEN_BEGGAR_MODE=full|sized|off` forces one.
2. **Size the task.** In `sized` mode the card says small means do it in the chat, and large means send one worker the whole reproduce, explore, fix and run the tests list. Large means an issue in a repository the model has not read, more than about 5 tool calls, more than one file, or an edit and test loop. A small task that grows past about 5 steps becomes large.
3. **Check the worker's work.** The worker reports in under 150 words and lists every site that shares the symptom. The chat reads the whole `git diff`, runs the tests, checks that list, and sends the same worker back if something is missing.
4. **Respect the ceiling.** The model and effort of your chat cap what the same vendor's models get. On Sonnet medium, nothing goes to Opus or to high effort.
5. **Report.** The Stop hook adds the footer. The model does not write it, so the number cannot be made up in prose.

Where the thresholds came from: 1.15x is about the run to run spread seen in repeated runs, so a smaller ratio is not called a saving. The large task ratio of 1.42x is the hard benchmark above. Details in [docs/benchmark.md](docs/benchmark.md#models-and-efforts).

### How it fits together

- **Skill**: the routing rules the chat reads. [`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md), explained in [docs/usage.md](docs/usage.md).
- **Hooks**: seven small hooks that add the card, hold workers to the ceiling, guard compaction and add the footer. [docs/on-your-machine.md](docs/on-your-machine.md).
- **Worker**: one agent with six tools that does the delegated job. [`agents/beggar-worker.md`](agents/beggar-worker.md), see [docs/architecture.md](docs/architecture.md).
- **CLI**: `token-beggar` for `doctor`, `mode`, `stats`, `inventory`, `ask` and more. [docs/usage.md](docs/usage.md#commands).

It also guards long sessions. It finds the point where the host compacts the context, asks the chat to save a short note before it, can postpone an automatic compaction in the middle of a step, and puts the note back afterwards. See [docs/architecture.md](docs/architecture.md).

## What it does on your machine

> [!NOTE]
> Everything below is also in [docs/on-your-machine.md](docs/on-your-machine.md), with the hook table.

- **Reads**: the transcript of the current session (to count cost and find the context size and the model), the launch flags of the chat process through `ps`, and the environment and settings files for the model and effort. None of it leaves your machine.
- **Runs**: seven hooks that call `python3 -m token_beggar hook <name>`. A hook that fails logs the error and exits 0, so it never breaks your session. Workers run under your own permission settings.
- **Sends**: one weekly download of the vendor's public models page, to keep prices current (`TOKEN_BEGGAR_OFFLINE=1` stops it). Text goes to an outside AI tool (`agy`, `gemini`, `codex`) only if you have it installed and you name it or a read is about 100k tokens or more. File names and text that look like keys are refused.
- **Writes**: one folder, `~/.claude/token-beggar`. No agent settings, no files in your project.
- **Turn it off**: `TOKEN_BEGGAR=off` for one shell, a file named `off` in that folder for good, or `/plugin uninstall token-beggar`.

## Configuration

You do not need any. The defaults come from the measurements.

| Setting | What it does |
| --- | --- |
| `TOKEN_BEGGAR=off` | Off for this shell |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | Force a mode instead of the measured one |
| `TOKEN_BEGGAR_EARLY=1` | Suggest early compaction on long sessions (measured to cost more, so off) |
| `TOKEN_BEGGAR_OFFLINE=1` | No weekly download |
| `token-beggar cap agy flash` | Keep an outside tool to its flash models |

All of it, including prompts such as "no gemini": [docs/config.md](docs/config.md).

## Limits

- Small tasks save little. Under about 1.15x it cannot be told from none, and the small task result from the earlier card (1.11x) is under it.
- The hard benchmark covers one chat model and effort (Opus 5.5, high) and Python projects. Sonnet, Haiku and Fable on large tasks are not measured.
- 69% against 70% resolved is a tie within the spread, and a blind review by a small model rated the v0.3.0 diffs lower than working alone (0.94 against 1.33 on a 0 to 2 scale), though it agrees only weakly with the tests, so it is not shown that the code is as good.
- v0.3.0 was not re-run on the small tasks.
- No saving from outside AI tools was found on small files, and Gemini was not measured. Large reads are unmeasured.
- Early compaction cost more in the one long session tested, so it is opt in.
- The footer is estimated from a measured ratio, not from your task. Hooks cannot see the chat model, so it is read from the transcript, then the process flags, the environment and settings. If none says, the card says the ceiling is unknown.
- Workers load your project memory file like any session. The benchmark projects have none, so that cost is not in the numbers.

## FAQ

**Does it change my answers?** On the hard tasks it fixed 69% of issues against 70% alone, a tie within the spread. It does not claim the code is of equal quality.

**Why no footer sometimes?** It prints one only when it routed something and a saving of 1.15x or more was measured for your model, effort and kind of task.

**Does it do anything on Sonnet or Haiku?** On Haiku nothing, because it is the cheapest model and there is nothing cheaper to send work to. On Sonnet small tasks measured a loss (about 0.85x), so they stay in the chat, and large tasks go to a worker, but the saving on large tasks was not measured.

**Does it use my quota?** The worker spends your normal Claude quota at a cheaper model. Outside AI tools spend their own quota and none of yours.

**Is anything sent to a server?** Only the weekly models page download, which carries no data about you, and files you hand to an outside tool you named. See [what it does on your machine](#what-it-does-on-your-machine).

**Which other tools are like it?** Router proxies send API requests to other providers by scenario, the subagent model variable pins one model to subagents, and meters such as ccusage report spend afterwards. Token Beggar works inside the session, grades the task and the ceiling, and its multiple comes from a benchmark, not your history. It combines with shorter prompts and smaller contexts. If a tool is missing here, open an issue.

## Documentation

| Goal | Start here |
| --- | --- |
| Install it, or try it for one session | [docs/install.md](docs/install.md) |
| Learn what it routes and the commands | [docs/usage.md](docs/usage.md) |
| See what it does on your machine | [docs/on-your-machine.md](docs/on-your-machine.md) |
| Change a setting or a rule | [docs/config.md](docs/config.md) |
| Understand the parts and the modes | [docs/architecture.md](docs/architecture.md) |
| Check the numbers or reproduce them | [docs/benchmark.md](docs/benchmark.md) |
| See what changed | [CHANGELOG.md](CHANGELOG.md) |

## Development

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## Contributing

Issues and pull requests are welcome. A change to the card, the skill or `data/profiles.json` needs a benchmark run before and after, with losses reported next to wins. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © Arthur031221

Assisted by Claude/Codex.
