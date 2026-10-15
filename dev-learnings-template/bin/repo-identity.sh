#!/usr/bin/env bash
# repo-identity.sh — resolve the current git repo to its learnings namespace.
#
# Keys learnings by the *normalized git origin URL*, not the filesystem path,
# so every worktree and every coworker's clone of the same repo resolves to
# the same entry. Run from inside a work repo. Prints JSON to stdout.
#
# Store location is $DEV_LEARNINGS_HOME, defaulting to ~/.claude/dev-learnings.

set -euo pipefail
STORE="${DEV_LEARNINGS_HOME:-$HOME/.claude/dev-learnings}"
origin="$(git remote get-url origin 2>/dev/null || true)"

if [ -z "$origin" ]; then
  printf '{"error": "no-origin", "store": "%s"}\n' "$STORE"
  exit 0
fi

python3 - "$origin" "$STORE" <<'PY'
import json, re, sys, os

origin, store = sys.argv[1], sys.argv[2]

def normalize(url):
    u = url.strip()
    u = re.sub(r'\.git$', '', u)
    # scp-like syntax: git@host:org/repo -> host/org/repo
    m = re.match(r'^[\w.-]+@([^:]+):(.+)$', u)
    if m:
        return f"{m.group(1).lower()}/{m.group(2)}"
    # scheme://[user@]host[:port]/path -> host/path
    m = re.match(r'^[a-zA-Z][\w+.-]*://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$', u)
    if m:
        return f"{m.group(1).lower()}/{m.group(2)}"
    return u.lower()

key = normalize(origin)
reg_path = os.path.join(store, "registry.json")
reg = {}
if os.path.exists(reg_path):
    with open(reg_path) as f:
        reg = json.load(f)

entry = reg.get("repos", {}).get(key)
out = {"origin": origin, "key": key, "store": store, "registered": bool(entry)}
if entry:
    out["namespace"] = entry["namespace"]
    out["stacks"] = entry.get("stacks", [])
print(json.dumps(out, indent=2))
PY
