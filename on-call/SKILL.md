---
name: on-call
description: "Run an alation-ai on-call shift for the on-call engineer. Monitors the alation-ai Slack alert channels (#alerts-prod-aai, #alerts-nonprod-aai, and Alation AI alerts in #alerts-prod-p1); investigates issues with Logfire and Grafana MCPs; tracks every issue (including self-resolved ones) in a per-session dashboard and per-issue files under the session dir (default ~/Notes/on-call/); proposes runbook updates; hands code fixes to /orchestrator. Use when the user mentions being on call, starts an on-call shift, asks to check alerts, triage on-call, sweep the alert channels, asks \"what's open?\" during on-call, or runs \"/on-call start|sweep|end\" or \"/loop /on-call sweep\"."
---

# On-call (alation-ai)

Follow the user's language and style preferences (for example from their CLAUDE.md).

## Hard rules
- Slack: read, and save replies ONLY with `slack_send_message_draft`. NEVER send messages, add reactions, or schedule messages.
- Runbooks: NEVER edit. Write proposals. Apply an edit only after the user approves that exact edit (`references/runbooks.md`).
- Code: NEVER change code in this session. Hand off with `references/handoff.md`.
- `state.json` is the source of truth. Read it at the start of every command; write it at the end.
- Never invent findings. Every hypothesis cites evidence (query result, link, message).

## Paths
- Session dir: `<base_dir>/<YYYY-MM>/` (month of `/on-call start`). The default `base_dir` is `~/Notes/on-call/`; at Start the user can choose another base dir, stored in `state.json` as `base_dir`. Active session = newest folder in the base dir whose `state.json` has `"ended": false`. (Below, `~/Notes/on-call/` means the base dir.)
- Symlink: `./on-call` in the cwd → session dir.

## Commands
- `/on-call start` → **Start**.
- `/on-call sweep` → **Sweep**. If no active session exists, do NOT run Start: tell the user "No active on-call session — run `/on-call start`", and stop the loop if in one.
- `/on-call end` → **End**.
- `/on-call catch-up` (also "catch me up", "what did I miss", "I'm back") → **Catch-up**.
- Free-form questions ("what's open?", "dig into X") → answer from the dashboard and issue files; investigate per `references/investigate.md`.

## Start
1. If an active session exists, say so and run a Sweep instead.
   Never overwrite an existing session dir. If `~/Notes/on-call/<YYYY-MM>/` exists with `"ended": true`, ask the user: reopen it (set `ended: false`, keep all files) or start a new dir `<YYYY-MM>-2`.
2. Ask the user for the base dir (default `~/Notes/on-call/`). Create `<base_dir>/<YYYY-MM>/` and `issues/`. Copy `templates/dashboard.md` → `dashboard.md` (fill the month and time). Create `state.json` (schema below, with `base_dir`) with each channel `last_ts` = now − 7 days (Unix seconds, string).
3. Carry-over: if an older session dir exists, copy each issue whose status is not `closed` (its `issues/<slug>.md` and its `state.json` entries in `issues`, `threads`, `fingerprints`, and the `notified` keys for those slugs). List it under "Open issues" with `(carried over)`.
4. Symlink, in the cwd (check with `test -L on-call` first, so a dangling symlink counts as a symlink):
   - `./on-call` does not exist → `ln -s <session dir> on-call`.
   - `./on-call` is a symlink whose target (`readlink on-call`) is under `~/Notes/on-call/` → `ln -sfn <session dir> on-call`.
   - Any other symlink, file, or dir → do not touch it; tell the user.
   - If the cwd is in a git repo (`git rev-parse --git-common-dir` succeeds): `mkdir -p <common-dir>/info`, add the line `on-call` to `<common-dir>/info/exclude` if missing, then run `git check-ignore -v on-call`. If it prints nothing (for example, `on-call` is tracked), tell the user.
5. MCP health check (`references/investigate.md` § Auth).
6. Fetch the runbooks (`references/runbooks.md` § Cache).
7. Run one Sweep (it backfills 7 days because of `last_ts`). During this backfill, do not send macOS notifications for issues that are already resolved.
8. Ask the user for the previous on-call engineer's handoff (Slack message, tickets, PRs). Fold it in: attach each item to an existing issue (Prior work / Related sections) or create an issue with `"alerting": false`; read each Jira ticket (status, assignee, verified facts, ruled out, not determined) and each PR (merged? first release tag with `git tag --contains <merge sha>`? deployed to prod? — compare with the prod image tag from `kube_pod_container_info{container="alation-ai"}`); list open tickets and merged-not-deployed PRs in `## Code changes`.
9. Tell the user: "Start the loop with `/loop /on-call sweep`."

## Sweep
0. **Token budget:** run steps 1–2 in a read-only Sonnet worker per `references/sweep-worker.md`. The main session writes the cursors, `quiet_streak` and the "Last sweep" time from the worker's `CURSORS` block. On `NO_CHANGE`, do only that write and schedule the next wakeup (interval rules in that file). On `CHANGE`, continue at step 3 with the worker's list. If the worker fails or a network error happens, retry once, then go to step 9 anyway.
   After a gap (resume, restart, lost wakeup): tell the user the loop was stopped and for how long.
1. Read `state.json`.
2. Read new messages per `references/sources.md`: production, then non-production, then P1 (filtered). Also read replies on every thread in `state.json.threads` whose issue is not `closed` — this includes threads in other channels (for example a question the user posted in #aai-rubberduck C08TG830WF2) that are linked to an issue.
   **Idempotency:** drop every top-level message with `ts <= channels[ch].last_ts` and every reply with `ts <= threads[key].last_reply_ts` (Slack `oldest`/`after` are inclusive). Only messages that pass this filter have effects. A message ts is added to `occurrences` only if it is not there already.
3. Map each message to an issue (`references/triage.md` § Dedup). Create or update issues.
4. Set priority and investigate (`references/triage.md`, `references/investigate.md`).
5. If `runbook_cache.fetched_at` is older than 24 h, refresh (`references/runbooks.md`).
6. Rewrite `dashboard.md` from `state.json` only (every column has a state field). Keep the `## Notes` section byte-for-byte: it is everything between the `## Notes` line and the `## Handoff summary` line (read it from the current file first; the user's own `##` subheadings are part of it). After every dashboard edit, verify that each string replacement matched (assert or grep); a silent no-op replace has happened. MCP header: `Logfire <ok>/<checked> ✅` plus 🔑 with the names of servers that need re-auth; same for Grafana, Slack, Atlassian. Write or update `issues/<slug>.md` for major issues (`templates/issue.md`). Create it from the template once; after that, edit sections in place. Never rewrite the whole file, and never change the `## Plan`, `## PR <n>: ...`, or `## Orchestration` sections (they belong to the orchestrator role, `references/handoff.md`).
7. Update `state.json`. Per channel, `last_ts` = ts of the newest message read; never move it backwards.
8. Notify (**Notifications**). Print the terminal summary: urgent items first, then counts (open P1/P2/P3, resolved this sweep), then the next wakeup.
9. If running under `/loop`, call `ScheduleWakeup` with prompt `/on-call sweep` and delay: 240 if any prod or P1 issue has an alert that is firing now (issues found by investigation with `"alerting": false` do not count — they do not change minute to minute); else 900 if any non-prod issue is open; else 1500. Store it in `last_interval_s`.
   **Every sweep turn ends with `ScheduleWakeup` or an explicit stop** — also when the worker fails or a network error happens (retry the worker once, then schedule anyway). A lost wakeup stopped the loop silently for ~1.5 days.

A sweep with no new messages must change only "Last sweep" in the dashboard and must not notify — unless `state.json` changed since the last render (see below).

**Render after every state change.** When `state.json` or an issue changes outside a sweep (a free-form question, an orchestrator/PR-session message, a thread reply the user shows you, a Jira or PR update), write `state.json` and then rewrite `dashboard.md` from it (same rules as Sweep step 6) in the same turn. Before you render, check that each changed issue's `status`, `understood`, `cause`, and `next_step`, plus its `code_changes` and `pending_decisions` entries, agree with the latest facts. Remove decisions that are answered or out of date. An issue whose alert resolved but whose underlying problem stays until a fix ships (chronic recurrence, a leak with a PR open) stays under "Open issues", not "Resolved".

## Catch-up
Purpose: the user was away (night, meetings) and needs the state without scrolling back.
1. Read `state.json`. Window = `last_catchup` → now (if null: session start).
2. Build the digest from state and issue-file timelines only (do not re-query tools, except one memory/alert check if the last sweep is older than 30 min). Order:
   - **Now** — anything firing right now, and any metric near a notify line (for example memory ≥ 85%).
   - **What happened** — one line per issue with events in the window: new, escalated, resolved, reopened, firings counted (for example "Picker ES ×5 tonight, counts rising 27→45"), with links to issue files. Group repeats; do not list each sweep.
   - **Replies and messages** — new replies on tracked threads, PR session messages, Jira/PR status changes.
   - **Waiting for you** — every entry in `pending_decisions`, most urgent first (deadline, then priority). One line each, with the action the skill can take on a yes.
   - **Quiet** — channels and areas with nothing new, in one line.
3. Keep it short: aim for one screen. Details stay in the dashboard and issue files.
4. Set `last_catchup` = now. Do not change anything else.

## Pending decisions
Whenever a message asks the user to decide something, also add it to `state.json.pending_decisions` (`id`, `question`, `issue`, `asked_at`, `deadline`, `offer`) and to the dashboard `## 🚨 Needs attention` section. Remove it when the user answers. Catch-up and End read this list, so no decision is lost in the scroll-back.

## End
1. Run a final Sweep without scheduling a wakeup.
2. Write `<session dir>/handoff.md`: a standalone file the user can send to the next on-call engineer (rules and sections in `references/handoff.md` § Shift handoff file). The dashboard `## Handoff summary` only links to it.
3. Set `"ended": true` in `state.json`. Stop the loop (`ScheduleWakeup` with `stop: true` if in a loop). End does NOT end the Claude session: the user can keep working. Only the loop stops.

## Notifications
Run `osascript -e 'display notification "<msg>" with title "On-call" sound name "Glass"'` for: new P1/P2, priority escalation, MCP re-auth needed, a runbook proposal or code handoff waiting for the user. Each event has a key (for example `new:<slug>`, `esc:<slug>:P1`, `reauth:<server>`, `proposal:<n>`, `handoff:<slug>`). Notify only if the key is not in `state.json.notified`, then add it. When an issue becomes `reopened`, remove its `new:` and `esc:` keys first, so the reopen notifies.

## Delegation
Investigation judgment stays in this session. Broad searches in `~/alation-ai` (find the code for an error, the callers of a function) go to a `scout` agent.

## state.json schema
```json
{
  "session": "YYYY-MM",
  "base_dir": "~/Notes/on-call/",
  "ended": false,
  "channels": {
    "C0B1CTRNYRW": {"last_ts": "1791000000.000000"},
    "C0B0XGL2C6M": {"last_ts": "1791000000.000000"},
    "C08661AE62U": {"last_ts": "1791000000.000000"}
  },
  "issues": {
    "<slug>": {
      "title": "", "env": "prod|nonprod", "environment": "prodeu-enterprise-euw1", "region": "euw1",
      "priority": "P1|P2|P3", "status": "firing|investigating|resolved|reopened|closed",
      "first_seen": "ISO", "firing_since": "ISO (start of the current firing; reset on reopen)",
      "last_update": "ISO", "resolved_at": null,
      "occurrences": ["<message ts>"], "understood": false, "major": false,
      "threads": ["<channel>:<ts>"], "rule_url": "",
      "summary": "", "hypothesis": "", "cause": "", "verdict": "cause|transient-no-action|unknown",
      "runbook_match": "<section + url> | no match", "missing_evidence": ["<server skipped because of auth>"],
      "draft_saved": false, "next_step": "", "alerting": true
    }
  },
  "threads": {"<channel>:<ts> | <channel>:channel": {"slug": "<slug>", "last_reply_ts": "<ts>", "active": true}},
  "patterns": ["<one line>"],
  "fingerprints": {"<fingerprint>": "<slug>"},
  "mcp_auth": {"<server>": "ok|needs_reauth"},
  "logfire_projects": {"<server>": "<project name>"},
  "notified": ["<event key>"],
  "runbook_cache": {"fetched_at": null},
  "proposals": [{"n": 1, "runbook": "", "section": "", "summary": "", "reason": "", "issue": "<slug>", "state": "pending|approved|rejected|applied"}],
  "code_changes": [{"issue": "<slug>", "jira": [], "plan": "", "prs": [], "status": ""}],
  "last_interval_s": 1500,
  "quiet_streak": 0,
  "known_noise": [{"fingerprint": "<title>|<env>", "reason": "", "ticket": "", "added": "ISO", "count": 0}],
  "last_catchup": "ISO | null",
  "pending_decisions": [{"id": "d1", "question": "", "issue": "<slug>", "asked_at": "ISO", "deadline": "ISO | null", "offer": "what the skill does on yes"}]
}
```

## References
- `references/sources.md` — channels, message format, P1 filter, decision channels and DMs, Logfire server map, Grafana, repo.
- `references/triage.md` — dedup, status, priority, depth, major-issue rule.
- `references/investigate.md` — Logfire/Grafana playbook, auth handling, secrets, fix chains, Slack drafts.
- `references/runbooks.md` — runbook cache, matching, proposals and how to apply them.
- `references/handoff.md` — orchestrator, Jira, pr-agent, teammate PR reviews, shift handoff file.
- `references/sweep-worker.md` — Sonnet sweep worker, cursor rules, tracked channels, loop continuity, quiet-interval backoff, known_noise, inactive threads, disabled MCP servers.
- `templates/dashboard.md`, `templates/issue.md`.
