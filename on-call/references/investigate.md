# Investigation

Logfire: call `query_schema_reference` once per session before writing SQL. Always add `LIMIT`. Pass `start_timestamp` / `end_timestamp` (ISO 8601, max 14 days). Window = alert start − 15 min → now (or → resolved time).

## Full (P1/P2)
1. Notify (SKILL.md § Notifications).
2. Grafana:
   - `alerting_rules_read` for the rule UID (from the alert URL). Note the query and threshold.
   - Run the rule's query over the window: `query_loki_logs` (use the drilldown in the alert description) or `query_prometheus`.
   - `list_incidents` for active incidents.
3. Logfire (server from `sources.md`; project from `state.json.logfire_projects`):
   - Exceptions: `SELECT exception_type, exception_message, count(*) AS n, min(start_timestamp) AS first, max(start_timestamp) AS last FROM records WHERE is_exception GROUP BY 1, 2 ORDER BY n DESC LIMIT 20`
   - Error rate per 5 min: `SELECT date_bin(INTERVAL '5 minutes', start_timestamp) AS t, count(*) FILTER (WHERE level >= level_num('error')) AS errs, count(*) AS total FROM records GROUP BY t ORDER BY t LIMIT 300`
   - Slow spans: `SELECT span_name, approx_percentile_cont(duration, 0.95) AS p95, count(*) AS n FROM records GROUP BY 1 ORDER BY p95 DESC LIMIT 20`
   - Add a tenant filter when the alert names a tenant (check `query_schema_reference` for the attribute name).
   - Use `project_logfire_link` for 1–3 representative traces.
   - `level` is numeric; if `level_num` is not available, check `query_schema_reference`. If a query fails on a column or function, fix it from `query_schema_reference` and tell the user the working form (propose an update to this file; do not edit the skill yourself).
4. Deploys: `sources.md` § Repo. Note merges or tags within 2 h before the alert.
5. P1: read the `Resolve` bot investigation in the C08661AE62U thread. List its claims as hypotheses; confirm or refute each with evidence.
6. Runbook match (`runbooks.md` § Matching).
7. Record in the issue (dashboard row; issue file if major): hypothesis, evidence links, verdict, next step.
8. Save a Slack draft with `slack_send_message_draft` in the alert thread (`thread_ts` = alert ts): what we see, probable cause, evidence links, next step. 5 lines or fewer. Tell the user the draft exists. Set `draft_saved: true`.
   Slack allows only one attached draft per conversation. If the call returns `draft_already_exists` (or a draft for another issue in the same conversation is still unsent), do not overwrite it: put the draft text in the issue file / dashboard row under "Draft reply" and ask the user to delete the old draft. The same applies when a draft save fails. Save at most one draft per issue per significant change of understanding.

## Alert-specific checks (from on-call experience; also proposed for the runbooks)
- **Deep health check failure (`/api/v1/healthz/deep`):** before you name a cause, read the `checks` array of the log `deep health check reported non-pass` (`status.py`): status, output and time for every component. Only checkers that catch their own error write a `<name> probe failed` line; a `Check timed out after 5.0s` (outer `wait_for`) writes none. A `critical` component (postgres, bedrock) gives overall `fail` → HTTP 503 → the P1; `high`/`medium` give only `warn`. (10-14 euc1: first read "OpenAI" was wrong — bedrock timed out, cause was a CoreDNS node stall.)
- **Infra causes outside alation-ai** (DNS, node network, CNI, kube-system): `kube-system` logs (aws-node, coredns, kubelet) are not in Loki and ENA `ethtool` counters are not in Prometheus. Do not guess the node-level cause; give the evidence to the infra owner (see `triage.md` § Owner of a non-alation-ai cause).
- **Agent chat failure / tool stream crash / unrecognized errors:** check the upstream model first. Prometheus/CloudWatch Bedrock `InvocationServerErrors` and throttles for the model + region in the window, and AWS Health. A Bedrock 5xx outage (10-07 usw2, claude-sonnet-4-6) causes this alert with no code fault; verdict = upstream outage, no action.
- **Chronic single-tenant alert** (same alert + tenant ≥ 3 times in 7 days, each self-resolving — e.g. Picker ES timeouts for one tenant): do not treat each firing as new. Investigate once for the pattern: ES health / write rejections for that tenant, firing times (batch schedule?), and whether the threshold suits that tenant. Outcome is a ticket (capacity or alert tuning), not monitoring.
- **OOMKilled / memory:** run the trend query, not only the instant value:
  `max by (k8s_cluster_name) (container_memory_working_set_bytes{container="alation-ai"} / on(pod, container, k8s_cluster_name) group_left kube_pod_container_resource_limits{resource="memory", container="alation-ai"})` (datasource `grafanacloud-prom`, range 5d, step 6h). ≥ 0.90 on any pod = OOM risk → notify.

- **Logfire scrubbing:** Logfire replaces some attribute values with `[Scrubbed due to 'auth']` (for example `agent_config_id`). Group by `tenant_id` in Logfire, and use the Loki queries from the runbook when you need the agent config ID.

## Fix chains and blockers
- A P1 that waits on several changes: record the chain in the issue file (IaC/Terraform → app PR → hotfix release), with the state of each item and who must approve.
- PR state: `gh pr view <n> --repo <owner/repo> --json state,mergedAt,url`. Release: `git tag --contains <sha>`.
- A fix can be on main but not on the maintenance branch that prod runs (for example prod on a 30.18.x hotfix branch, main at 30.28). Check the branch prod runs.
- Check whether a migration in an already-released tag runs on the next upgrade of a region, and whether it conflicts with an open incident.

## Secrets
- When a credential fix is needed, check the privilege of the key before you suggest copying it (the console shows privileges).
- Never propose a provisioning/admin token in place of a view-only key as a permanent fix.
- Never read secret values. Ask the user to read only the last 4 characters.

## Repeats of a known-cause issue
When an issue with a known cause fires again, run the same diagnostic query again and record what changed (new IDs, new chat, new tenant, new magnitude). It can confirm or widen the fix scope (10-14 request-limit: 1 asset id → 23 integer ids, all covered by the planned guard).

## Light (P3)
One-paragraph summary from the alert description, the exceptions query only, runbook match. No Slack draft unless the user asks.

## Post-hoc (resolved, not understood)
Grafana rule query + Logfire exceptions and error rate over the incident window, deploy check. Then set `understood: true` with either a probable cause (with evidence) or the verdict "transient, no action" with the evidence that shows it. If neither is possible, leave `understood: false` and write what is missing.

## Auth
Health check (Start, and on every sweep for servers marked `needs_reauth`):
- Logfire: `project_list` on `logfire-p-use1` and `logfire-qa-use1`. A real project must be listed (not only `starter-project`). Then `query_run` `SELECT 1 LIMIT 1`.
- Grafana: `user_info` returns the user's Alation account.
- Slack: `slack_read_channel` on `C0B1CTRNYRW` with `limit: 1`.
- Atlassian: `atlassianUserInfo`.
The same rules below apply to all four (server names `slack`, `atlassian`, `grafana`, `logfire-*`). If Slack needs re-auth, the sweep cannot run: notify, add the attention line, and schedule the next wakeup at 240 s.

A server needs re-auth when a call fails with 401/403, "unauthorized", "authenticate", "token expired", an OAuth prompt, or when Logfire lists only the personal `starter-project`:
1. Set `mcp_auth[<server>] = "needs_reauth"`.
2. Notify once (key `reauth:<server>`): "Re-auth needed: <server>".
3. Add "🔑 Re-auth needed: `<server>` — run `/mcp`, select the server, and authenticate with the Alation account" to `## 🚨 Needs attention`.
4. Skip that server for the rest of the sweep. Add the server to `missing_evidence` of each issue whose investigation needed it. Try again on the next sweep.

On a later success: set `ok`, remove `reauth:<server>` from `notified`, remove the attention line.
If all Logfire servers fail, still investigate with Grafana (Loki + Prometheus) and say in the issue that Logfire evidence is missing.
