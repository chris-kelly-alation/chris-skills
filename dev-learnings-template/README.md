# dev-learnings store (template)

An empty store for the `dev-start`, `dev-wrapup`, and `dev-consolidate` skills.
The store is a separate git repo, outside every work repo. Learnings are keyed
by each repo's normalized git origin URL, so all worktrees and clones of a repo
share them.

## Set up

```bash
cp -R ~/chris-skills/dev-learnings-template ~/.claude/dev-learnings
cd ~/.claude/dev-learnings && git init && git add -A && git commit -m "init store"
```

To use another location, set `DEV_LEARNINGS_HOME` to it.

## Layout

```
registry.json          normalized origin -> { namespace, stacks }
bin/repo-identity.sh   resolves the current repo to its registry entry
core.md                universal learnings (loaded for every repo)
stacks/<stack>.md      loaded for each stack tag on the repo
repos/<namespace>/
  learnings.md         compact index, always loaded
  INBOX.md             raw captures from dev-wrapup, waiting for consolidation
  detail/*.md          heavy reference, loaded only when needed
```

`repos/_example/` shows the file shapes. Copy it to `repos/<namespace>/` (or let
`dev-start` register the repo for you), then delete `_example`.

## Skills

- **dev-start**: at the start of work. Loads core, stacks, repo learnings, and inbox.
  Offers to register an unknown repo.
- **dev-wrapup**: at the end of work. Appends new learnings to the repo inbox.
- **dev-consolidate**: periodically. Folds inboxes into curated files and promotes
  lessons that recur across repos to `stacks/` or `core.md`.
