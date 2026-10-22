# Other AIs

Use them only when the card lists them or the user asks.

| Tool | Headless call | Good for |
| --- | --- | --- |
| Codex | `codex exec "<prompt>"` | an independent review, a second implementation |
| Gemini | `gemini -p "<prompt>"` | reading long documents or logs |
| Antigravity | `agy` with the prompt on stdin or as an argument, per its own help | bulk reading and summaries |
| An MCP server | its tool, named in the card | whatever the server exposes |

Rules:
- Give each call the full task. These tools do not see this conversation.
- The user's cap wins: if they wrote "agy max flash", use the Flash tier and nothing larger.
- Treat the answer as a draft from a colleague. Check it before relying on it.
- Never send secrets, tokens or private data.
