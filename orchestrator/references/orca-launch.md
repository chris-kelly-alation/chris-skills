# Orca CLI Launch Procedure

## Detection

The session runs under Orca when both conditions are true:

1. `ORCA_TERMINAL_HANDLE` or `ORCA_WORKSPACE_ID` is set in the environment
2. `orca status --json` reports `.result.runtime.state == "ready"`

If detection fails, use the existing manual path: Chris opens a worktree and a new session, runs `/rename <session-name>`, and pastes the start prompt.

**CLI selection:** Use `orca` as the executable. If `ORCA_CLI_COMMAND` is set, use its value instead (see `~/.claude/skills/orca-cli/SKILL.md`).

## Launch Steps

These steps were verified working on 2026-11-05 with Orca 1.4.248.

### 1. Find the repo id

```bash
orca repo list --json
```

Match `.path` to the repo's absolute path. Record the `id`.

### 2. Create the worktree and launch Claude

```bash
orca worktree create \
  --repo id:<repoId> \
  --name <workspace-name> \
  --no-parent \
  --base-branch origin/<base> \
  --branch <branch> \
  --reference <JIRA-KEY> \
  --agent claude \
  --surface terminal \
  --activate \
  --json
```

Do NOT pass `--prompt`. The session must be renamed before work starts.

Record from the JSON result:
- `.result.worktree.id` — worktree id
- `.result.worktree.path` — worktree path
- `.result.launch.outcome.handle` — terminal handle
- `.result.launch.operationId` — for retry if needed

### 3. Verify the worktree

```bash
git -C <path> log --oneline -1
git -C <path> branch --show-current
```

Check that the log commit equals the verified base SHA and the branch equals the expected branch name.

### 4. Wait for Claude to be ready

```bash
orca terminal wait \
  --terminal <handle> \
  --for tui-idle \
  --timeout-ms 60000 \
  --json
```

### 5. Rename the session

```bash
orca terminal send \
  --terminal <handle> \
  --text "/rename <session-name>" \
  --enter \
  --wait-submit 10 \
  --json
```

Then run `ListAgents` and verify the new name appears.

### 6. Send the start prompt

Write the prompt to a temp file first (outside any repo, for example `/tmp/<session-name>-start-prompt.txt`).

```bash
orca terminal send \
  --terminal <handle> \
  --text "$(cat <prompt-file>)" \
  --enter \
  --wait-submit 15 \
  --json
```

With `--enter`, Orca bracketed-pastes text to a recognized agent, so a multi-line prompt arrives as one turn.

**Success criteria:** `.result.send.accepted == true` and stages include `turn_started`.

### 7. Record in the plan doc

Write these values to the plan doc's status table or "Resume here" section:
- Worktree path
- Terminal handle
- Session name

Then wait for the `ACK` message (via `SendMessage`). Do not poll.

## Failure Handling

- **If a step does not land:** Read the terminal with `orca terminal read --terminal <handle> --json` before any retry. Output is nested JSON under `.result.terminal`; search its strings. Tell the user before retrying.
- **Never launch a second agent without the user's approval.**
- **Lost create reply:** Retry only with `--retry-launch <operationId>`.
- **Lost send reply:** Reissue the exact command with `--retry-request <requestId>`.

## Notes

- Orca puts worktrees under `~/orca/workspaces/<repo>/<workspace-name>`.
- `terminal read` output is nested JSON, not plain text.
- Messaging stays Claude `SendMessage`. Orca is used only to create the worktree, start Claude, and type into it. Never use Orca orchestration or messaging commands.
