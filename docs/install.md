# Install

Token Beggar is a plugin for a terminal coding agent (the agent with a plugin marketplace and Agent tool). It needs that agent and Python 3.10 or newer. It uses the standard library only.

## From the marketplace in this repository

```
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

Restart the agent or run `/reload-plugins`. The next non-trivial prompt of a session carries the routing card.

## Try it for one session without installing

```
git clone https://github.com/Arthur031221/Token-Beggar
<your agent command> --plugin-dir ./Token-Beggar
```

## Check that it works

Run:

```
token-beggar doctor
```

It prints one line per check and exits 1 if something is broken. A warning is not a failure, but each one names something that would change routing: a forced worker model, an unset compaction window, a hook error in the log, or a catalog older than 30 days. After a few sessions, `token-beggar stats` shows the workers that ran. To see the routing table, run `token-beggar route`.

The plugin puts `token-beggar` on the PATH of the agent's shell. Outside the agent, run `python3 -m token_beggar route` from the repository root.

## Turn it off

- For one shell: start the agent with `TOKEN_BEGGAR=off` in its environment.
- For good: create a file named `off` in the state directory (`token-beggar env` prints its path). Delete the file to turn it back on.
- Remove it: `/plugin uninstall token-beggar`

## Where it keeps files

Everything lives in one state directory, printed by `token-beggar env`: the model inventory, quota marks, handoff notes and an `errors.log`. Nothing is sent anywhere. The only network call is the weekly download of the model vendor's public models page.
