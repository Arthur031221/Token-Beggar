# Other AIs

They are routing targets. The menu at the start of the session lists the ones that are installed, with the models found on this machine.

| Tool | How it is called | Good for |
| --- | --- | --- |
| agy (Antigravity) | `token-beggar ask agy --model <id>` | bulk reading, summaries, drafts, a second opinion. The model list comes from `agy models` |
| gemini | `token-beggar ask gemini` | reading long documents or logs |
| codex | `token-beggar ask codex` | an independent review, a second implementation |
| An MCP server that fronts another AI | its tool, named in the menu | whatever the server exposes |

Order of trust: the host's own models, then Codex, then Gemini. Judgement and the final answer stay with the host model and bulk work can go out. The host model always checks the result.

Rules:
- Give each call the whole task. These tools do not see this conversation. Name files with `--file`. Their text goes into the prompt and the tool runs in an empty directory with no tools.
- The user's cap wins: "agy max flash" allows the flash models and nothing larger, "no gemini" switches it off. `token-beggar cap` shows what is recorded for the session.
- Treat the answer as a draft from a colleague. Check it before relying on it.
- Never send secrets, tokens or private data. `ask` refuses file names that look like secrets and prompts that contain a key.
- A usage limit or login error marks that tool or model out for the time the error gives (five hours when it gives none, a day for a login error). The menu then leaves it off. `token-beggar exhausted --clear` resets this.
- Tokens an external tool reports are counted separately in the footer and never added to the host total.
