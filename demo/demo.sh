#!/bin/sh
# The demo shown in assets/demo.gif. Every line is a real command against this checkout.
# It uses a throwaway state directory, so it touches nothing in ~/.claude.
set -e
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d /tmp/token-beggar-demo.XXXXXX)"
trap 'rm -rf "$work"' EXIT
export TOKEN_BEGGAR_HOME="$work/state" TOKEN_BEGGAR_OFFLINE=1 CLAUDE_CODE_AUTO_COMPACT_WINDOW=400000
export ANTHROPIC_MODEL=claude-opus-5-5 CLAUDE_CODE_EFFORT_LEVEL=high
mkdir -p "$work/state"
tb() { PYTHONPATH="$here" python3 -m token_beggar "$@"; }

step=${1:-all}
want() { [ "$step" = all ] || [ "$step" = "$1" ]; }

if want 1; then
echo '$ token-beggar route --model opus --effort high'
tb route --model opus --effort high
echo
fi

if want 2; then
echo '$ # a prompt arrives; the hook adds this card to the context'
printf '%s' '{"prompt":"Rename calc_total to order_total across the repo and run the tests","session_id":"demo","cwd":"'"$work"'","transcript_path":""}' |
  tb hook prompt | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])' | sed -n '1p;4,11p' | cut -c1-110
echo
fi

if want 3; then

echo '$ # context is at 410k of 400k and a file was edited but not tested: compaction is deferred'
python3 - "$work" <<'PY'
import json, sys
path = sys.argv[1] + "/session.jsonl"
rows = [
    {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Migrate the billing module"}]}},
    {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-5-5", "usage": {"input_tokens": 410000, "output_tokens": 50},
     "content": [{"type": "tool_use", "id": "1", "name": "Edit", "input": {"file_path": "billing/invoice.py"}}]}},
]
open(path, "w").write("\n".join(map(json.dumps, rows)) + "\n")
PY
printf '%s' '{"session_id":"demo","trigger":"auto","cwd":"'"$work"'","transcript_path":"'"$work"'/session.jsonl"}' | tb hook precompact || echo "exit code $?"
echo
echo '$ head the note it wrote before anything could be lost'
sed -n 1,9p "$work/state/handoff/demo.md"
fi

if want 4; then
echo '$ # measured: 63 runs per arm, Opus 5.5 high as the chat model'
sed -n '5p;7,14p' benchmark/results/report.md | tr -d '*' | awk -F'|' '{printf "%-14s%-12s%-11s%-11s%-15s%s\n", $2,$3,$4,$5,$7,$8}'
fi
