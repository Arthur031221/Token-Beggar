# Usage

You do not have to do anything. On the first non-trivial prompt of a session, a hook adds a short routing card to the context. The model reads it, grades the task and hands bulk work to a cheaper worker.

## What gets routed

The chat model sizes the task before it reads any code.

- Small (a one-shot answer, an edit to one named file): it works inline. Nothing is dispatched and no footer is added.
- Large (an issue or bug in a repository it has not read, more than about 5 tool calls, more than one file, an edit and test loop): it sends one worker the whole reproduce, explore, fix and run-the-tests list. The worker reports in under 150 words, then the chat reads the whole `git diff`, runs the tests itself and keeps the root cause, the design choices and the answer.
- A small task that grows past about 5 steps, or sits in a long context, is large from then on.

The worker is one tier below your chat model (Haiku under Sonnet or higher). Outside tools (`agy`, `gemini`, `codex`) are used only when you name one or a single job reads about 100k tokens or more. The full menu of providers, models and efforts, with the rules behind it, is in `data/profiles.json` and prints with `token-beggar menu`.

## When it stands down

`data/measured.json` holds the cost with the skill over the cost alone for the model and effort of your chat. Where small tasks measured a saving clear of the spread (1.15x or more) the whole menu is used (`full`: Fable at every effort, Opus at max). Everywhere else the size decides (`sized`). If the chat is already the cheapest model there is nothing cheaper to send work to, so there is no card, no delegation and no footer (`off`). `TOKEN_BEGGAR_MODE=full|sized|off` forces a mode.

## The ceiling

The model and effort of your chat cap what the same vendor's models get routed to. Opus at high effort never sends work to Opus at max or to Fable. Outside tools on your machine (`agy`, `gemini`, `codex`) are not capped, unless you say so in the prompt: "agy max flash".

## Commands

```
token-beggar menu                   every provider, model and effort routing can pick for this chat (--model, --effort, --json)
token-beggar mode                   how much the skill acts for this ceiling and the measured ratio behind it (--model, --effort, --all)
token-beggar ask agy "<task>"       hand one task to an outside tool (--model, --file path-or-glob ...)
token-beggar cap agy flash          cap an outside tool for this session; `cap agy` switches it off; `cap` shows the caps
token-beggar note --mid-step        save the note the next compaction restores (--clean when between steps; text as arguments or on stdin)
token-beggar inventory --refresh    rescan models, outside tools and MCP servers on this machine
token-beggar update                 refresh the model list now
token-beggar exhausted opus         mark a model out of quota for 5 hours
token-beggar exhausted --clear
token-beggar doctor                 check hooks, state directory, overrides and logged errors
token-beggar stats                  workers run in the last 7 days and what they cost (--days N, --json)
token-beggar window                 print the compaction point in use and where it came from
token-beggar env                    list the environment variables and the state directory
```

You can also type `/token-beggar` or say "token beggar" to have the model apply the skill by hand.

## The footer

After a reply where Token Beggar routed something, a hook adds one line:

```
Token Beggar: about 1.3x less quota than Opus 5.5 high alone, saved about $0.42 (est.) | exact edits | routed 3: haiku low x2, agy flash x1
```

The multiple is the measured price-weighted cost ratio for your model, effort and kind of task (`data/measured.json`), so it is an estimate. The dollars are the reply's own list-price cost, counted from the transcript (the chat plus every worker, each at its model's price), times the ratio minus one. The line never shows token counts. A ratio from a cell that wasn't run says `interpolated`. Under 1.15x the line states no multiple. If the last message wasn't in the transcript when the hook ran, the dollar figure is prefixed "at least".

## Compaction guard

See [architecture](architecture.md#compaction-guard).
