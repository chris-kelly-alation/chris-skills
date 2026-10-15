---
name: dev-consolidate
description: >
  Garden the development learnings store: fold inbox entries into curated
  learnings, promote cross-repo recurring learnings up to shared stack/core
  files, dedupe, prune obsolete entries, push bulky detail into detail files,
  and enforce size budgets. Runs across ALL registered repos at once by default
  (optionally a single repo). Use this periodically — when the user wants to
  consolidate, clean up, garden, compact, or process inbox learnings, or every
  several sessions. Supports a dry-run that reports the plan without writing.
---

# dev-consolidate

The periodic, judgment-heavy pass kept off the hot path. Default scope is **all
registered repos at once** — seeing the whole store is what lets you detect that
a learning recurs across repos and therefore belongs in a shared file.

Modes:
- **all repos** (default) — no argument.
- **single repo** — when the user names one (e.g. "consolidate alation-ui").
- **dry-run** — when the user says dry-run / preview / "what would you do":
  produce the report in step 6 but write nothing and don't commit.

Store root is `$DEV_LEARNINGS_HOME` (default `~/.claude/dev-learnings`).

## Procedure

1. **Discover.** Read `registry.json`. Collect every repo whose
   `repos/<namespace>/INBOX.md` has entries below the marker. Silently skip
   empty inboxes. (Single-repo mode: just that one.)

2. **Load the whole store** once: `core.md`, all `stacks/*.md`, and for each
   in-scope repo its `learnings.md` + `INBOX.md` (+ `detail/*.md` as needed).
   This is the cost center — see Scaling below if it ever strains context.

3. **Cluster across repos.** Group inbox entries (and existing learnings) that
   express the same underlying lesson, including matches against already-curated
   content. Cross-repo clusters are the signal for promotion.

4. **Promote, by this rule:**
   - Cluster spans repos that **share a stack** → promote to that
     `stacks/<stack>.md`.
   - Cluster spans repos with **no common stack** → promote to `core.md`.
   - A single repo's entry tagged `candidate-core`/`candidate-stack` but seen in
     only one repo so far → keep it repo-local but leave the candidate tag noted;
     promote once a second repo corroborates it. Don't promote on one data point.
   - **Contradiction** (two repos with opposing conventions) → do **not** merge
     upward; keep both repo-local, and if useful note the divergence in each.
   - When you promote, **remove the now-redundant copies** from the individual
     repos so nothing is duplicated across tiers.

5. **Per-repo cleanup**, for each in-scope repo:
   - Merge remaining inbox entries into `learnings.md` as compact one-line rules.
   - Push any bulky specifics (long code, step-by-step) down into a
     `detail/<area>.md`, leaving a one-line pointer in `learnings.md`.
   - **Prune obsolete entries** — e.g. a stopgap whose tracking ticket has
     shipped. Pruning and rewriting are expected; this is not append-only.
   - **Enforce the size budget:** `learnings.md` stays a compact index (rough
     target: under ~120 lines / mostly one-liners). If it's overflowing, move
     detail down, not the other way around.
   - Clear the consolidated entries from `INBOX.md` (keep the header/format).

6. **Report and commit.** Produce a summary:
   - per repo: entries consolidated, promoted, pruned;
   - cross-cutting: what was promoted to core / each stack, and why.
   In dry-run, stop here — print the plan, write nothing. Otherwise make **one**
   atomic commit across the whole store
   (`consolidate: N entries across M repos; promoted P, pruned Q`) so the pass is
   easy to review or revert in a single step.

## Scaling

Step 2 reads the whole store, so cost grows with total store size, not per-repo
size. Fine for a handful of repos. If it ever strains context: first do a cheap
mechanical pass — hash/normalize inbox lines to find candidate duplicate clusters
— and only reason in depth over the genuine clusters, rather than ingesting the
entire corpus at once. Build the simple version unless/until that's needed.

## Notes

- Promotion direction is always toward the **most general tier the evidence
  supports** — and no further. One repo is not evidence of universality.
- Prefer merging near-duplicates and deleting stale entries over accumulating;
  unchecked growth and staleness are the failure modes this pass exists to fight.
