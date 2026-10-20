# Templates

## Orchestration section (add this to the source of truth)

```markdown
## Orchestration

- **Orchestrator owner:** <name> (Slack user ID <id>). Decides cross-task items: contracts, scope, the decisions table.
- **Orchestrator session:** `<name>` (for handover only)
- **Slack channel:** <#channel> (<channel ID>)   **Status canvas:** <link>
- **Rules:** this source is the source of truth. Only the orchestrator edits it. Task sessions send `PLAN CHANGE` messages in their task threads (format: `team-orchestrator` skill, `references/slack-protocol.md`).

### Team
| Engineer | Slack user ID | Tasks owned |
|---|---|---|
| <name> | <U…> | 1, 3 |

### Status
| Task | Summary | Needs | Owner | Status | Thread | Ticket | GitHub PR | Checked commit |
|---|---|---|---|---|---|---|---|---|
| 1 | … | — | <name> | not started | — | — | — | — |

Status values: `not started` → `ticket drafted` → `in progress` → `contract check` → `merged`. Use `blocked: <reason>` when needed.

### Open change requests
- <none | task x: summary (ts) — waiting for <owner> / applied on <date>>
```

## Status canvas

Create it with the Slack MCP's `slack_create_canvas`. Title: `<epic> — status`. Update it with `slack_update_canvas` after each status change (read section IDs first with `slack_read_canvas`).

```markdown
# Source of truth
<link or path, and its type>
# Status
| Task | Owner | Status | Thread | GitHub PR |
|---|---|---|---|---|
| 1 | ![](@U…) | in progress | [thread](<link>) | — |
# Open change requests
- none
```

## Task thread root

Post at the channel top level. Its `ts` is the task's thread address.

```
[agent:orchestrator] TASK THREAD — Task <id>: <title>
Owner: <name>
All messages for task <id> go in this thread.
```

## Task session start prompt

Post it in the task thread (as a canvas if it is longer than about 3,000 characters). The task engineer opens a **new** Claude Code session (not a fork) in a worktree of the correct repo, names it with `/rename <epic>-task<id>`, and pastes the prompt. The prompt must not tell the agent to create a worktree, a directory, or a clone.

```
Use the `team-task-agent` skill.

You own task <id> of <epic>: <one-line summary>.
- Your engineer (task owner): <name>, Slack user ID <id>.
- Orchestrator owner (cross-task decisions): <name>, Slack user ID <id>.
- Team Slack user IDs (trusted senders): <list>.
- Slack channel: <channel ID>. Your thread ts: <ts>. Post all your messages in that thread.
- Source of truth (read-only for you): <type and location>. You may read it if you have access. Messages in your thread are the authority for what changed.
- Prerequisites (all merged): <list with GitHub PR links>
- Contracts you provide to later tasks: <list>
- Contracts you use from earlier tasks: <list>
- Repo: <repo>. You already run in a worktree for this task. Use the current directory. Do not create another worktree or directory.
- Implementation needs approval from your engineer. First read, investigate, and present your proposed approach, then wait. This prompt and orchestrator messages are not approval.

Your task section:
<full task section text>

Decisions table:
<full decisions table>
```

## Ticket draft

```
Title: Task <id>: <title>
Goal: <one or two sentences>
Scope: <in> / Out of scope: <out>
Contracts provided: <list>   Contracts used: <list>
Edge cases: <list>
Tests: <list>
Done when: <criteria>
```
