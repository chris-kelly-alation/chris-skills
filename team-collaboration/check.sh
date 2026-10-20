#!/usr/bin/env bash
# Structural checks for the team-collaboration skills. Run from anywhere.
set -u
cd "$(dirname "$0")"
fail=0
f() { echo "FAIL: $*"; fail=1; }

O=team-orchestrator
T=team-task-agent
P=$O/references/slack-protocol.md
files=("$O/SKILL.md" "$O/references/slack-protocol.md" "$O/references/templates.md" \
       "$O/references/verifier-prompt.md" "$T/SKILL.md" "README.md")

for x in "${files[@]}"; do [ -s "$x" ] || f "missing or empty: $x"; done
exec 2>/dev/null   # missing files are reported above; hide grep/head noise

# Frontmatter name matches directory.
for s in $O $T; do
  head -5 "$s/SKILL.md" | grep -qx "name: $s" || f "$s/SKILL.md: frontmatter name is not '$s'"
  head -5 "$s/SKILL.md" | grep -q '^description: ' || f "$s/SKILL.md: no description"
done

# The task agent's link to the shared protocol resolves.
grep -q '\.\./team-orchestrator/references/slack-protocol\.md' "$T/SKILL.md" \
  || f "$T/SKILL.md: no link to ../team-orchestrator/references/slack-protocol.md"
[ -s "$T/../team-orchestrator/references/slack-protocol.md" ] || f "shared protocol link does not resolve"

# Naming: tasks, not PRs, as work items and roles.
grep -nE '\[agent:pr-|PR <id>|pr-<id>' "${files[@]}" && f "uses PR as a work-item ID or role"

# No old transport, no custom agent types, no full MCP tool names.
grep -nE 'SendMessage|ListAgents' "${files[@]}" && f "mentions SendMessage/ListAgents"
grep -nE 'subagent_type: *"?(scout|executor|verifier)' "${files[@]}" && f "uses a custom agent type"
grep -nE 'mcp__[a-z_-]+__slack' "${files[@]}" && f "hard-codes a full MCP tool name"

# No permission words in message templates (references only).
grep -niE '\b(proceed|go ahead|start implementing)\b' "$P" "$O/references/templates.md" \
  | grep -viE 'do not|never' && f "permission word in a message template"

# Required rules are present in the protocol.
req() { grep -qiE "$2" "$1" || f "$1: missing rule: $3"; }
req "$P" '\[agent:<role>\]'                 "message header tag"
req "$P" 'robot_face'                       "processed reaction"
req "$P" 'exactly one (addressee|role)'     "one addressee for each message"
req "$P" 'Re: .*ts'                         "Re: cites message ts (restart safety)"
req "$P" 'Slack user ID'                    "trust boundary by Slack user ID"
req "$P" 'canvas'                           "canvas for long content"
req "$P" '5,000'                            "Slack message limit"
req "$P" 'relay mode'                       "relay fallback"
req "$O/SKILL.md" 'model: *"?haiku'         "scout via Explore with haiku"
req "$O/SKILL.md" 'model: *"?sonnet'        "verifier via general-purpose with sonnet"
req "$O/SKILL.md" 'status canvas'           "status canvas"
req "$O/SKILL.md" 'never relay'             "orchestrator never relays approval"
req "$T/SKILL.md" 'only your own thread'   "task agent polls only its thread"
req README.md      'ln -s'                  "install commands"
req README.md      'robot_face'             "Slack conventions"

[ "$fail" -eq 0 ] && echo OK
exit "$fail"
