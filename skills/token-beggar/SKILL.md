---
name: token-beggar
description: Use on every non-trivial task in the coding agent, such as coding, debugging, code review, research, summarising or writing. It splits the prompt into subtasks and hands each one to the cheapest provider, model and effort that still does it right, using subagents and any other AI already wired in. Also runs when the user types /token-beggar or says "token beggar".
---

# Token Beggar

Most prompts do not need the biggest model at the highest effort for every step. Reading files, applying edits and running tests are cheap work. Design and root-cause judgement are not. Send each part where it belongs and keep the answer quality the same. The goal is the fewest Claude tokens at the same quality.

A hook adds a menu to your context at the start of the session: every provider, model and effort you may use here, with what each is good and weak at. There is no fixed table. You choose per subtask, with the rules below. This file explains them.

## 1. Split the prompt

Break the prompt into subtasks before you read a file or run a command. A prompt often holds several: find things, change things, check things, decide things. Each gets its own pick.

## 2. Pick for each subtask

Start at the cheapest combination whose strengths fit, and check these five things:
- Size. One to three tool calls or a short answer is cheaper inline than a worker, which starts with its own base context.
- Context to read. Many files or long logs go to a worker or an external AI, so the reading does not sit in your context.
- Ambiguity. An open choice, or an answer that depends on this conversation, stays inline or goes one model up.
- Risk. Data loss, money, auth or a public API gets a model at or near your own, or your own review of the diff.
- Verifiable. If a test or command can check the result, a cheaper model is safe, because a failure shows. If nothing can check it, use a stronger one.

Synthesis (explaining how parts fit together) stays inline or on a mid model. A cheap model reads and lists, it does not conclude.

## 3. Respect the ceiling

The model and effort of this chat are the upper limit for models of the same vendor. Never dispatch a higher model, and never a higher effort than the chat runs at. A hook enforces this on every worker call. Models from other providers are not bound by it unless the user caps them, for example "agy max flash" or "no gemini". The hook records such caps, and `token-beggar ask` refuses what they forbid.

## 4. Dispatch

Claude workers: call the Agent tool with `subagent_type: "token-beggar:beggar-worker"`, set `model` and `effort` on that call, and `run_in_background: false`. Independent subtasks go out in one message so they run in parallel. Write the prompt so the worker needs nothing else: the goal, exact file paths, what to change, the check to run, and "report under 150 words with exact names and paths". Do not ask it to paste files back. Delegate first: exploring the code yourself before handing it over pays the big model for the reading you meant to avoid.

## 5. Check the result

Check cheaply: one test run or `git diff --stat`, not a second read of every file. If the result is wrong or the check fails, redo the step once one step up, never above the ceiling. If it fails there too, do it inline. Judgement, design, root cause and the final answer stay with you.

## 6. Other AIs

Tools on this machine, such as agy, gemini and codex, and MCP servers that front another AI, are routes too. They use their own quota, so the work does not touch your Claude quota. Use them for bulk reading, summaries, first drafts and second opinions. Claude is the judge: treat what they return as a draft and check it. Call one with `token-beggar ask <tool> [--model <id>] [--file <path> ...] "<the whole task>"`. The command refuses files that look like secrets, applies the user's caps, and marks the tool out of quota when it says so. See [reference/other-ais.md](reference/other-ais.md).

## 7. Quota

If a Claude dispatch fails with a usage limit, run `token-beggar exhausted <alias>`; the menu then leaves that model off for a while. For external tools `ask` does this by itself from the error text. `token-beggar exhausted --clear` resets it.

## 8. Context and compaction

The skill picks the compaction moment unless the user has set one. When the context nears the compaction point, or a phase has just finished on a long context, a hook asks you to save a note: `token-beggar note --mid-step | --clean | --phase-done` with the goal, decisions and why, open threads, file paths and next steps on stdin. Optional flags: `--progress 0..1` (how far the current step is) and `--needs-early-detail` (later work depends on early details).

- Mid-step: the compaction is deferred, longer when the step is far from done or needs early detail, shorter when it is nearly done, always below the host's blocking level.
- On a long context (about 150k, or 40 percent of a small point, never under 60k) a hook asks once whether a phase just finished. If it did and the rest does not need its raw details, save `--phase-done` and tell the user in one line that now is a good moment to type `/compact`. A hook cannot start a compaction, so you suggest it. If the next work needs the details, save `--needs-early-detail` and say nothing.
- If the user set `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `autoCompactWindow` or `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, the point is theirs: no deferral and no suggestions.

The note is handed back after the compaction. `token-beggar window` shows the point in use and who chose it. Token Beggar writes no settings: the host reads its window only at startup, so a change made mid-session would not take effect.

## 9. Footer

A one-line footer with the quota multiple and the money saved is added at the end of the turn by a hook. Do not write one, and never state token counts.

## What this cannot do

It cannot change the model of this chat in the middle of a turn. It saves quota and money by moving work to subagents and other tools, so a task that is all judgement saves nothing.
