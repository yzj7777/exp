#!/usr/bin/env bash
# OPT-IN installer: registers the Ralph Stop hook into .claude/settings.json
# so that a plain interactive 'claude' session in this repo automatically
# re-feeds the research prompt after every answer (same mechanism as the
# official ralph-loop plugin), until "DONE" is printed or the cap is hit.
# Remove the hook later by deleting the "Stop" entry from .claude/settings.json.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT=$(pwd)
python3 - "$ROOT" <<'PY'
import json, os, sys
root = sys.argv[1]
p = os.path.join(root, ".claude", "settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
cfg = {}
if os.path.exists(p):
    with open(p) as f:
        cfg = json.load(f)
# Claude Code's default Stop-hook block cap is 8; raise it so the loop can run
cfg.setdefault("env", {})["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"] = "50"
hook_cmd = f"{root}/self_loop/claude-code-kit/hooks/ralph-stop.sh"
stop = cfg.setdefault("hooks", {}).setdefault("Stop", [])
existing = {h.get("command", "") for g in stop for h in g.get("hooks", [])}
if hook_cmd not in existing:
    stop.append({"matcher": "", "hooks": [{"type": "command", "command": hook_cmd}]})
with open(p, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print(f"Ralph Stop hook installed in {p}")
print("Now: export ANTHROPIC_API_KEY=sk-... && claude   -> just state your topic.")
print("Stop the loop anytime with Esc; reset its counter with: rm /tmp/claude-ralph/counter")
PY
