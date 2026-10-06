# chris-skills

Agent skills (SKILL.md format) for Claude Code, Codex, and other tools that read `~/.agents/skills`.

| Skill | Purpose |
|---|---|
| `orchestrator` | Coordinate a multi-PR epic across separate agent sessions |
| `pr-agent` | Own one PR of an epic that an orchestrator coordinates |
| `monitor-pr` | Watch a PR's CI checks, investigate failures, propose fixes |

## Install

```bash
git clone git@github.com:chris-kelly-alation/chris-skills.git ~/chris-skills
mkdir -p ~/.agents/skills
for s in orchestrator pr-agent monitor-pr; do ln -s ~/chris-skills/$s ~/.agents/skills/$s; done
```

Use `git pull` to get updates. `orchestrator` and `pr-agent` work as a pair. They use Claude Code tools (`SendMessage`, `ListAgents`, subagents) and have a manual "relay mode" for other tools.
