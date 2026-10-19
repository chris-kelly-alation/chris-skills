# Sweep worker (token budget)

The main on-call session is large (Opus, long context). A quiet sweep must not cost a full main-session turn. So the main session gives the **read** part of each sweep to a small worker, and it does the judgment only when the worker reports a change.

## Worker
- Agent: `general-purpose`, **`model: "sonnet"`** (a smaller model made repeated errors: filtered human replies as "chatter", skipped threads without an `active` key, re-reported old messages, wrote wrong timestamps and cursors). If Sonnet fails twice in a row (wrong format, missed or invented messages), tell the user.
- Input (in the prompt): the session dir path, and this file.
- **The worker only reads. It writes no file** (not `state.json`, not `dashboard.md`).
- The worker:
  1. Reads `state.json`: `channels[*].last_ts`, `threads`, `known_noise`.
  2. Reads the 3 channels with `oldest = last_ts`, **`response_format: "detailed"`** (NOTE: NOC_Sentinel text is in the attachment; `concise` returns empty bodies). Keeps only messages with `ts > last_ts` (strict; Slack `oldest` is inclusive).
  3. Reads every **active** thread (`threads[key].active` is `true` or missing — a missing key means active) with `oldest = last_reply_ts`, and keeps only replies with `ts > last_reply_ts`. A key `<channel>:channel` is a whole channel: read it with `slack_read_channel` instead, same rule, skip "has joined" messages. Also read the **thread replies** in that channel: read the channel with `response_format: "detailed"` for the last 48 h (not only past the cursor), and for each message whose "Thread: … (latest: …)" time is after the cursor, read it with `slack_read_thread` and report the replies with `ts > cursor`. The cursor is the newest ts of any top-level message or reply.
  4. Drops alert messages that match `known_noise` (alert title + env, or fingerprint), and counts them per fingerprint.
  5. Drops P1 alert messages that are clearly not alation-ai (no `alation-ai`, `Alation AI`, `agent studio`, `bedrock`, or an alation-ai cluster label in the attachment).
  6. Does no time conversion. It reports raw `ts` values only.
- Output, exactly this format, at most 30 message lines, no analysis:
  ```
  NO_CHANGE | CHANGE
  <channel or thread key> | <ts> | <author or alert title> | <env> | <firing/resolved/-> | <one-line gist>
  ...
  CURSORS
  <channel id or thread key> = <newest ts read, or unchanged value>
  ...
  NOISE <fingerprint> = <count>
  ```
- The worker never posts, drafts, reacts, edits files, or investigates.

## Worker reporting rule
Every new human message on a tracked thread, tracked channel, or DM is a `CHANGE`, also when it is only discussion. The worker never filters human messages. It filters only alert messages (known_noise, not alation-ai).
- Cursor checks are strict `ts > cursor`. Never re-report a message at or before the cursor.
- A missing `active` key means active. The main session sets `active` explicitly when it adds a thread.
- Long gap (for example after a restart): paginate until the cursor, and group repeated alert pairs (firing + resolved) on one line with a count.
- If the worker cannot read a thread, but the channel listing shows its latest reply at or before the cursor, `NO_CHANGE` for that thread is valid.

## Main session
- The worker is read-only. Only the main session writes the cursors from `CURSORS` (never move one backwards), the noise counts, `quiet_streak` (+1 on `NO_CHANGE`, 0 on `CHANGE`), `last_interval_s`, and the "Last sweep:" time in `dashboard.md`. Take that time from `date` in the user's local time zone (for example `TZ=<IANA zone> date`), not from the worker.
- When the user posts a message they want to track, add the thread with its cursor set to the user's own message ts (not later), so replies are not missed. Set `active: true`.
- Loop continuity: the sweep turn ends with `ScheduleWakeup` (or an explicit stop) in every case. If the worker fails or a network error happens, retry the worker once, then schedule anyway. On resume after a gap, tell the user the loop was stopped and for how long.
- On `NO_CHANGE`: only the one state write above (cursors, noise counts, `quiet_streak`, "Last sweep") and `ScheduleWakeup`. Reply in one line.
- On `CHANGE`: do Sweep steps 3–8 for the listed messages only (map, triage, investigate, render, notify).
- Known noise firing again: increase the count in the issue only when the worker reports it in a summary, once per sweep.

## Interval (replaces Sweep step 9 values when quiet)
- A prod or P1 alert is firing now: 240 s.
- Otherwise 900 s if a non-prod issue is open, else 1500 s.
- After 3 `NO_CHANGE` sweeps in a row: 1800 s. After 6: 3600 s. Reset to the normal value on any `CHANGE`.
- Store the streak in `state.json.quiet_streak`.

## known_noise (state.json)
`known_noise: [{"fingerprint": "<title>|<env>", "reason": "", "ticket": "", "added": "ISO"}]`. Add an entry only when the user agrees, or when the issue is closed as a false positive with an owner ticket (example: Curation Hub Agent Studio auth flaps, AL-271314). Remove it when the ticket is done.

## Threads
Set `threads[key].active = false` when the issue is `closed`/`resolved` and has had no human reply for 24 h. A worker never reads inactive threads. Set it back to `true` when the user asks or the issue reopens.

## MCP servers
MCP servers can be disabled to save context. If a step needs a server that is not available (Logfire region, Grafana stack, Atlassian, Figma), do not fail silently: tell the user which server is needed and why, and ask them to enable it with `/mcp`. Then continue with the other steps and record the gap in `missing_evidence`.
