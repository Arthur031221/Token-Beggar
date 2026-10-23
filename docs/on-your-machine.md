# What it does on your machine

Everything the plugin does in the background, so you know before you install it. Nothing here is hidden behind a setting. It needs no permission prompts beyond the normal ones of your agent, and it installs nothing with pip.

## The seven hooks

All seven run `python3 -m token_beggar hook <name>` from the plugin directory. A hook that fails writes to `errors.log` and exits 0, so it never breaks your session.

| Hook | When it runs | What it does |
| --- | --- | --- |
| `UserPromptSubmit` | on every prompt | Adds the routing card to the first real prompt of a session, checks how full the context is, starts the weekly model list refresh when it is due |
| `PreToolUse` (Agent and Task only) | before a worker starts | Holds the worker to the ceiling of your chat model and keeps out models that are out of quota |
| `PostToolUse` | after every tool call | Counts the steps of the reply and watches the context against the compaction point |
| `PostToolUseFailure` (Agent and Task only) | when a worker fails | Reads a usage limit error so that model stays off the menu until it resets |
| `PreCompact` | before a compaction | Writes a short note of the goal, what is done and what is next. May postpone an automatic compaction in the middle of a step, up to 3 times |
| `SessionStart` (after a compaction) | when the session resumes | Puts the note back into the context |
| `Stop` | at the end of each turn | Reads the transcript and adds the one line footer when a saving was measured |

## What it reads

- **The session transcript** of the current session, to count what the reply and its workers cost (for the footer) and to find the context size and the chat model. It stays on your machine.
- **The launch flags of the chat process**, with `ps -o args= -p <pid>` and `ps -o ppid=`, to learn the model and effort you started with, since a hook cannot see them. The ceiling comes from there.
- **The environment** variables listed by `token-beggar env`, and the agent's settings files for the model and effort.

## What it runs and sends

- **A weekly download of one public page**, the model vendor's models overview (`https://platform.claude.com/docs/en/about-claude/models/overview.md`), to keep prices and windows current. No data about you goes with it. `TOKEN_BEGGAR_OFFLINE=1` turns it off, and also stops it from listing outside models.
- **Outside AI tools** (`agy`, `gemini`, `codex`) only when one is installed and routing picks it, which the card allows only when you name the tool or one read is about 100k tokens or more. Then the text of the files you pass is sent to that tool under its own terms. File names and text that look like secrets are refused. `TOKEN_BEGGAR_EXTERNAL=none` turns this off. `agy models` is run to list its models.
- **The worker** (`agents/beggar-worker.md`) has Read, Grep, Glob, Bash, Edit and Write. They run under your own permission settings, so a command or an edit that your agent asks about still asks you.

## Where it writes

One state directory, `~/.claude/token-beggar` (`TOKEN_BEGGAR_HOME` moves it; `token-beggar env` prints it): the model list and the date of its last refresh, the tool inventory, per session counters and notes, a ledger of workers, `errors.log`. It writes no agent settings and no files in your project.

## Turn it off or remove it

- One shell: start the agent with `TOKEN_BEGGAR=off`.
- For good: create a file named `off` in the state directory.
- Check it: `token-beggar doctor`.
- Remove it: `/plugin uninstall token-beggar`, then delete the state directory if you want the notes gone.
