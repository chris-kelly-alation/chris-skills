---
name: dev-wrapup
description: >
  Capture reusable learnings from a finished development session into the docs
  inbox. Reflects on what was non-obvious or surprising during the work,
  filters out one-offs and anything already documented, and writes one inbox
  file per genuine new takeaway. Use this whenever development work wraps up —
  after a feature, bugfix, refactor, or PR is done, or when the user says
  they're finished, "wrapping up", "done with this", or asks to record / save /
  capture learnings. Fast and write-only; no git step. Consolidation happens
  later via dev-consolidate.
model: sonnet
---

# dev-wrapup

Record what this session taught you, cheaply. The goal is a low-friction capture
so learnings actually get written down. Placement and deduplication are
dev-consolidate's job, not yours.

The docs tree is at `~/.agents/docs/`. Entries go to `~/.agents/docs/inbox/`.
That folder is git-ignored, so capture needs no commit and no lock.

## Procedure

1. **Find the repo name.** Take the basename of `git remote get-url origin`, and
   remove a trailing `.git`. Check that a hub `~/.agents/docs/repos/<name>.md`
   exists. If it does not, look for a hub whose `Origin:` line names this repo
   (the hub file name can differ from the GitHub name):

   ```bash
   grep -l "^Origin:.*/<name>$" ~/.agents/docs/repos/*.md
   ```

   If no hub matches, use `scope: core` and write the repo name in the entry.
   If the work belongs to a project (not one repo), use `scope: project:<name>`.

2. **Reflect on the session.** Look for learnings that are all three of:
   - **non-obvious** — a surprise, a gotcha, a counterintuitive cause, a
     convention you only discovered by tripping on it;
   - **reusable** — likely to matter again, to you or a coworker;
   - **not already captured** — search the docs for your keywords before you
     write (you may not have read them this session):

     ```bash
     grep -ril "<keyword>" ~/.agents/docs
     ```

     Skip anything that a doc or an inbox file already says.

   Explicitly discard: one-off incidents, project-specific trivia with no future
   value, and restatements of things already in core, stack, or repo docs.

3. **Write one file per kept entry** at
   `~/.agents/docs/inbox/YYYY-MM-DD-<repo-or-project>-<slug>.md`. One file per
   entry means two agents never write the same file. Each file holds plain
   `key: value` lines.

   | Key | When | Value |
   |---|---|---|
   | `kind` | always | `learning`, `stale-doc`, or `epic-complete` |
   | `scope` | always | `repo:<name>`, `stack:<name>`, `core`, or `project:<name>` |
   | `expected`, `actual`, `rule` | `learning` | the lesson |
   | `doc`, `code shows` | `stale-doc` | the stale doc and what the code shows |

   A `learning` looks like this:

   ```
   kind: learning
   scope: repo:<name>
   expected: what you thought would happen
   actual: what happened
   rule: the rule to follow next time
   ```

   Set `scope` to your best guess. It is only a hint; dev-consolidate makes the
   real call. Use `stale-doc` when a doc disagrees with the code; the code wins.
   Do not write `epic-complete` here. The orchestrator writes it.

4. **Report** what you captured. Zero is a perfectly good answer. Say "nothing
   new worth recording this session" rather than inventing filler. Padding the
   inbox with low-value entries is the main way the docs rot.

## Notes

- Write-only. Do not edit docs under `~/.agents/docs/` here. That is
  consolidation. Do not run `git` in the docs repo.
- Never write a secret in an entry. Name where it lives (a password manager
  item, a `.env` file) instead.
- Keep entries terse but self-contained: a reader (or the consolidator) should
  understand the rule without the session context.
