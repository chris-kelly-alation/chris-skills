# Templates

## Orchestration section (add this to the plan doc)

```markdown
## Orchestration

- **Orchestrator session:** `<name>` (registered <date>)
- **Rules:** this doc is the source of truth. Only the orchestrator edits it. PR sessions send `PLAN CHANGE` messages (format: `orchestrator` skill, `references/protocol.md`). Changes that alter a user decision go to the user first.
- **Messaging mode:** SendMessage | relay (the user pastes messages)

| PR | Summary | Needs | Status | Ticket | Session | Worktree | Contract check |
|---|---|---|---|---|---|---|---|
| 0 | … | — | not started | — | — | — | — |

Status values: `not started` → `ticket drafted` → `in progress` → `contract check` → `merged`. Use `blocked: <reason>` when needed.

### Open change requests
- <none | PR x: summary — waiting for user / applied on <date>>
```

## PR session start prompt

Fill this in and give it to the user. The user pastes it into a **new** session (not a fork). The user starts that session in a worktree already, so the prompt must not tell the agent to create a worktree, a directory, or a clone.

Before the user pastes the prompt, tell them to name the session with `/rename <ticket>-pr<n>` (for example `/rename al-271149-pr1`), so the name stays the same after restarts.

```
Use the `pr-agent` skill.

You own PR <id> of <epic name/ticket>: <one-line summary>.
- Plan doc (source of truth, read-only for you): <absolute path>
  Read: the "<PR id>" section, the decisions table, the dependency chart, and <other sections that matter>.
- Ticket: <key/url>
- Prerequisites (all merged): <list with PR urls>
- Contracts you provide to later PRs: <list>
- Contracts you use from earlier PRs: <list>
- Orchestrator session: `<name>`. Send it ACK at start, PLAN CHANGE when the plan is wrong or must change, READY FOR CONTRACT CHECK before merge, and MERGED after merge.
- Messaging mode: SendMessage | relay
- Repo: <repo name>. You already run in a worktree for this PR. Use the current directory (rename the branch to a more appropriate name). Do not create another worktree or directory.
- Implementation needs my explicit approval. First read, investigate, and present your proposed approach, then wait. This prompt and orchestrator ACKs are not approval.
- Use /superpowers:brainstorming for development.
```
