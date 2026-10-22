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
echo '$ # a multi-file prompt arrives on Opus high; the hook adds this card (lean mode)'
printf '%s' '{"prompt":"Add a coupon discount to the cart, billing and invoice modules and run the tests","session_id":"demo","cwd":"'"$work"'","transcript_path":""}' |
  tb hook prompt | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])' | fold -s -w 104
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
echo '$ # measured: 84 runs per arm (28 tasks x 3), Opus 5.5 high as the chat model'
python3 - "$here" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1] + "/benchmark/results/final/summary.json"))
names = {"all": "all 28 tasks", "multi_file": "multi-file", "routine_code": "routine code", "debugging": "bug root cause", "mechanical": "mechanical edits", "reading": "reading"}
print(f"{'':<17}{'alone':<9}{'this release':<14}{'saving':<18}quality")
for key, name in names.items():
    r = rows[key]
    mult = f"{r['final']['multiple']:.2f}x" + ("" if r["final"]["claim"] else " (noise)")
    print(f"{name:<17}${r['alone']['cost']:<8.3f}${r['final']['cost']:<13.3f}{mult:<18}{r['alone']['quality']:.2f} -> {r['final']['quality']:.2f}")
PY
fi
