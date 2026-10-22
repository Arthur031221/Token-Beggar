# Usage

You do not have to do anything. On the first non-trivial prompt of a session, a hook adds a short routing card to the context. The model reads it, grades the task and hands bulk work to a cheaper worker.

## What gets routed

Nothing is fixed in advance. The chat model splits the prompt into subtasks and picks each route from the menu: itself inline, a worker (any model and effort at or under the ceiling) or an outside tool. The rules it follows are in `data/profiles.json` and print with `token-beggar menu`. In short:

- Small, ambiguous or risky work, design, root causes and anything that needs this conversation stays inline.
- Mechanical edits and bulk reading go to the smallest model that does them right, usually in a worker.
- Multi-file work with a test that can verify it goes to a worker one step below the ceiling.
- Bulk reading, a first draft and a second opinion can go to an outside tool when one is available.

Chat, one line answers and anything under about three tool calls stay inline. A worker starts with its own base context, so tiny jobs would cost more as workers.

## The ceiling

The model and effort of your chat cap what the same vendor's models get routed to. Opus at high effort never sends work to Opus at max or to Fable. Outside tools on your machine (`agy`, `gemini`, `codex`) are not capped, unless you say so in the prompt: "agy max flash".

## Commands

```
token-beggar menu                   every provider, model and effort routing can pick for this chat (--model, --effort, --json)
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
