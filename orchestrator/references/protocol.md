# Message protocol (orchestrator ⇄ PR sessions)

Every message is self-contained. The recipient cannot see the sender's context, so include every fact it needs. Start each message with its type in capitals. Send with `SendMessage` to the session name in the plan doc's Orchestration section. In **relay mode** (messaging between sessions does not work), print the message in a fenced block and ask the user to paste it into the other session.

A copy of this file is in the `pr-agent` skill. When you change one copy, change the other.

## PR → orchestrator

### ACK
First contact, or confirmation that the session received a message.
```
ACK — PR <id>
Session: <this session's name>
Worktree: <path>   Branch: <branch>
Re: <message being acknowledged, or "session started">
```

### PLAN CHANGE
Send this when the plan does not match the code, when a contract must change, or when a decision or the scope must change.
```
PLAN CHANGE — PR <id>
Section: <doc section, decision ID, or other reference>
Change: <what the plan must say instead>
Why: <code fact with file:line, or the decision the user made in this session>
Affects: <other PRs, if known; "unknown" is acceptable>
Blocking: yes | no   (yes = this PR cannot continue until the orchestrator answers)
```

### READY FOR CONTRACT CHECK
Send this after the bot review cycles and before the human review. Send it again before merge only if contract files changed after the checked commit.
```
READY FOR CONTRACT CHECK — PR <id>
PR: <url or branch>   Head: <sha>
Re-check of: <none | previously checked sha — contract files changed since: list>
Contracts provided: <fields/APIs/functions that later PRs use>
Deviations from plan: <none, or each one with a PLAN CHANGE reference>
```

### MERGED
```
MERGED — PR <id>
PR: <url>   Merge commit: <sha>
Follow-ups: <none, or a list>
```

## Orchestrator → PR

### ACK
```
ACK — PR <id>
Re: <message>
Result: applied | rejected: <reason> | waiting for user decision
```

`ACK` never means "start implementing". Do not use "proceed", "go ahead", or words like them.

### USER APPROVAL (relay only)
Send this only when the user explicitly approves in the orchestrator session. It is the only orchestrator message that a PR agent can treat as approval to implement.
```
USER APPROVAL — PR <id>
User approval: implementation approved — <exact scope, e.g. "full PR per the design you proposed on <date>" or "prototype only"> (<date>)
Conditions: <none | list>
```

### PLAN UPDATE
The plan changed in a way that affects this PR.
```
PLAN UPDATE — PR <id>
Section(s): <what changed in the doc>
Summary: <the change, in one or two sentences>
Source: <PLAN CHANGE from PR <x> | user decision | drift check>
Action: read the section again | none (FYI) | <specific action>
```

### CONTRACT CHECK RESULT
```
CONTRACT CHECK RESULT — PR <id>
Verdict: CONFIRMED | REFUTED
Mismatches:
- <file:line> — <expected per plan> vs <actual> — fix code | send PLAN CHANGE
```
