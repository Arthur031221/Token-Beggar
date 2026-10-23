#!/bin/sh
# The demo shown in assets/demo.gif. Every line is a real command against this checkout.
# It uses a throwaway state directory, so it touches nothing in ~/.claude.
set -e
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d /tmp/token-beggar-demo.XXXXXX)"
trap 'rm -rf "$work"' EXIT
export TOKEN_BEGGAR_HOME="$work/state" TOKEN_BEGGAR_OFFLINE=1
export ANTHROPIC_MODEL=claude-opus-5-5 CLAUDE_CODE_EFFORT_LEVEL=high
mkdir -p "$work/state"
tb() { PYTHONPATH="$here" python3 -m token_beggar "$@"; }

step=${1:-all}
want() { [ "$step" = all ] || [ "$step" = "$1" ]; }

if want 1; then
echo '$ token-beggar mode --all   # measured: cost with the skill vs alone'
tb mode --all
echo
fi

if want 2; then
echo '$ # a bug report arrives on Opus high; the hook adds this card (sized mode, first lines)'
printf '%s' '{"prompt":"Fix this issue: format_filename raises on non-unicode paths. Reproduce it, find every place with the same symptom, fix it and run the tests","session_id":"demo","cwd":"'"$work"'","transcript_path":""}' |
  tb hook prompt | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])' | fold -s -w 90 | sed -n 1,15p
echo
fi

if want 3; then

echo '$ # context is at 968k of a 967k point and a file was edited but not tested: compaction is deferred'
python3 - "$work" <<'PY'
import json, sys
path = sys.argv[1] + "/session.jsonl"
rows = [
    {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Migrate the billing module"}]}},
    {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-5-5", "usage": {"input_tokens": 968000, "output_tokens": 50},
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
echo '$ token-beggar doctor'
tb doctor | cut -c1-110
echo
fi

if want 5; then
echo '$ # measured: 18 real bug fixes, 3 runs each, Opus 5.5 high as the chat model'
python3 - "$here" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1] + "/benchmark/results/hard/summary.json"))["arms"]
names = {"alone": "Without Token Beggar", "main": "Main before v0.3.0", "scoped": "v0.3.0 (this release)"}
print(f"{'':<24}{'cost/run':<10}{'multiple':<26}resolved")
for key, name in names.items():
    r = rows[key]
    mult = "1.00x" if key == "alone" else f"{r['multiple']:.2f}x ({r['low']:.2f} to {r['high']:.2f})"
    print(f"{name:<24}${r['cost']:<9.2f}{mult:<26}{r['resolved'] * 100:.0f}%")
PY
fi
