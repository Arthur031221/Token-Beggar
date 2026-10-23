# Architecture

```
prompt -> UserPromptSubmit hook -> menu + decision rules in context
                                      |
        chat model splits the prompt into subtasks, picks provider + model + effort for each
                                      |
     inline  |  beggar-worker (Agent tool, model and effort per call)  |  token-beggar ask <tool>
                                      |
                  model checks with one command and answers
                                      |
                  Stop hook prices the reply and writes the footer
```

The host agent gives a plugin hooks, skills and agents but no hook that can change the model of the chat itself. So Token Beggar works through the levers that exist: the Agent tool takes a `model` and an `effort` on every call, and a shell command can call another tool's CLI.

There is no routing table. `data/profiles.json` holds a capability score and a price for every host model, a profile of what each external tool is good and weak at, and the decision rules (size, ambiguity, risk, how much has to be read, whether a test can verify the result). `card.py` renders the combinations that are available right now into the menu, and the chat model does the choosing. The v0.1 fixed table is kept in the benchmark as an arm so the two can be compared.

## Parts

| Path | Role |
| --- | --- |
| `hooks/hooks.json` | wires prompt, tool, stop, compaction and session start events to `python3 -m token_beggar hook <event>` |
| `token_beggar/ceiling.py` | finds the chat's model and effort: transcript, then launch flags, then environment, then settings |
| `token_beggar/profiles.py` | loads `data/profiles.json` and lists the combinations allowed under the ceiling and the user's caps |
| `token_beggar/card.py` | builds the text the model sees |
| `token_beggar/external.py` | calls `agy`, `gemini` and `codex` headless, expands `--file` globs, refuses secrets, applies caps, reads quota errors |
| `token_beggar/inventory.py` | models denied by settings, CLI tools and MCP servers found, quota marks |
| `token_beggar/usage.py`, `footer.py` | cost tally of a reply (main chain plus each subagent transcript, each at its model's list price) and the footer line |
| `token_beggar/compact.py`, `handoff.py`, `transcript.py` | the compaction guard |
| `token_beggar/update.py` | parses the vendor's public models page into `models.json` |
| `skills/token-beggar/SKILL.md` | the rules and the rubric |
| `agents/beggar-worker.md` | the worker |
| `benchmark/` | the runner, the tasks, the footer matrix, the outside tool jobs and the raw results |

## Finding the ceiling

A hook does not receive the model or the effort. Token Beggar reads them from the best source that has them:

1. the model of the last main-chain assistant message in the transcript,
2. the `--model` and `--effort` flags of the agent process that started the hook,
3. the model and effort environment variables (`token-beggar env` lists them),
4. `model` and `effortLevel` in `settings.json`.

If none of them names a known model, the card says so and tells the model to treat itself as the ceiling.

## Footer

The Stop hook reads the transcript of the reply that just ended. The count is the main chain's messages (each message id once, because the transcript logs one line per content block) plus every subagent's own transcript under `<session>/subagents/`, input + output + cache read + cache write. It matches the `modelUsage` the agent reports in print mode. Tokens from `token-beggar ask` come from a per session ledger and are shown apart.

The ratio comes from `data/measured.json`: the pooled ratio of the chat model and the kind of task (edit, read, bulk read, function, feature, bug fix, review, design, chosen by rules on the prompt and the edits made). Below 1.15 the footer doesn't claim a saving. A model or effort that wasn't run carries the nearest measured ratio and says `interpolated`.

The host can run the Stop hook before it has written the final message. The hook compares `last_assistant_message` with the transcript and waits up to `TOKEN_BEGGAR_SETTLE` seconds (default 4). If the message is still missing the footer says "at least". Before that wait existed the footer undercounted a real run by the size of the last message (49k against 69.9k). It now agrees with the agent's own total (86k against 85.8k).

## Modes

`footer.mode` reads `data/measured.json` for the chat model and effort and returns how much the skill acts. `overall` holds the measured price-weighted cost ratio per model and effort.

| Mode | When | What the hooks do |
| --- | --- | --- |
| `full` | the small task ratio is at or above 1.15 (a saving clear of the run to run spread), or the model was not measured | the whole menu, the reminder after it and the footer, small tasks included |
| `sized` | everything else | one short card that decides by task size. Small tasks stay inline with nothing added. Large tasks (an issue in code you have not read, more than about 5 tool calls, more than one file, an edit and test loop) go to one worker, and the chat reads the whole diff before it answers. A footer follows a large task only |
| `off` | the chat is already the cheapest model | no card, no delegation, no footer |

The task decides first and the model second: `sized` is what every model gets unless its small task ratio clears 1.15. A step counter (`PostToolUse`) sends a one line reminder once a small task passes about 5 steps, so the rest of it is routed. The footer's multiple for a large task comes from the `large` key of `data/measured.json` (hard task benchmark, Opus 5.5 at high effort only). `TOKEN_BEGGAR_MODE` forces one of the three. The compaction guard runs in every mode. `token-beggar doctor` forces `full` for its own hook check so the result does not depend on the ceiling.

## Compaction guard

Works without any setting. `compact.py` finds the compaction point as the context window of the model minus 33k tokens, the host's default. `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (clamped to 100k to 1M) and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` are read when set. `token-beggar window` prints the point and where it came from.

- Every prompt and after every tool call (`PostToolUse`): at 87.5 percent of the point, or 30k tokens before it if that is earlier, a notice asks the chat model to judge where it is and to save a note with `token-beggar note` (`--mid-step`, `--clean` or `--phase-done`, plus optional `--progress` and `--needs-early-detail`). The extra margin is there because one large tool result can jump a small margin in a single call.
- With `TOKEN_BEGGAR_EARLY=1` (off by default, because the long-session benchmark measured no saving and a quality loss), on a long context (150k, or 40 percent of a small point, never under 60k), once per stage, the notice asks the model whether a phase just finished. If so it saves a `--phase-done` note and suggests `/compact` to the user in one line. A hook cannot start a compaction, and the host reads its window setting only at startup, so a lower point cannot be set from inside a session. Suggesting is the one honest way to compact early.
- `PreCompact`: writes the mechanical extract (request, files changed, last commands, open todos, where the last turn stopped) to `handoff/<session>.md` so a note exists even if the model wrote none. For an automatic compaction, when the note says mid-step (or the model's note is missing and there are unverified edits), it exits with code 2, which makes the host postpone the compaction. Up to 3 times, each lifting the point by 5 percent of the window: 3 when the step is far from done or needs early detail, 1 when nearly done. Never past `blocked - 5k` where `blocked` is the level where the host refuses requests.
- A point the user set (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `autoCompactWindow`, `modelSettings.autoCompactWindow`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) is never moved: no deferral, no suggestions. The notes are still written and restored. Token Beggar writes no settings.
- `SessionStart` on `compact`: puts the note and the menu back in front of the model. The model's note comes after the extract, and a note written more than 15k tokens of context before the compaction is labelled as old.

Tested in real print mode sessions with a 100k window (the lowest the host allows): the notice came at 47k and 63k of a 67k point, two compactions were deferred, the host compacted once at 95k, and the model finished the task from the note. A host compaction can still land before the model reacts if one tool result is larger than the margin. Edits made inside a worker are not in the main transcript, so they are neither deferred for nor listed. A manual `/compact` is never blocked. The `PreCompact` output isn't shown in the event stream, so its effect is seen in the state files and in what is restored afterwards.

A test run counts when a step of the shell line starts with a known runner (`pytest`, `python3 -m unittest`, `npm test`, `cargo test`, `ruff`, `make test` and similar). Naming a tests folder in `ls` or `cat` does not.

## Weekly update

`update-models.yml` runs every Monday, fetches the public models page, rewrites `data/models.json` and opens a pull request if the model rows changed. On your machine the prompt hook starts the same refresh in the background once a week, writes it to `models.json` in the state directory, and the newer of the two files wins. If the page changes shape, the parser raises and the old catalog stays.
