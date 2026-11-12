# Writing docs

Read this before you add or change a doc under `~/.agents/docs/`. The tree is for agents. Docs orient;
code decides. If a doc disagrees with the code, trust the code and write a `stale-doc` inbox entry.

## Layout

| Path | Holds |
|---|---|
| `~/.agents/docs/core.md`, `core/<topic>.md` | Universal rules. Core is a hub. |
| `~/.agents/docs/stacks/<stack>.md`, `stacks/<stack>/<topic>.md` | Rules for one stack. |
| `~/.agents/docs/repos/<repo>.md`, `repos/<repo>/<topic>.md` | Rules for one repo. |
| `~/.agents/docs/projects/<project>.md`, `projects/<project>/<feature>.md` | One project and its features. |
| `~/.agents/docs/reference/<topic>.md` | Cross-cutting how-to (dev cluster, dev tenants). |
| `~/.agents/docs/inbox/` | Raw capture. Git-ignored. One file per entry. |

Plans and specs are not docs. They live in `~/.agents/artifacts/` and are not part of the tree.

## Limits and branching

- Soft limit: 150 lines per doc. Hard limit: 300 lines. `AGENTS.md` has the same limits, counted outside
  its `dispatch:*` blocks. Inbox entries and `artifacts/` do not count.
- A doc `X.md` that grows past the soft limit keeps its name and becomes a hub. Move the detail into
  children under `X/` (`X/<topic>.md`). Split along the existing `##` headings. Move rules; do not
  rewrite them.
- The hub links to every child with a one-line description. A doc that no link reaches is an orphan.
- Link between docs with relative links, for example `[testing](core/testing.md)`. Use absolute paths
  (`~/.agents/docs/...`) only in `AGENTS.md`, in the `stale-doc` rule, and in this file. Agents run in
  worktrees, so a relative path in an instruction resolves against the wrong directory.
- Do not use spaces in file names.

## What a doc may contain

A doc holds what the code cannot say.

| Allowed | Not allowed |
|---|---|
| Entry points: `repo:path`, and a symbol name where to start reading | Step-by-step "how it works" |
| Why: a decision with a date, a one-line reason, and a ticket or PR link | Field lists, API shapes, schemas |
| Vocabulary: what a term in this area means | Date-stamped snapshots of how code looks today |
| Traps: a flag that does not gate what it seems to, a legacy product with a similar name | Status words and task checklists |
| Cross-repo shape: which repo owns which layer | Secrets of any kind |
| Manual procedures (reference docs only): commands, with a pointer to the script they run | |

Never write a secret, in a doc or in an inbox entry. Name where it lives instead (a 1Password item, a `.env` file).

## Code pointers

Every factual claim about code carries a pointer in this form:

`` `<repo>:<path>` ``, and a symbol name after it when useful. Example: `` `<repo>:libs/x/src/y.ts` `` and `` `useThing` ``. The checker reads a backticked identifier that follows a pointer on the same line as its symbol and checks that the file contains it.

- `<repo>` is the name of a hub under `~/.agents/docs/repos/`. Example: the hub `repos/my-app.md` makes `my-app` a valid prefix.
- A token is a pointer only when its prefix is a known repo hub. `localhost:4200` is not a pointer.
- A repo with no hub is written `<org>/<repo>:<path>`. The checker reads it directly from GitHub.
- Write no line numbers (`file.ts:12`, `repo:path:12`, `:12-20`). Lines move; symbols and paths survive.

## Repo hubs

A repo hub `repos/<repo>.md` starts with its title and then two lines. They replace the old registry.

```
Origin: github.com/<org>/<repo>
Stack: <name>[, <name>]
```

- `Origin` is the real GitHub name. It can differ from the hub file name. Example: the origin
  `acme/my_app` (with an underscore) can have the hub file `repos/my-app.md`.
- Each stack name links to `../stacks/<name>.md` when that doc exists.
- A repo hub links to its stack and to reference docs. It never links to project docs.
- An agent finds its repo with `git remote get-url origin`, then reads `repos/<repo>.md`.

## Decisions and Prior work

These two sections go in a feature doc under `projects/`.

- **Decisions.** A dated list. One line per decision: the decision, the reason, and a link to the
  ticket or PR where it was made. Jira and GitHub keep the full talk; plan files do not survive.
  Decisions are history, not claims about code, so never remove one because it is old. If a decision is
  reversed, add a new dated line that says so.
- **Prior work.** Who built what, with links. Example: "Sam: first version of subscriptions,
  PROJ-123 and PROJ-124." This tells a new agent that Sam worked on the feature before. Hubs record
  ownership by layer, not by person. When an `epic-complete` entry is filed, add the lifted artifact paths to
  this line (for example `artifacts: 2026-11-11-x-plan.md`). An artifact whose file name appears in a
  committed Prior work line is ready to delete.

## Capture: the inbox

Do not edit a doc to record a quick lesson. Write one file to `~/.agents/docs/inbox/`:

`YYYY-MM-DD-<repo-or-project>-<slug>.md`

If that path exists, add `-2`, `-3`, and so on before `.md`. One file per entry means two agents never write
the same file. Capture needs no lock and no commit.
`/dev-consolidate` files each entry into the right doc and deletes it. Before you write an entry, search
`~/.agents/docs/` for the idea (it may exist).

| Kind | Content |
|---|---|
| `learning` | `expected`, `actual`, `rule`, and `scope`. Scope is `repo:<name>`, `stack:<name>`, `core`, or `project:<name>`. For `repo:<name>`, `<name>` is the hub file name without `.md`, not the GitHub name. |
| `stale-doc` | The doc path, and what the code shows instead. |
| `epic-complete` | Written by `/orchestrator` when the last PR of an epic merges. Lists the decisions, the merged PRs, the tickets, and the paths of the plan and spec artifacts. |

Filing rule for a `learning`: a rule that spans repos on one stack goes to the stack doc; a rule that
spans repos with no common stack goes to core; a rule for one repo goes to the repo doc.

## After you write

Run the checker. It reports size limits, broken links, orphans, missing hub children, and lint:

```
python3 -I ~/chris-skills/dev-consolidate/scripts/check_tree.py
```

Fix every `error`. A `warn` for `over-soft` means: split the doc. Add `--pointers` to check that each
code pointer exists on the default branch.
