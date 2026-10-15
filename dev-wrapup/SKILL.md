---
name: dev-wrapup
description: >
  Capture reusable learnings from a finished development session into the
  learnings store. Reflects on what was non-obvious or surprising during the
  work, filters out one-offs and anything already documented, and appends only
  genuine new takeaways to the repo's inbox. Use this whenever development work
  wraps up — after a feature, bugfix, refactor, or PR is done, or when the user
  says they're finished, "wrapping up", "done with this", or asks to record /
  save / capture learnings. Fast and append-only; consolidation happens later
  via dev-consolidate.
---

# dev-wrapup

Record what this session taught you, cheaply. The goal is a low-friction capture
so learnings actually get written down — placement and deduplication are
dev-consolidate's job, not yours.

## Procedure

1. **Resolve identity** with the shared helper (same as dev-start):

   ```bash
   bash "${DEV_LEARNINGS_HOME:-$HOME/.claude/dev-learnings}/bin/repo-identity.sh"
   ```

   If the repo isn't registered, offer to register it (see dev-start) before
   capturing — there's nowhere to file otherwise.

2. **Reflect on the session.** Look for learnings that are all three of:
   - **non-obvious** — a surprise, a gotcha, a counterintuitive cause, a
     convention you only discovered by tripping on it;
   - **reusable** — likely to matter again, to you or a coworker;
   - **not already captured** — dev-start loaded the existing learnings and
     inbox into this same context, so check against them and skip anything
     that's already there.

   Explicitly discard: one-off incidents, project-specific trivia with no future
   value, and restatements of things already in core/stack/repo learnings.

3. **Write each kept learning** to `repos/<namespace>/INBOX.md`, appended below
   the marker line, in the inbox format:

   ```
   ## YYYY-MM-DD — short title
   - expected: ...
   - actual: ...
   - rule: ...
   - scope: candidate-core | candidate-stack:<name> | repo
   ```

   Set `scope` to your best guess — `candidate-core` if it looked
   tool/language-agnostic, `candidate-stack:<name>` if it's about the stack, else
   `repo`. It's only a hint; dev-consolidate makes the real call.

4. **Commit the store** with a message like
   `wrapup(<namespace>): +N learning(s)`.

5. **Report** what you captured. Zero is a perfectly good answer — say "nothing
   new worth recording this session" rather than inventing filler. Padding the
   store with low-value entries is the main way it rots.

## Notes

- Append-only. Don't edit `learnings.md`, `detail/`, `stacks/`, or `core.md`
  here — that's consolidation.
- Keep entries terse but self-contained: a reader (or the consolidator) should
  understand the rule without the session context.
