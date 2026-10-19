# Triage

## Dedup (message → issue)
1. Reply on a known thread (`state.json.threads`) → that issue.
2. Else compute a fingerprint:
   - Grafana/NOC alert: `<alert name>|<environment>` (add `|<tenant id>` if the alert is "per tenant" and the description names one). P1-channel alerts have no environment field: use `<alert name>|p1` and also attach to an open issue with the same alert name.
   - Other (human report, exception): exception type + first line of the message, lowercased, with digits, UUIDs, and hex replaced by `#`.
3. If the fingerprint maps to an issue that is not `closed`: attach (add thread, add the message ts to `occurrences` if not already there). If that issue is `resolved` and the message is a firing, set `reopened` and `firing_since` = message time.
Only new messages (after the idempotency filter in SKILL.md § Sweep) can change status. A human "fixed" reply changes status only if it is newer than the latest firing.
4. Else create a new issue. Slug: kebab-case from the alert name + short env (e.g. `picker-es-indexing-timeouts-euw1`), max 6 words, unique (append `-2`, `-3`).

## Status from messages
- `ALERT:` / `*ALERT*-*Firing*` → `firing` (or `reopened` if it was `resolved`).
- `RESOLVED:` / `*ALERT*-*Resolved*` → `resolved`, set `resolved_at`. Use `Total Duration` if given.
- Human reply saying fixed/mitigated → `resolved` (note who said it).
- Before you accept a `RESOLVED` for an issue whose cause is known, check the signal itself (the Logfire/Loki query that showed the cause). If it still shows the failure, keep the issue `investigating` and note "resolve not real (flap / NoData)". Example: QA Coveo 403, 2026-10-13.
- After investigation starts → `investigating` (while still firing).
- `closed` only when `resolved` AND `understood`.

## Priority (re-evaluate every sweep)
| Priority | Rule |
|---|---|
| P1 | kept P1-channel alert, alert with `[P1]`, or prod issue open ≥ 30 min |
| P2 | other prod issue open < 30 min, or non-prod issue open ≥ 4 h, or non-prod with ≥ 3 occurrences in 24 h |
| P3 | other non-prod issues |

"Open" = `firing`, `investigating`, or `reopened`; duration counts from `firing_since`.
Priority never goes down while the issue is open. A rise is an escalation → notify (`esc:<slug>:<P>`).
A prod alert that resolves in < 30 min stays P2 in the record; it still must become `understood`.

## Depth
- P1/P2: Full investigation (`investigate.md` § Full) on this sweep.
- P3: Light triage (`investigate.md` § Light). Do Full if the priority rises.
- Resolved and not `understood`: Post-hoc (`investigate.md` § Post-hoc), on this sweep if time allows, else the next quiet sweep. Prod first.
- Quiet sweep (no new messages): do one Post-hoc or Light item from the backlog, prod first, so the backlog gets smaller without long sweeps. An investigation can find a new issue with no alert (for example a steady error rate); create it with `"alerting": false`.
- Backfill at Start: do Light for all issues and Post-hoc for prod issues; do not do Full on issues already resolved. Messages already in a carried-over issue's `occurrences` or threads are skipped.
- `missing_evidence` not empty and the server is `ok` again → re-run the skipped queries on the next sweep, then clear the list.

## Major issue → issue file
Set `major: true` and write `issues/<slug>.md` when any is true: P1; open > 2 h; `reopened` or ≥ 3 occurrences; needs a code change. Otherwise the issue is only a dashboard row.

## Patterns
After triage, if ≥ 2 issues share a cause, component, tenant, cluster, or deploy, add or update a line in `state.json.patterns` (rendered in `## Patterns`).

## Owner of a non-alation-ai cause
If the cause is cluster infrastructure (CoreDNS, nodes, CNI, Istio), find the owner from the related Grafana alert rule's `Squad` label (CoreDNS rules: `Squad = RPD`) and use that team's channel and on-call (RPD: #team-rpd; US and India on-call). Prefer the existing alert thread for the ping; draft only. A ticket assigned to the user can be commented on; a ticket owned by someone else gets comments only (never change its priority, body, or fields); propose a split (infra items → owner team, alation-ai items → us).
