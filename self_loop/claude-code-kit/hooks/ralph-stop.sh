#!/usr/bin/env bash
# Ralph Stop hook (INTERACTIVE mode — the same mechanism as the official
# ralph-loop plugin): after every completed answer, either
#   - let Claude stop (its last output ended with a lone "DONE" line), or
#   - block the stop and re-inject the research instruction, up to RALPH_MAX times.
# Claude Code sends hook JSON on stdin (we use transcript_path).
set -uo pipefail
STATE="${RALPH_STATE:-/tmp/claude-ralph}"
MAX="${RALPH_MAX:-20}"
mkdir -p "$STATE"
COUNTER="$STATE/counter"
input="$(cat 2>/dev/null || true)"

# 1) completion-promise check on the latest assistant message of the transcript
done_flag=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    tp = d.get("transcript_path", "")
    last_done = False
    if tp:
        with open(tp) as f:
            lines = f.readlines()[-40:]
        for line in reversed(lines):
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("type") != "assistant":
                continue
            content = rec.get("message", {}).get("content", [])
            text = "\n".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
            last_done = "DONE" in [l.strip() for l in text.splitlines()]
            break
    print("1" if last_done else "0")
except Exception:
    print("0")
')
if [ "$done_flag" = "1" ]; then
  rm -f "$COUNTER"
  echo "DONE detected — Ralph loop finished." >&2
  exit 0
fi

# 2) iteration cap
n=$(cat "$COUNTER" 2>/dev/null || echo 0)
n=$((n + 1))
echo "$n" > "$COUNTER"
if [ "$n" -gt "$MAX" ]; then
  echo "Ralph iteration cap ($MAX) reached — stopping. Reset with: rm $COUNTER" >&2
  exit 0
fi

printf '{"decision":"block","reason":"Ralph iteration %d/%d: keep digging the research topic of this session. Read the latest state under research/<topic>/ (progress.md, todo.md), do exactly one more iteration: pick the most promising open question, research it, append findings with sources to progress.md, update todo.md. Output the single word DONE as your LAST line only when the topic is genuinely exhausted."}' "$n" "$MAX"
exit 0
