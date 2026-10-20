# Team collaboration skills

Two skills to run one epic with a team of engineers. Each engineer uses their own machine and Claude Code account. The sessions talk through Slack.

| Skill | Who runs it |
|---|---|
| `team-orchestrator` | One engineer (the **orchestrator owner**). Owns the plan and checks contracts. |
| `team-task-agent` | Every engineer, one session for each task they own. A task is sized as one GitHub PR. |

## Prerequisites (every engineer)

- Claude Code.
- The Slack MCP, connected, with access to the epic channel.
- If the source of truth is Confluence or Jira: the Atlassian MCP, for the orchestrator owner. (Other engineers do not need it.)

## Install (every engineer)

Install both skills on every machine. `team-task-agent` reads the protocol file from `team-orchestrator`.

```bash
git clone git@github.com:chris-kelly-alation/chris-skills.git ~/chris-skills   # or: cd ~/chris-skills && git pull
mkdir -p ~/.claude/skills
for s in team-orchestrator team-task-agent; do ln -s ~/chris-skills/team-collaboration/$s ~/.claude/skills/$s; done
```

Use `~/.agents/skills` instead of `~/.claude/skills` if your tools read that directory. Run `bash ~/chris-skills/team-collaboration/check.sh` after you edit the skills.

## Setup checklist (target: less than one hour)

**Orchestrator owner**
1. Create a Slack channel for the epic, for example `#hack-<idea>-coord`. Invite the team.
2. Have the plan ready: tasks with IDs, a dependency chart, a decisions table, one section for each task. It can be a Markdown file, a Confluence page, a Jira epic, or another doc.
3. Start a Claude Code session, run `/rename <epic>-orchestrator`, and say: "Use the `team-orchestrator` skill. The source of truth is `<location>`. The channel is `#<channel>`."
4. Answer the setup questions: team names, which tasks each person owns.

**Each task engineer**
1. When the orchestrator posts a task thread for your task, open the start prompt in it.
2. Open a **new** session (not a fork) in a worktree of the correct repo. Run `/rename <epic>-task<id>`. Paste the start prompt.
3. Your agent posts `ACK` in the thread. That is the smoke test.

## Slack conventions

- **One thread for each task.** All agent messages for a task go in its thread.
- **Agent messages start with `[agent:<role>]`** (`orchestrator` or `task-<id>`). Agents post as you, so the tag is the only way to tell agent from human. Do not start your own messages with `[agent:`.
- **Humans post untagged.** Untagged messages are context or decisions.
- **To approve implementation of your task**, tell your agent in your session, or post in your task thread: `User approval: implementation approved — <scope>`. Only the task owner can approve. The orchestrator never relays approval.
- **The `:robot_face:` reaction** means "this agent processed the message." Do not use it yourself in this channel.
- **Status** is in the status canvas linked at the top of the channel.

## Troubleshooting

| Problem | Fix |
|---|---|
| The Slack MCP does not work in a session | The agent uses relay mode: it prints each message, and you post it in the correct thread. Paste replies back to it. |
| An agent did not act on a message | Remove its `:robot_face:` reaction, and delete its reply to that message if one exists. It processes the message again on the next poll. |
| An agent seems stopped | Check that its `/loop` still runs. Start it again with `/loop` if not. |
| The orchestrator's context is too long, or a new person becomes the owner | Ask the orchestrator for a handover. It updates the source and the status canvas, and gives a start prompt for the new session. |
| Someone outside the team posts in the channel | Agents ignore them. They act only on the Slack user IDs recorded at setup. |
