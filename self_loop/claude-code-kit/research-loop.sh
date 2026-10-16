#!/usr/bin/env bash
# Ralph-style HEADLESS research loop for Claude Code.
# Fresh model context every iteration + persistent state on disk = keep digging
# a topic far beyond any single context window ("infinite" research).
#
# Usage:
#   TOPIC="quantum error correction" MAX_ITERS=20 ./self_loop/claude-code-kit/research-loop.sh
#   ./self_loop/claude-code-kit/research-loop.sh "quantum error correction"
#
# Env vars:
#   TOPIC        research topic (or pass as $1)
#   MAX_ITERS    max iterations, default 20
#   MODEL        optional model name (e.g. claude-sonnet-4-5)
#   SKIP_PERMS   default 1 (headless tool use allowed); set 0 to disable
#   SLEEP        seconds between iterations, default 5
set -euo pipefail
cd "$(dirname "$0")"

TOPIC="${TOPIC:-${1:-}}"
[ -n "$TOPIC" ] || { echo "Usage: TOPIC='<your topic>' ./self_loop/claude-code-kit/research-loop.sh"; exit 1; }
MAX="${MAX_ITERS:-20}"
SLEEP="${SLEEP:-5}"
MODEL_ARGS=()
[ -n "${MODEL:-}" ] && MODEL_ARGS+=(--model "$MODEL")
PERM_ARGS=()
[ "${SKIP_PERMS:-1}" = "1" ] && PERM_ARGS+=(--dangerously-skip-permissions)

SLUG=$(echo "$TOPIC" | tr ' /()&' '----' | cut -c1-48)
DIR="research/$SLUG"
mkdir -p "$DIR"
[ -f "$DIR/todo.md" ]     || printf '# Open questions for: %s\n\n- %s\n' "$TOPIC" "$TOPIC" > "$DIR/todo.md"
[ -f "$DIR/progress.md" ] || printf '# Findings: %s\n\n' "$TOPIC" > "$DIR/progress.md"

# --- bootstrap: verify claude is actually usable before burning iterations ---
if ! timeout 90 claude -p "Reply with exactly: OK" > "$DIR/_bootstrap.log" 2>&1; then
  {
    echo "ERROR: 'claude -p' bootstrap failed. Common causes:"
    echo "  1. No API key:   export ANTHROPIC_API_KEY=sk-..."
    echo "  2. Not logged in: run 'claude' once interactively to authenticate"
    echo "  3. Network egress: api.anthropic.com must be reachable from this machine"
  } >&2
  head -5 "$DIR/_bootstrap.log" >&2 2>/dev/null || true
  exit 2
fi
rm -f "$DIR/_bootstrap.log"

for i in $(seq 1 "$MAX"); do
  echo "===== iteration $i/$MAX  $(date -Is) ====="
  sed -e "s|{TOPIC}|$TOPIC|g" -e "s|{STATE_DIR}|$DIR|g" ralph/PROMPT.md > "$DIR/prompt-$i.md"
  timeout 3600 claude -p "${MODEL_ARGS[@]}" "${PERM_ARGS[@]}" "$(cat "$DIR/prompt-$i.md")" \
    > "$DIR/iteration-$i.md" 2>&1 || echo "WARNING: iteration $i exited non-zero; see $DIR/iteration-$i.md" >&2

  if grep -qE 'Invalid API key|authentication|rate limit|overloaded' "$DIR/iteration-$i.md" 2>/dev/null; then
    echo "ERROR: auth/rate error in iteration $i — stopping. tail of output:" >&2
    tail -5 "$DIR/iteration-$i.md" >&2
    exit 2
  fi
  if grep -qxE 'DONE' "$DIR/iteration-$i.md"; then
    echo "DONE detected at iteration $i. Results in $DIR/"
    exit 0
  fi
  echo "(no DONE yet — sleeping ${SLEEP}s before next iteration)"
  sleep "$SLEEP"
done
echo "Reached MAX_ITERS=$MAX without DONE. State preserved in $DIR/ — re-run the same command to continue."
