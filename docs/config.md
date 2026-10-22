# Configuration

| Setting | Effect |
| --- | --- |
| `TOKEN_BEGGAR=off` | disable the hooks for this process |
| a file named `off` in the state directory | disable the hooks everywhere |
| `TOKEN_BEGGAR_HOME` | state directory. `token-beggar env` prints the one in use |
| `TOKEN_BEGGAR_MODE` | `off`, `lean` or `full`. Forces how much the skill acts. Unset, the measured cost ratio for the ceiling decides |
| `TOKEN_BEGGAR_EARLY=1` | turn on the early `/compact` suggestion at a finished phase. Off by default |
| `TOKEN_BEGGAR_OFFLINE=1` | never fetch the models page |
| `TOKEN_BEGGAR_EXTERNAL` | comma list of outside tools routing may use (for example `agy`), or `none` |
| `TOKEN_BEGGAR_EXTERNAL_TIMEOUT` | seconds an outside call may run. Default 600 |
| `TOKEN_BEGGAR_SETTLE` | seconds the footer waits for the last message to reach the transcript. Default 4 |
| the host's compaction window variable | optional. The compaction guard finds the point from the model's own window (33k short of it) and works with nothing set. When the variable is set (100000 to 1000000) or the percent override is, that value is used. `token-beggar window` shows which |
| `deniedModels`, `availableModels` in `settings.json` | models you block there are left out of routing |

`token-beggar env` lists every variable by name, with what it does.

## Editing the router

- `data/profiles.json`: the capability and price of each Claude model, what each outside tool is good and weak at, and the decision rules the menu prints. Change a rule here, then run the benchmark (see CONTRIBUTING).
- `data/models.json`: model ids, tiers and list prices. Refreshed weekly.
- `data/measured.json`: the benchmark numbers the footer quotes (the pooled ratios, the interpolated cells, the router comparison, the outside tool results).
- `agents/beggar-worker.md`: the worker. It defaults to haiku at low effort. The caller overrides model and effort per call.

## Caps

Say it in a prompt: "agy max flash" keeps agy to its flash models, "agy max medium" to medium levels and below, "no gemini" switches a tool off for the session, "agy max none" lifts a cap. Or run `token-beggar cap agy flash`, `token-beggar cap agy` (off), `token-beggar cap` (show). Same vendor models are capped by the model and effort of the chat.

## Quota

If a Claude model hits its limit, run `token-beggar exhausted <alias>`. It leaves the menu until the mark expires. For an outside tool, `token-beggar ask` reads the reset time from the usage-limit error (five hours when the text has none, a day for a login problem), marks that tool or model, and the next menu leaves it out.

## Outside tools

`token-beggar inventory --refresh` lists `agy`, `gemini` and `codex` when they are on the PATH, the models `agy models` reports, and MCP servers found in your settings. Nothing is sent to them unless the chat model decides a subtask suits them, and files that look like secrets are refused. The prior is the host's own models first, then Codex, then Gemini. The Gemini CLI has to be logged in; if it isn't, the call fails with a login message and the tool is left off the menu for a day.
