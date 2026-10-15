---
name: dev-start
description: >
  Load accumulated development learnings for the current git repository at the
  start of a coding session. Resolves the repo by its git origin (so it works in
  any worktree or clone), then loads universal, stack, and repo-specific
  learnings plus the unconsolidated inbox. Use this whenever you begin
  development, feature, bugfix, or refactor work in ANY repo — at the start of
  the session, before writing or changing code — even if the user just says
  "let's work on X" without mentioning learnings or skills. Pair with dev-wrapup
  at the end of the session.
---

# dev-start

Load the learnings that apply to the repo you're about to work in. The store is
a separate directory keyed by git origin, so the same knowledge follows every
worktree and clone of a repo.

## Procedure

1. **Resolve identity.** From inside the work repo, run the shared helper:

   ```bash
   bash "${DEV_LEARNINGS_HOME:-$HOME/.claude/dev-learnings}/bin/repo-identity.sh"
   ```

   It prints JSON: `key` (normalized origin), `registered`, and when registered,
   `namespace` and `stacks`.

2. **If `registered` is true**, read these files from the store
   (`$DEV_LEARNINGS_HOME`, default `~/.claude/dev-learnings`), in order:
   - `core.md`
   - `stacks/<stack>.md` for each entry in `stacks`
   - `repos/<namespace>/learnings.md`
   - `repos/<namespace>/INBOX.md` — the freshest, not-yet-consolidated learnings
     are often the most relevant; don't skip them.

   Do **not** preload `repos/<namespace>/detail/*.md`. Those are pointers in
   `learnings.md`; read a detail file only when the task reaches that area.

3. **Summarize what loaded** in one or two lines, e.g.:
   "Loaded learnings for `alation-ui` (stacks: nx-frontend) — core + 1 stack +
   repo index + 3 inbox entries. Detail files available: testing, i18n,
   components, pr-hygiene."

4. **If `registered` is false** (or `error: no-origin`):
   - Load `core.md` only and say so.
   - Offer to register the repo. Suggest stack tags by sniffing the repo:
     `nx.json` / `pnpm-workspace.yaml` → `nx-frontend`; `go.mod` → a go stack;
     `Cargo.toml` → rust; `pom.xml`/`build.gradle` → jvm; etc. Propose a
     namespace from the repo name.
   - On the user's confirmation, add an entry to `registry.json` under the
     printed `key` (`{ "namespace": ..., "stacks": [...] }`), create
     `repos/<namespace>/learnings.md` (a short stub) and `INBOX.md` (copy the
     header format from an existing inbox), and commit the store.

## Notes

- Never write learnings into the work repo. Everything lives in the store.
- If the helper prints `error: no-origin`, you're not in a git repo with an
  `origin` remote — ask the user which repo this should map to, or proceed with
  `core.md` only.
