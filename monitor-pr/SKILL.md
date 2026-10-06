---
name: monitor-pr
description: >
  Monitor a GitHub pull request's CI checks, investigate failures as they
  happen, propose specific code fixes, and implement chosen resolutions. Use
  this skill whenever the user wants to monitor PR checks, fix CI failures,
  investigate why CI is failing, watch a PR's status, debug check failures, or
  resolve failing CI pipelines. Triggers on: "monitor my PR", "fix CI",
  "why are my checks failing", "watch PR checks", "CI is red", "checks are
  failing", "help me fix the build", "pr checks", "investigate CI", or any
  request to track, diagnose, or resolve GitHub PR check/CI issues — even if
  the user doesn't explicitly say "monitor". If there's a PR involved and
  checks are mentioned, use this skill.
---

# PR Check Monitor

Monitor a pull request's CI checks, investigate failures as they arrive, and
walk the user through fixing each one.

## Step 1: Identify the PR

Determine which PR to monitor:

1. **User gave a number**: Use it directly (e.g., "monitor PR 42")
2. **User gave a URL**: Extract the number from the URL path
3. **Auto-detect**: Run `gh pr view --json number,title,url` to find the PR for
   the current branch

Confirm before starting:

```
Monitoring PR #42: "Add user auth". Starting check monitoring...
```

If no PR can be found, ask the user to specify one.


## Step 1.5: Decide Execution Mode

**Default: Use a subagent** to handle the monitoring loop and investigation. This
keeps the main conversation clean and allows you to continue other work.

**Exception:** If the user explicitly says "inline", "don't use a subagent", "run
this in the foreground", or similar, proceed with inline execution (Steps 2-7).

### If using a subagent (default):

Spawn a background monitoring agent with the Agent tool:

```
Agent({
  description: "Monitor PR #<NUMBER> checks",
  prompt: "Monitor PR #<NUMBER> in <OWNER/REPO>. Poll CI checks every 30 seconds.
For each new failure, spawn investigation subagents in the background. Present
failures one at a time to the user, wait for resolution choice, implement fixes,
and commit when all failures are resolved. Do NOT push. Follow the pr-monitor
skill steps 2-7 exactly.",
  run_in_background: true
})
```

After spawning, tell the user:

```
Monitoring PR #<NUMBER> in the background. I'll notify you when checks complete
or failures are found. You can continue working — I'll interrupt when there's
something to review.
```

Then exit this skill. The subagent will handle Steps 2-7 and report back.

### If running inline:

Continue to Step 2 below.


## Step 2: Poll Checks

Query check status:

```bash
gh pr checks <NUMBER> --json name,state,startedAt,completedAt,link,description,event,workflow
```

The `state` field uses values like `SUCCESS`, `FAILURE`, `PENDING`, `ERROR`,
`TIMED_OUT`, `CANCELLED`, etc.

After each poll, display a one-line summary:

```
Checks: 4 passing, 1 failing, 2 pending
```

**Polling rules:**

- Poll every 30 seconds (use `sleep 30` between cycles)
- Track which failures you've already started investigating to avoid duplicates
- As soon as a *new* failure appears, spawn an investigation subagent for it
  immediately (Step 3) — do not wait for all checks to finish
- Continue polling until every check has reached a terminal state
- If all checks pass with no failures, report success and exit


## Step 3: Investigate Failures

For each newly-failed check, use the **Agent tool** to spawn an investigation
subagent. Run these in the background so multiple failures get analyzed
concurrently while polling continues.

### What to tell the investigation subagent

Give it the PR number, branch name, repo owner/name, the failed check's name,
its `link` URL, and instruct it to:

1. **Determine the CI system.** Check if the check maps to a GitHub Actions run:

   ```bash
   gh run list --branch <BRANCH> --json databaseId,name,status,conclusion,workflowName --limit 20
   ```

   Match the failed check name against workflow/job names.

2. **Pull failure logs.** Try these approaches in order — some may be blocked
   depending on permissions and workflow state.

   *GitHub Actions (primary):*
   ```bash
   gh run view <RUN_ID> --log-failed 2>&1 | tail -300
   ```

   **Important:** `--log-failed` only works after the *entire workflow run*
   completes. If the failed job has sibling jobs still running, this command
   will fail. In that case, fall back to:

   *Fallback 1 — Run summary with annotations:*
   ```bash
   gh run view <RUN_ID>
   ```
   This shows step-by-step status and often includes error annotations inline.

   *Fallback 2 — Check previous run logs:*
   If the same check failed on a prior push to this branch, those logs are
   often accessible since the whole workflow has completed:
   ```bash
   gh run list --workflow "<WORKFLOW>" --branch <BRANCH> --limit 5 \
     --json databaseId,conclusion
   ```
   Find a completed failed run and pull its logs with `--log-failed`.

   *Fallback 3 — Annotations API:*
   ```bash
   PR_SHA=$(gh pr view <NUMBER> --json headRefOid --jq '.headRefOid')
   gh api "repos/{owner}/{repo}/commits/${PR_SHA}/check-runs" \
     --jq '.check_runs[] | select(.name == "<CHECK_NAME>") | .id' \
     | xargs -I{} gh api "repos/{owner}/{repo}/check-runs/{}/annotations"
   ```
   Note: this may be blocked by repository permissions. If so, skip it.

   *Other CI systems:*
   Note the check's `link` URL. If the URL points to an API-accessible system,
   try fetching it. Otherwise, capture the URL — the main agent will ask the
   user to paste the logs.

3. **Analyze the failure.** From the logs, extract:
   - The exact error message and surrounding log lines
   - Which source files and line numbers are implicated
   - The error category: build error, test failure, lint violation, type error,
     dependency issue, timeout, flaky/transient, or infrastructure issue
   - The root cause — *why* the error happened, not just *what* the error says

4. **Attribution analysis — is this caused by the PR or pre-existing?** This
   step is critical. Many CI failures are not caused by the PR's changes — they
   may be pre-existing issues affecting all branches. Misattributing a systemic
   failure to the PR wastes the user's time and proposes wrong fixes. Always:

   a. Check the PR diff for relevance:
      ```bash
      gh pr diff <NUMBER> --repo <OWNER/REPO> --name-only
      ```
      Do any of the changed files relate to the error? If the error is in a
      completely different area of the codebase, that's a strong signal.

   b. Check if the same failure occurs on other branches:
      ```bash
      gh run list --workflow "<WORKFLOW_NAME>" --repo <OWNER/REPO> --limit 10 \
        --json databaseId,headBranch,conclusion
      ```
      If the same workflow is failing across multiple unrelated branches, the
      failure is almost certainly pre-existing and not caused by this PR.

   c. Check the PR's actual changes for the failing types/symbols:
      ```bash
      gh pr diff <NUMBER> --repo <OWNER/REPO> | grep -i "<ERROR_KEYWORD>"
      ```
      If the PR diff doesn't touch the symbols mentioned in the error, that
      confirms the failure isn't from this PR.

   Mark the failure as **[PR-caused]** or **[Pre-existing]** based on this
   analysis. This classification changes the resolution options significantly.

5. **Read local source.** Read the affected files in the repo to understand the
   code context around the failure. (If the working directory isn't the repo
   checkout, note this limitation.)

6. **Draft resolution options.** The options depend on the attribution:

   **If [PR-caused]:** Propose 2-3 code fix options with specific files,
   functions, and lines. For each, explain what changes and why. If the failure
   looks **flaky** (timeouts, transient network errors, rate limits,
   non-deterministic tests), include a "Re-run this check" option.

   **If [Pre-existing]:** Always include these options:
   - "Skip / ignore for this PR" — this failure predates the PR and affects
     other branches too. The PR can proceed if this check isn't required.
   - "Fix upstream" — describe what the actual fix would be, but frame it as
     a team-level issue, not something the PR author should be expected to
     fix in this PR.
   - "Coordinate with team" — note which other PRs/branches are affected.

7. **Return a structured summary** with: check name, error description, root
   cause, affected files, attribution tag, and numbered resolution options.


## Step 4: Present Failures One at a Time

Once an investigation subagent returns its findings, present that failure to the
user. Handle one failure at a time — wait for the user to pick a resolution
before presenting the next one.

Use this format:

```
### [Check Name] — [PR-caused] or [Pre-existing]

**Error:** [concise error message]
**File(s):** [affected files with line numbers]
**Root cause:** [why this happened]
**Attribution:** [Caused by this PR / Pre-existing — also failing on branches X, Y, Z]

**Resolution options:**

[For PR-caused failures:]
1. **[Fix description]** — [what changes and why]
2. **[Alternative fix]** — [what changes and why]
3. **Re-run check** — [only when failure looks transient]

[For pre-existing failures:]
1. **Skip for this PR** — this failure predates your changes and affects other branches
2. **Fix upstream** — [describe the fix, but note it's a team-level issue]
3. **Coordinate with team** — [which other PRs/branches are affected]

Which resolution would you like? (1/2/3)
```

If the subagent couldn't access logs (non-Actions CI), tell the user:

```
I can see [check name] failed but can't pull logs automatically.
Detail URL: [link]
Can you paste the relevant error output?
```

Then analyze whatever the user provides and propose resolutions.


## Step 5: Implement the Chosen Resolution

Based on the user's choice:

- **Code fix**: Make the minimal, targeted edit. Don't refactor or clean up
  surrounding code. Briefly show what changed.

- **Re-run check**:
  - GitHub Actions: `gh run rerun <RUN_ID> --failed`
  - Other CI: provide the detail URL and tell the user how to trigger a re-run
  - After re-running, add the check back to the monitoring list — it will be
    picked up in the next poll cycle. If it fails again on re-run, treat it as
    a real failure and investigate normally.

After handling one failure, move to the next. If some checks are still pending,
continue monitoring while working through known failures.


## Step 6: Commit and Prompt for Review

Once every failure has been addressed (all fixes implemented or re-runs
triggered):

1. **Merge readiness assessment.** Summarize the overall picture:

   ```
   ### Merge Readiness
   | Category | Count |
   |----------|-------|
   | Checks passing | X |
   | PR-caused failures fixed | Y |
   | Pre-existing failures (not blocking) | Z |
   | Checks skipped | W |

   **Verdict:** [Safe to merge / Blocked by X]
   ```

   This helps the user understand at a glance whether their PR is clean.
   Pre-existing failures that affect other branches should not block the PR
   unless they are required status checks.

2. **Summarize** what was done:

   ```
   ### Changes Summary
   - [check-name]: [brief description of fix]
   - [check-name]: re-run triggered
   - [check-name]: pre-existing, skipped
   ```

3. **Commit** (only if code changes were made):

   ```bash
   git add <specific-changed-files>
   git commit -m "fix: resolve CI check failures

   - [check]: [what was fixed]
   - [check]: [what was fixed]"
   ```

4. **Show the diff** for review: `git diff HEAD~1`

5. **Do NOT push.** Tell the user to push when they're satisfied.


## Step 7: Offer to Re-monitor

After the user pushes (or says they're done reviewing):

```
Would you like me to monitor the checks again for this push?
```

If yes, return to Step 2 for a fresh polling loop.
If no, exit.


## Edge Cases

- **`gh` not authenticated**: Tell the user to run `gh auth login`
- **PR not found**: Ask the user to verify the number and repo access
- **No checks on the PR**: Report "This PR has no CI checks configured" and exit
- **Can't find run ID for a check**: Fall back to the check's detail URL
- **All failures are re-runs**: Skip the commit step, just keep monitoring
- **User wants to skip a failure**: Allow it — move to the next one and note
  what was skipped in the summary
- **Not in the repo directory**: If the current working directory isn't the repo
  checkout, use `--repo OWNER/REPO` with all `gh` commands. Note that you won't
  be able to read local source files or make code edits — flag this to the user
  and suggest they `cd` to the repo first if fixes are needed
- **All failures are pre-existing**: If every failure is pre-existing and none
  are caused by the PR, skip straight to the merge readiness assessment — the
  PR is likely clean and the user just needs confirmation
- **Running in subagent mode (default)**: The background agent will interrupt the
  main conversation when findings are ready. The user doesn't need to check on
  progress — they'll be notified automatically when checks complete or failures
  need attention
