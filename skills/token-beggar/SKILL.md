---
name: token-beggar
description: Use on every non-trivial task in the coding agent, such as coding, debugging, code review, research, summarising or writing. It grades the task, splits it into parts and hands each part to the cheapest model and effort that still does it right, using subagents and any other AI already wired in. Also runs when the user types /token-beggar or says "token beggar".
---

# Token Beggar

Most prompts do not need the biggest model at the highest effort for every step. Reading files, applying edits and running tests are cheap work. Design and root-cause judgement are not. Send each part where it belongs and keep the answer quality the same.

A hook adds a routing card to your context with the exact table for this session. Follow the card. This file explains the rules behind it.

## 1. Grade the task

| Class | Looks like |
| --- | --- |
| mechanical | rename, reformat, bump a version, apply a list of exact changes |
| reading | summarise logs or docs, find where something is defined, answer questions about long text |
| routine_code | one function or file with a clear spec, a unit test, a script |
| multi_file | a feature across several files that must keep tests green |
| debugging | something fails and the cause is unknown |
| design | trade-offs, structure, what to build |
| review | find defects in a diff or file before it ships |

A prompt can hold several classes. Split it: reading first, then the code, then your own judgement on the result.

## 2. Respect the ceiling

The model and effort of this chat are the upper limit for models of the same vendor. Never dispatch a higher model, and never a higher effort than the chat runs at. Models from other providers are not bound by this, unless the user caps them in the prompt, for example "agy max flash". Honour that cap.

## 3. Delegate only when it saves tokens

Delegate when the work needs many tool calls or large reads that you would otherwise carry in your own context: whole-file reads, log digging, repeated edits, test loops. The subagent works in its own context and returns a short result.

Stay inline when:
- the task is a chat answer or needs under about three tool calls,
- the subagent would need most of this conversation to do the job,
- the step is design, root-cause judgement or the final answer.

Every subagent starts with its own base context, so one tiny subagent costs more than doing the step yourself.

When you do delegate, delegate first. Exploring the code yourself before handing it over means you pay the big model for the very reading you meant to avoid.

## 4. Dispatch

Call the Agent tool with `subagent_type: "token-beggar:beggar-worker"` and set `model` and `effort` for that call from the table, and `run_in_background: false` so the result comes back before you go on. Independent parts go out in one message so they run in parallel. Write the prompt so the worker needs nothing else: the goal, the exact file paths, what to change, the check to run, and "report in under 150 words". Do not ask it to paste files back.

## 5. Check the result

Check cheaply: one test run or `git diff --stat`, not a second read of every file. For code, run the tests yourself or confirm the worker ran them and read the output line. If the result is wrong or the check fails, redo the step once on the next model up, never above the ceiling. If it fails there too, do it inline.

## 6. Other AIs on this machine

If the card lists `codex`, `agy` or `gemini`, they are available for bulk reading and independent second opinions through their command line (`codex exec "<prompt>"`, `gemini -p "<prompt>"`). Send no secrets and no private data to a provider the user has not already approved. See [reference/other-ais.md](reference/other-ais.md).

## 7. Quota

If a dispatch fails with a usage limit for a model, mark it so routing skips it for a while: `token-beggar exhausted <alias>`. Clear it with `token-beggar exhausted --clear`.

## 8. Footer

The card says when to end a reply with the one-line Token Beggar footer and which measured number to use. Copy the number from the card, never estimate one. If you routed nothing, write no footer.

## What this cannot do

It cannot change the model of this chat in the middle of a turn. It saves tokens by moving work to subagents and other tools, so a task that is all judgement saves nothing.
