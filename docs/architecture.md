# Architecture

```
prompt -> UserPromptSubmit hook -> routing card in context
                                      |
                  model grades the task, calls Agent(model, effort) per row
                                      |
                  beggar-worker (haiku or sonnet) does the bulk, returns < 150 words
                                      |
                  model checks with one command and answers
```

The host agent gives a plugin hooks, skills and agents but no hook that can change the model of the chat itself. So Token Beggar works through the one lever that exists: the Agent tool takes a `model` and an `effort` on every call.

## Parts

| Path | Role |
| --- | --- |
| `hooks/hooks.json` | wires three events to `python3 -m token_beggar hook <event>` |
| `token_beggar/ceiling.py` | finds the chat's model and effort: transcript, then launch flags, then environment, then settings |
| `token_beggar/routes.py` | class + ceiling -> model, effort, mode. Never above the ceiling |
| `token_beggar/card.py` | builds the text the model sees |
| `token_beggar/inventory.py` | models denied by settings, CLI tools on the PATH, quota marks |
| `token_beggar/update.py` | parses the vendor's public models page into `models.json` |
| `token_beggar/compact.py`, `handoff.py`, `transcript.py` | the compaction guard |
| `skills/token-beggar/SKILL.md` | the rules and the rubric |
| `agents/beggar-worker.md` | the worker |
| `benchmark/` | the runner, the tasks and the raw results |

## Finding the ceiling

A hook does not receive the model or the effort. Token Beggar reads them from the best source that has them:

1. the model of the last main-chain assistant message in the transcript,
2. the `--model` and `--effort` flags of the agent process that started the hook,
3. the model and effort environment variables (`token-beggar env` lists them),
4. `model` and `effortLevel` in `settings.json`.

If none of them names a known model, the card says so and tells the model to treat itself as the ceiling.

## Compaction guard

Three hooks, all in `compact.py`:

- Every prompt: when the context is within 12.5 percent of the compaction point, the card adds a one line warning to reach a clean stopping point.
- `PreCompact`: always writes a note to `handoff/<session>.md` in the state directory with the original request, the files changed, the last commands, open todos and where the last turn stopped. For an automatic compaction it checks one rule: were files edited after the last test, lint or build command? If so it exits with code 2, which makes the host agent postpone the compaction. It defers at most three times and never when the context is more than 15 percent past the point.
- `SessionStart` on `compact`: puts the note and the card back in front of the model.

What it cannot do: it does not see the model's plan, only the transcript. "Mid step" means unverified edits, nothing finer. Edits made inside a worker are not in the main transcript, so they are neither deferred for nor listed in the note. A manual `/compact` is never blocked. Without a compaction window set (`token-beggar window` shows it), only the note is written.

A test run counts when a step of the shell line starts with a known runner (`pytest`, `python3 -m unittest`, `npm test`, `cargo test`, `ruff`, `make test` and similar). Naming a tests folder in `ls` or `cat` does not.

## Weekly update

`update-models.yml` runs every Monday, fetches the public models page, rewrites `data/models.json` and opens a pull request if the model rows changed. On your machine the prompt hook starts the same refresh in the background once a week, writes it to `models.json` in the state directory, and the newer of the two files wins. If the page changes shape, the parser raises and the old catalog stays.
