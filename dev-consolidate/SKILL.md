---
name: dev-consolidate
description: >
  Garden and audit the agent docs tree at ~/.agents/docs: file inbox entries
  into the right docs, enforce size limits, check links, reachability, code
  pointers, and lint, and clean up finished plan artifacts. Runs across the
  whole tree by default (optionally one repo or project). Use this periodically
  — when the user wants to consolidate, clean up, garden, audit, compact, or
  process inbox learnings, or every several sessions. Supports a dry-run that
  reports the plan without writing.
---

# dev-consolidate

The periodic, judgment-heavy pass kept off the hot path. It files raw capture
into the docs tree and audits the tree. Default scope is the **whole tree**.
Seeing everything is what lets you detect that a lesson recurs across repos and
belongs in a shared doc.

Modes:
- **all** (default) — no argument.
- **single repo or project** — when the user names one (for example
  "consolidate alation-ui"). Pass 1 files only inbox entries whose `scope` is
  `repo:<name>` or `project:<name>` for that name; other entries stay in the
  inbox. Report only checker findings whose path is `repos/<name>.md`,
  `repos/<name>/`, or starts with `projects/<name>`. In pass 6, list only
  artifacts named in a Prior work line of those docs, and skip the Review list.
- **dry-run** — when the user says dry-run / preview / "what would you do":
  run every pass, produce the report, write nothing, move nothing, delete
  nothing, and do not commit.

Tree root: `~/.agents/docs`. All doc rules (limits, split rule, allowed content,
pointer form, inbox format, filing rule, secrets) are in
`~/.agents/docs/writing-docs.md`. Read it first. This file holds only the
procedure.

There is no lock. Concurrent runs are not supported.

## Passes

Run in order. Right after pass 1, run the checker once:
`python3 -I <skill dir>/scripts/check_tree.py --pointers` (it needs `gh`). Keep
the output. Passes 2 to 5 work from it by finding kind; each line is
`<level> <kind> <path>: <detail>`. Do not run it again for each pass. After you
split docs or edit `AGENTS.md`, run it once more without `--pointers` to confirm
the structure findings are gone.

1. **File the inbox.** Read each file directly in `~/.agents/docs/inbox/`.
   - `learning` → the right doc, as a one-line rule, by the filing rule. Do not
     promote on one data point. If two repos have opposing conventions, keep
     both repo-local. When you promote, remove the redundant copies.
   - `stale-doc` → check the claim against the code, then fix the doc.
   - `epic-complete` → add the decisions and entry-point pointers to the feature
     doc under `projects/`, and add the work to its Prior work line with the
     lifted artifact paths, as `writing-docs.md` says.
   - Move each filed entry to `~/.agents/docs/inbox/.filed/<run-timestamp>/`.
     Delete that folder only after this run's commit succeeds. If the commit
     fails, leave the folder and say so in the report.

2. **Limits** (`over-soft`, `over-hard`). Split by the rule in `writing-docs.md`.
   If a doc cannot be split cleanly, report it and fail the run.

3. **Structure** (`broken-link`, `orphan`, `hub-missing-child`). Fix each. The
   checker finds orphans by walking from the `AGENTS.md` index. When a hub is not
   reachable (for example a new project hub), add or change an index line in
   `~/.agents/AGENTS.md`. Edit only outside the
   `<!-- dispatch:*:begin -->` … `<!-- dispatch:*:end -->` blocks, and never
   change a byte inside them. Before each edit, copy the file to
   `~/.agents/docs/.agents-md-backups/AGENTS.md.<timestamp>` and keep only the
   last 10 backups. Index paths are absolute (`~/.agents/docs/...`). If the
   index grows over the limit, move the repo and stack lines to a listing doc.

4. **Pointers** (`broken-pointer`). For a missing path, find the commit that
   removed or renamed it with `gh api repos/<org>/<name>/commits?path=<path>`.
   Repair the pointer only when the rename is unambiguous. Otherwise mark the
   doc for review. For a missing symbol, search the file and repair only when the
   new name is unambiguous. Only docs with a broken pointer or a `stale-doc`
   entry get a deeper read. Never re-summarize the whole tree. A `warn` from a
   failed `gh` call is not a broken pointer; report it.

5. **Lint** (`lint`, `space-in-name`). Report every finding. Do not auto-edit.
   A secret is the most urgent finding: tell the user at once and do not copy it.

6. **Artifacts.** List the files in `~/.agents/artifacts/` in two lists:
   - **Ready to delete:** an artifact whose file name appears in a Prior work
     line that is committed in the docs repo (`grep -rn "<file name>"
     ~/.agents/docs --include='*.md'`). A name added in this run counts only
     after the run's commit succeeds. Delete a file only when it is in this list
     and the user confirms in this run. This is the only way an artifact is
     deleted.
   - **Review:** files older than 30 days that are not in a committed Prior work
     line. Never delete these, and never delete a file only because it is older
     than 30 days. Show each file with its decisions table (or "no decisions
     found") so the user can lift the decisions, mark the file as having none, or
     leave it.
   - Put a file in neither list when an open epic names it: an orchestrator
     plan doc with unmerged PRs, and every artifact that such a plan links to.
     To find them, read the plan docs in `~/.agents/artifacts/` and check their
     status tables for PRs that are not merged.

## Report and commit

Produce one report: entries filed, docs split, checker findings by kind, broken
pointers, artifacts in each list. In dry-run, stop here.

Otherwise make **one** commit in `~/.agents/docs` for the whole run
(`consolidate: filed N entries; split S docs; fixed F findings`), so the pass is
easy to review or revert in one step. The inbox and backups are git-ignored, so
the commit holds only doc changes. When the commit succeeds:

1. Delete `inbox/.filed/<run-timestamp>/`.
2. Ask the user to confirm the pass-6 "Ready to delete" list (now including
   names committed in this run). Delete only the files the user confirms.

## Notes

- Promotion goes toward the most general tier the evidence supports, and no
  further. One repo is not evidence of universality.
- Prefer merging near-duplicates and deleting stale rules over accumulating.
