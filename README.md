# chris-skills

Agent skills (SKILL.md format) for Claude Code, Codex, and other tools that read `~/.agents/skills`.

| Skill | Purpose |
|---|---|
| `orchestrator` | Coordinate a multi-PR epic across separate agent sessions |
| `pr-agent` | Own one PR of an epic that an orchestrator coordinates |
| `team-collaboration/` | `team-orchestrator` + `team-task-agent`: run one epic with several engineers through Slack. See `team-collaboration/README.md` |
| `monitor-pr` | Watch a PR's CI checks, investigate failures, propose fixes |
| `dev-start` | Load stored development learnings for the current repo |
| `dev-wrapup` | Capture new learnings into the repo's inbox at the end of work |
| `dev-consolidate` | Fold inboxes into curated learnings and promote shared lessons |

The three `dev-*` skills need a learnings store. `dev-learnings-template/` is an
empty one; see its README to set it up (default location `~/.claude/dev-learnings`).

## Install

```bash
git clone git@github.com:chris-kelly-alation/chris-skills.git ~/chris-skills
mkdir -p ~/.agents/skills
for s in orchestrator pr-agent monitor-pr dev-start dev-wrapup dev-consolidate; do ln -s ~/chris-skills/$s ~/.agents/skills/$s; done
```

Use `git pull` to get updates. `orchestrator` and `pr-agent` work as a pair. They use Claude Code tools (`SendMessage`, `ListAgents`, subagents) and have a manual "relay mode" for other tools.

The team skills are in `team-collaboration/` and install from there. See `team-collaboration/README.md`.
