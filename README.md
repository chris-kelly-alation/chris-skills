# chris-skills

Agent skills (SKILL.md format) for Claude Code, Codex, and other tools that read `~/.agents/skills`.

| Skill | Purpose |
|---|---|
| `orchestrator` | Coordinate a multi-PR epic across separate agent sessions |
| `pr-agent` | Own one PR of an epic that an orchestrator coordinates |
| `team-collaboration/` | `team-orchestrator` + `team-task-agent`: run one epic with several engineers through Slack. See `team-collaboration/README.md` |
| `monitor-pr` | Watch a PR's CI checks, investigate failures, propose fixes |
| `dev-wrapup` | Capture new learnings into the docs inbox at the end of work |
| `dev-consolidate` | File the inbox into the docs tree and audit the tree (limits, links, pointers, lint) |

The two `dev-*` skills work on a docs tree, a git repo of small linked markdown
docs. `docs-template/` is an empty one. Copy it to `~/.agents/docs`, run `git init`
there, and read its `writing-docs.md`. Point your `AGENTS.md` at the hub docs, so
an agent reads the repo doc before it works in a repo. There is no `dev-start`
skill: the index in `AGENTS.md` replaces it.

## Install

```bash
git clone git@github.com:chris-kelly-alation/chris-skills.git ~/chris-skills
mkdir -p ~/.agents/skills
for s in orchestrator pr-agent monitor-pr dev-wrapup dev-consolidate; do ln -s ~/chris-skills/$s ~/.agents/skills/$s; done
```

Use `git pull` to get updates. `orchestrator` and `pr-agent` work as a pair. They use Claude Code tools (`SendMessage`, `ListAgents`, subagents) and have a manual "relay mode" for other tools.

The team skills are in `team-collaboration/` and install from there. See `team-collaboration/README.md`.
