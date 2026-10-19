# Sources

## Slack channels
| Name | ID | Priority | Read rule |
|---|---|---|---|
| #alerts-prod-aai | C0B1CTRNYRW | highest | every message and thread |
| #alerts-nonprod-aai | C0B0XGL2C6M | normal | every message and thread |
| #alerts-prod-p1 (shared) | C08661AE62U | P1 | filtered — see below |

### Reading
- Use `slack_read_channel` with `oldest = last_ts` and **`response_format: "detailed"`**. The alert text is in the message *attachment*; `concise` returns empty messages for the Grafana bot. Paginate with `cursor` until there are no more pages.
- Threads: `slack_read_thread` with the message ts.
- A 7-day backfill of #alerts-prod-aai is ~60 KB and is saved to a file. Do not read it whole: extract one line per message (time, ts, ALERT/RESOLVED, title, Environment, tenant, reply count) with a short `python3 -I` script kept outside the session dir.
- `slack_search_public` on C08661AE62U also returns human investigation posts (for example "Investigation summary: …"). Use them as evidence for the matching issue.

### Message format (#alerts-prod-aai, #alerts-nonprod-aai)
Bot: `Grafana_Alert` (U094S4V3PU7). Attachment first line:
- `:alert: ALERT: [P<n>] Alation AI: <alert name> (<grafana rule url>)` → firing
- `:white_check_mark: RESOLVED: [P<n>] Alation AI: <alert name> (<url>)` → resolved

Fields: `*Severity:*` (p1–p4), `*Environment:*` (cluster, e.g. `prodeu-enterprise-euw1`), `*Instance:*`, labels, and `description` annotation (often names the tenant ID and includes a Loki drilldown query). Firing and resolved are separate top-level messages — pair them by alert name + environment (+ tenant if the description names one).

The Grafana rule UID is in the URL: `https://alationprod.grafana.net/alerting/grafana/<uid>/view`.

### P1 filter (C08661AE62U)
This channel is noisy (other services). Do not read it in full. Instead:
- `slack_search_public` with `keywords: ["\"Alation AI\""]`, `filters: "in:<#C08661AE62U>"`, `after: <last_ts>`, `include_bots: true`, `sort: "timestamp"`.
- Keep messages whose title is `*[P1] Alation AI: <name>*` (bot `NOC_Sentinel`, U07TF46E2TX). Firing: `*ALERT*-*Firing*`; resolved: `*ALERT*-*Resolved*` with `*Total Duration*`.
- Also keep human messages in that channel that mention "Alation AI" / "alation ai" — attach them to the matching P1 issue.
- Read the thread of each kept alert. The AI investigation is posted by the `Resolve` bot (U0B5SC13T0F) and ends with "Investigation concluded." Treat its claims as hypotheses.
- Also, when a P1 alert appears in #alerts-prod-aai, check C08661AE62U around the same time for its thread.
- **Date filter:** do not use `on:<today>` — Slack dates are UTC and miss alerts after 17:00 PDT. Use `after:<yesterday>` plus the `after=<last ts>` parameter as the cursor.
- **Human RCAs:** NOC/SRE engineers post root-cause summaries and Jira tickets as replies in the P1 alert thread (for example AL-271159). For every P1 issue, add that thread to `state.json.threads` and read it every sweep for at least 24 h; a human RCA overrides your first classification — correct the issue and say so.

### Decision channels and DMs
Incidents move out of the alert channels. Add these to `state.json.threads` as `<channel>:channel` (whole channel) or `<channel>:<ts>`, with `active: true`:
- ad-hoc incident channels (for example a dedicated `#p1-<topic>` channel);
- release channels (`#mt_weekly_releases`: off-schedule Terraform/IaC approvals);
- DMs and group DMs where the fix or its approval is discussed.
Non-alation-ai P1s (EC2 node failures, OCF, KMS, uptime) are dropped. A human question in #alerts-prod-p1 with unclear scope is read once, then dropped or linked to an issue.

## Logfire servers
| Env | Regions → MCP server |
|---|---|
| prod | use1, usw2, cac1, euc1, euw1, apne1, aps1, apse1, apse2 → `logfire-p-<region>` |
| staging | use1, use2 → `logfire-s-<region>` |
| qa | use1, use2, usw2 → `logfire-qa-<region>` |
| dev | use1 → `logfire-d-use1` |

Region from the alert `Environment` suffix (e.g. `prodeu-enterprise-euw1` → `euw1` → `logfire-p-euw1`). Non-prod environment prefixes map to `s` / `qa` / `d`. If an alert has no region, run one cheap count query on each prod server.

**Projects (org `alation-ai`, verified 2026-10-12).** The project name equals the alert `Environment` value, so map an alert straight to its server:
| Environment / project | MCP server |
|---|---|
| prod-enterprise-use1 | logfire-p-use1 |
| prod-enterprise-usw2 | logfire-p-usw2 |
| prodca-enterprise-cac1 | logfire-p-cac1 |
| prodeu-enterprise-euc1 | logfire-p-euc1 |
| prodeu-enterprise-euw1 | logfire-p-euw1 |
| prodap-enterprise-apne1 | logfire-p-apne1 |
| prodap-enterprise-aps1 | logfire-p-aps1 |
| prodap-enterprise-apse1 | logfire-p-apse1 |
| prodap-enterprise-apse2 | logfire-p-apse2 |
| seprod-enterprise-use1 | logfire-s-use1 |
| stage-enterprise-use2 | logfire-s-use2 |
| qa-enterprise-use1 | logfire-qa-use1 |
| qa-enterprise-use2 | logfire-qa-use2 |
| qa-enterprise-usw2 | logfire-qa-usw2 |
| development-enterprise-use1 | logfire-d-use1 |

Note: `seprod-enterprise-use1` is on a `logfire-s-*` server but its alerts may arrive in either channel — classify env by the channel the alert came from.
If `project_list` shows only `starter-project` (a personal org), the MCP is authenticated to the wrong org — treat it as `needs_reauth` (`investigate.md` § Auth). Record the project per server in `state.json.logfire_projects` at the health check.

## Grafana
MCP: `plugin_grafana-cloud-mcp_grafana-cloud` (stack `alationprod.grafana.net`, org 1, Viewer). Use:
- `alerting_rules_read` with the rule UID from the alert URL.
- `query_loki_logs` with the drilldown from the alert description (labels like `{app_name="alation-ai", ...}`).
- `query_prometheus` for the rule's metric.
- `list_incidents` for active incidents.

Non-prod (qa, dev; rule URLs on `alationdev.grafana.net`): MCP `grafana-alationdev` (stack `alationdev.grafana.net`, separate OAuth login; URL `https://mcp.grafana.com/mcp?stack=alationdev`. The URL must differ from the plugin's URL. If it is the same, Claude Code removes the duplicate and the prod plugin server disappears). Loki datasource `grafanacloud-logs`, clusters `qa-enterprise-use1|use2|usw2`, `development-enterprise-use1` (label `cluster`, `container="alation-ai"`). Logs go back about 32 days, and one query can cover at most 30 days. The prod MCP cannot see non-prod logs.

## Repo
`~/alation-ai`: `git -C ~/alation-ai fetch --tags -q`, then `git -C ~/alation-ai log --since="<window start>" --oneline origin/main`, `git -C ~/alation-ai tag --sort=-creatordate | head -5`, and `CHANGELOG.md`.
