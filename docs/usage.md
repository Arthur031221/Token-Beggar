# Usage

You do not have to do anything. On the first non-trivial prompt of a session, a hook adds a short routing card to the context. The model reads it, grades the task and hands bulk work to a cheaper worker.

## What gets routed

| Class | Where it goes |
| --- | --- |
| mechanical | smallest model, low effort, in a worker |
| reading | smallest model, medium effort, in a worker |
| routine_code | next model down, medium effort, in a worker |
| multi_file | next model down, high effort, in a worker |
| review | the chat model, inline (a worker cost more than it saved in the benchmark) |
| debugging | stays with your chat model |
| design | stays with your chat model |

Chat, one line answers and anything under about three tool calls stay inline. A worker starts with its own base context, so tiny jobs would cost more as workers.

## The ceiling

The model and effort of your chat cap what the same vendor's models get routed to. Opus at high effort never sends work to Opus at max or to Fable. Other providers on your machine (`codex`, `agy`, `gemini`) are not capped, unless you say so in the prompt: "agy max flash".

## Commands

```
token-beggar route                  show the routing table for this chat
token-beggar route --model sonnet --effort medium
token-beggar inventory --refresh    rescan models and tools on this machine
token-beggar update                 refresh the model list now
token-beggar exhausted opus         mark a model out of quota for 5 hours
token-beggar exhausted --clear
token-beggar window                 print the compaction point in use
token-beggar env                    list the environment variables and the state directory
```

You can also type `/token-beggar` or say "token beggar" to have the model apply the skill by hand.

## The footer

After a reply where work went to a cheaper model, the model adds one line, for example `Token Beggar: about 1.5x less spend than the top model at high effort alone (measured, mechanical)`. The number comes from `data/measured.json`, which `benchmark/report.py` writes, and only for classes measured at 1.15x or more. It only appears when your chat model and effort match the ones the benchmark ran on. Otherwise you get a plain `routed 2 subtasks to haiku`.

## Compaction guard

See [architecture](architecture.md#compaction-guard).
