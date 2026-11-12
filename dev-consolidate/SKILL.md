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
  "consolidate alation-ui").
- **dry-run** — when the user says dry-run / preview / "what would you do":
  run every pass, produce the report, write nothing, delete nothing, and do not
  commit.

Tree root: `~/.agents/docs`. Rules for the docs: `~/.agents/docs/writing-docs.md`
(read it first). The checker is `scripts/check_tree.py` in this skill's
directory. Run it as `python3 -I <skill dir>/scripts/check_tree.py`; it reads
`--root` (default `~/.agents/docs`) and `--agents-md` (default
`~/.agents/AGENTS.md`). Each finding is one line: `<level> <kind> <path>: <detail>`.

There is no lock. Concurrent runs are not supported.

## Passes

Run in order.

1. **File the inbox.** Read each file in `~/.agents/docs/inbox/`.
   - `learning` → the right doc, as a one-line rule. Promotion rule: a lesson
     that spans repos on one stack goes to that stack doc; one that spans repos
     with no common stack goes to `core`; a lesson for one repo goes to that repo
     doc. Do not promote on one data point. If two repos have opposing
     conventions, keep both repo-local. When you promote, remove the redundant
     copies from the repo docs.
   - `stale-doc` → check the claim against the code, then fix the doc.
   - `epic-complete` → add each decision (one line: date, reason, ticket or PR
     link) and the new entry-point pointers to the feature doc under
     `projects/`, and add the work to its Prior work section. Then mark the
     listed artifacts as ready to delete (pass 6).
   - Delete each inbox file after you file it.
   - Keep doc content to what `writing-docs.md` allows: no step lists, no
     status, no line-number pointers, no secrets.

2. **Limits.** Run the checker. Flag docs over 150 lines (`over-soft`). Split a
   doc over 300 lines (`over-hard`) along its `##` headings: the parent keeps
   its name and becomes a hub with one line per child. Move rules; do not
   rewrite them. If a doc cannot be split cleanly, report it and fail the run.

3. **Structure.** Run the checker. Fix every `broken-link`, `orphan`, and
   `hub-missing-child`. The checker finds orphans by walking from the
   `AGENTS.md` index. When a hub is not reachable (for example a new project
   hub), add or change an index line in `~/.agents/AGENTS.md`. Edit only
   outside the `<!-- dispatch:*:begin -->` … `<!-- dispatch:*:end -->` blocks,
   and never change a byte inside them. Before each edit, copy the file to
   `~/.agents/docs/.agents-md-backups/AGENTS.md.<timestamp>` and keep only the
   last 10 backups. Index paths are absolute (`~/.agents/docs/...`). If the
   index grows over the limit, move the repo and stack lines to a listing doc.

4. **Pointers.** Run the checker with `--pointers`. It checks each
   `` `<repo>:<path>` `` pointer on the default branch through `gh api`, with no
   local clone. For a `broken-pointer`, find the commit that removed or renamed
   the path with `gh api repos/<org>/<name>/commits?path=<path>`. Repair the
   pointer only when the rename is unambiguous. Otherwise mark the doc for
   review. Only docs with a broken pointer or a `stale-doc` entry get a deeper
   read. Never re-summarize the whole tree. A `warn` from a failed `gh` call is
   not a broken pointer; report it.

5. **Lint.** Run the checker. Report every `lint` and `space-in-name` finding:
   "as of" text, status words, line pointers, long tables, and anything that
   looks like a secret. Report; do not auto-edit. A secret is the most urgent
   finding: tell the user at once and do not copy it.

6. **Artifacts.** List the files in `~/.agents/artifacts/` in two lists:
   - **Ready to delete:** files whose decisions are already committed to a
     feature doc (from pass 1 in this run or an earlier one). Delete a file
     only when its decisions are committed, and only after the user confirms in
     this run. This is the only way an artifact is deleted.
   - **Review:** files older than 30 days whose decisions are not lifted. Never
     delete these, and never delete a file only because it is older than 30
     days. Show each file with its decisions table (or "no decisions found") so
     the user can lift the decisions, mark the file as having none, or leave it.
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
the commit holds only doc changes.

## Notes

- Promotion goes toward the most general tier the evidence supports, and no
  further. One repo is not evidence of universality.
- Prefer merging near-duplicates and deleting stale rules over accumulating.
  Decisions in feature docs are history: never remove one because it is old. A
  reversed decision gets a new dated line.
- Docs orient; code decides. When a doc and the code disagree, the code wins.
