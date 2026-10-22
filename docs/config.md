# Configuration

| Setting | Effect |
| --- | --- |
| `TOKEN_BEGGAR=off` | disable the hooks for this process |
| a file named `off` in the state directory | disable the hooks everywhere |
| `TOKEN_BEGGAR_HOME` | state directory. `token-beggar env` prints the one in use |
| `TOKEN_BEGGAR_OFFLINE=1` | never fetch the models page |
| the host's compaction window variable | the point where the host agent compacts. Token Beggar reads it, from the environment or the `env` block of `settings.json`. When it is not set, the warning and the deferral are off, because a guessed window could let a deferral run past the model's real limit. The handoff note is written either way. The host ignores very small values, so use 60000 or more |
| `deniedModels`, `availableModels` in `settings.json` | models you block there are left out of routing |

`token-beggar env` lists every variable by name, with what it does.

## Editing the router

- `data/routes.json`: the seven classes, the tier, effort and mode of each.
- `data/models.json`: model ids, tiers and list prices. Refreshed weekly.
- `data/measured.json`: the benchmark numbers the footer may quote.
- `agents/beggar-worker.md`: the worker. It defaults to haiku at low effort. The caller overrides model and effort per call.

## Quota

If a model hits its limit, run `token-beggar exhausted <alias>`. Routing steps down to the next model until the mark expires. The model does this itself when a dispatch fails with a usage limit.

## Other AIs

`token-beggar inventory` lists `codex`, `agy` and `gemini` when they are on the PATH. Token Beggar never installs them and never sends them anything on its own. The skill only tells the model they exist.
