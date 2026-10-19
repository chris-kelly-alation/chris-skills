# Code-change handoff

Use when an issue needs a code change in alation-ai (or in the GitHub Pages runbook repo). The issue file `issues/<slug>.md` becomes the orchestrator plan doc. This session is both the on-call loop and the orchestrator, so it is the only writer of the file.

1. Set `major: true`. In the issue file, write: why a code change is needed, the evidence, the proposed fix direction, and the risk. If the fix touches auth or secrets, apply the Alation auth/secrets policy (no `ALATION_API_KEY` static-key auth extensions, no secrets in `alation_conf`, Vault / tenant vault for secrets) and say that the change is security-sensitive.
2. Notify (key `handoff:<slug>`) and ask the user: "Start the orchestrator for `<slug>`?" Do nothing more until the user says yes.
3. On yes, append to the issue file, below the on-call sections, in the form that `/orchestrator` reads:
   - `## Plan` — goal (link the evidence sections above), non-goals, and the contracts between PRs (if more than one);
   - one `## PR <n>: <title>` section per PR, with enough detail to write a ticket: scope, files/areas, edge cases, tests, done criteria, prerequisites.
   Usually there is one PR. Show these sections to the user and get approval.
4. Invoke `/orchestrator` with the issue file as the plan doc. It adds `## Orchestration`, writes the Jira ticket draft(s), creates them after the user approves, and generates the `pr-agent` start prompt(s). The user runs each prompt in a fresh session. pr-agent sessions read the file; they never write it.
5. Section ownership in the issue file: on-call sweeps edit only the on-call sections (Summary, Timeline, Hypotheses, Runbook, Actions, Open questions, header). The orchestrator role edits only `## Plan`, `## PR <n>`, and `## Orchestration`. Always edit in place; never rewrite the whole file.
6. Record in `state.json.code_changes` and the dashboard `## Code changes`: issue, Jira keys, plan = the issue file path, PRs, status.
7. Keep the on-call loop running. On each sweep, for each recorded PR: `gh pr view <n> --repo <owner/repo> --json state,mergedAt,url` and update the status. When the fix merges and deploys, watch for the alert to stay quiet, then set the issue `understood: true` with the PR as the cause fix.
8. An issue with an active orchestration is not `closed` at `/on-call end`, so it carries over to the next session with its plan.

## Reviewing teammates' PRs during an incident
Offer a start prompt for a separate review session. The user runs `/rename <ticket>-review-<pr>` first. The prompt:
- starts with `/review-pr <url>`;
- gives the incident context and earlier review findings;
- has a numbered "check especially" list;
- lists the on-call issue file paths as read-only, and the orchestrator session name;
- asks for an ACK and a REVIEW SUMMARY (verdict, blockers with file:line, rollout impact, deploy order) via `SendMessage`;
- says the review session never posts comments itself.
Record each summary in the issue file. Duplicate ACK/SUMMARY messages can arrive (session restarts): compare them and report only the differences.

## Shift handoff file (End step 2)
Write `<session dir>/handoff.md` as a standalone file the user can send to the next on-call engineer. The dashboard `## Handoff summary` only links to it. Rules:
- No links to local files (`issues/*.md`).
- Slack messages as permalinks: `https://alation.slack.com/archives/<channel>/p<ts without dot>`. PRs and Jira as links.
- Write to the reader ("<user> will add you to …"), not as notes to self. No internal tool notes (sweep worker etc.).
- Sections: open P1/P2 with status; the exact "before you call it resolved" checks; kill switches; threads to watch; chronic issues and their owners; post-deploy checks for merged-not-deployed PRs; closed this shift (one line); runbook changes made (link the page); other tickets.
- Personal follow-ups (for example a kudos/award nomination) go to the user's memory, not the handoff.
- End does not end the Claude session. The user can keep working; only the loop stops and `ended: true` is set.
