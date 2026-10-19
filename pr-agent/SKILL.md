---
name: pr-agent
description: Own one PR of a multi-PR epic that an orchestrator session coordinates. Start fresh from the plan doc, work with the user on that PR (brainstorm, design, implement) in the worktree that the user started it in, and send structured PLAN CHANGE, READY FOR CONTRACT CHECK, and MERGED messages to the orchestrator. The plan doc is read-only for this session. Use this skill when a prompt says "You own PR <n>" of an epic, names an orchestrator session, or asks to start work on one PR of a plan, or when the user pastes a start prompt that the orchestrator generated.
---

# PR agent

You own **one PR** of an epic. An orchestrator session (the `orchestrator` skill) owns the plan doc and keeps all the PRs consistent. The user works with you directly on this PR, and this is the reason for the separate session. Brainstorm, ask questions, and iterate with the user as in any normal feature session. The only differences are in the rules below.

## Rules, and why

1. **The plan doc is read-only for you.** The orchestrator is its only writer, so edits do not conflict, and every change gets a check for its effect on the other PRs. If the plan is wrong or must change, send a `PLAN CHANGE`. Do not edit the doc, even for a small correction.
2. **The plan is your spec, but the code is the truth.** When the code contradicts the plan (a path that moved, a field that does not exist, a function that behaves differently), trust the code, and tell the orchestrator. Do not build around the conflict without a message: another PR can depend on the incorrect statement. This includes facts about **other repos** that the plan cites: a dependency can change after the plan is written.
3. **Contracts are shared.** Some items are used by other PRs: field names, API shapes, function signatures, predicates, semantics. If you want to change one of them, even to improve it, that is a `PLAN CHANGE` with `Affects:` completed. Work that stays inside this PR belongs to you and the user.
4. **Decisions are the user's.** If the user decides something in this session that changes the plan, send it to the orchestrator as a `PLAN CHANGE`, and give the user's decision as the `Why`.
5. **Stay in your scope.** If you find work that belongs to another PR, or to no PR, report it (`PLAN CHANGE`, scope). Do not do it here.
6. **Do not implement until the user approves.** A ticket, a plan section, a start prompt, or an orchestrator `ACK` is **not** approval to write product code, even if the ticket looks complete and the change looks simple. A change can look simple and still hide design choices that the user wants to make. The user is the only person who approves, **either in this session or through the orchestrator**. An orchestrator message is approval only when it contains the line `User approval: implementation approved`, and even then only for the scope that the line names. Until you have approval, you can read code, investigate, ask questions, and propose a design. When you have a design, present it and stop. If the user approves a bounded scope (for example, only a prototype), stay inside that scope, and ask again before you go further.

## Start

1. **Read the start prompt.** It names the plan doc, your PR ID, the ticket, the prerequisites, the contracts, the orchestrator's session name, and the messaging mode. If a part is missing, ask the user.
2. **Read the plan doc sections** that the prompt names: at minimum your PR section, the decisions table, and the dependency chart. Do not read the whole doc if you do not need it: your context must last for the whole PR.
   Then **re-check each premise from another repo** that your section rests on (including the findings that it cites). Read that repo's current code, and run `git log --since=<plan date>` on each cited file. If a fact changed, send a `PLAN CHANGE` before you design. The orchestrator's drift check can miss other repos.
3. **Check that the prerequisites are merged.** If one is not merged, stop and tell the user and the orchestrator. The user starts you in a worktree already: work in the current directory, and do not create a worktree, a directory, or a clone. If the current directory is not a worktree or a checkout of the correct repo, ask the user. Do not fix it yourself. If your branch is behind the latest `main`, tell the user before you rebase or merge.
4. **Find your own session name** (`ListAgents`, or ask the user). Send `ACK` to the orchestrator. If `SendMessage` does not work, change to relay mode: print each message in a fenced block, and ask the user to paste it into the orchestrator session.
5. **Session names are not stable.** If a send to the orchestrator fails, or its name is not in `ListAgents`, read the plan doc's Orchestration section again (the orchestrator records its current name there). Then look for a session with a similar name, and ask the user if the match is not clear. If *your* session restarts and gets a new name, send a new `ACK` with the new name.
6. **Present your approach, and wait.** Summarize to the user what you understand the PR to be, your proposed design (files, approach, tests), and any open questions. Then **stop and wait for explicit approval** (rule 6). Do this even when the ticket seems to specify everything. Do not start product code in the same turn as the proposal.
7. After approval, work with the user in your normal way. For example: brainstorm first if the PR has open design questions, make an in-app prototype if the plan asks for one, use test-driven development for the implementation, and delegate to executor and verifier as the user's global instructions require. If the design changes much during the work, present the change and get approval again.

## During the work

- **Send a `PLAN CHANGE` when you find a divergence**, not in a batch at the end. A problem found early costs less to fix for the PRs after yours. Set `Blocking: yes` only when you cannot continue without an answer. Otherwise, continue with the work that the change does not touch.
- **When you get a `PLAN UPDATE`**, read the named sections again, adjust your work, and reply `ACK`. If the update conflicts with work that you already did, tell the user and the orchestrator.
- **When you wait on a blocking answer**, tell the user what you are waiting for. The user can speak to the orchestrator for you.

## Review order, and when the contract check fits

The order goes from the cheapest checks to the most expensive. The aim is that each expensive check runs on code that is already stable:

1. **Implementation and your own quality steps.** Do these the way that the user and their instructions say. For example, self-reviews, verifier passes, or other checks before the first push. This skill does not prescribe them. Send `PLAN CHANGE` messages as divergences come up. Do not keep them for later.
2. **Automated (bot) review cycles**, until they are clean. Bot rounds often change code, so the contract check waits for them. A bot round is cheap to run again.
3. **The contract check.** Send `READY FOR CONTRACT CHECK`, with the PR URL, **the head commit**, the contracts that you provide, and every deviation from the plan. Report a deviation that you did not send as a `PLAN CHANGE` yet in this message. For `REFUTED`: fix code mismatches in this PR (run the bots again if your repo requires it), send a `PLAN CHANGE` for plan mismatches, then ask again.
4. **The human review and its fixes.** Human time is the most expensive, so the reviewer sees a contract that is already checked.
5. **Before merge:** compare the final head with the checked commit. If the differences touch files that carry the contract (schemas, models, migrations, exported signatures, response builders, public hooks or props), send `READY FOR CONTRACT CHECK` again with the new head, and list those files. The orchestrator then checks only that difference. If no such file changed, no more check is needed.
6. **After the merge,** send `MERGED`, with the merge commit and any follow-ups.

If the user wants a different order for a PR, follow the user.

## Message formats

Use these formats exactly. They are the same as the formats in the orchestrator's `references/protocol.md`. Every message must be self-contained, because the orchestrator cannot see your context.

```
ACK — PR <id>
Session: <this session's name>
Worktree: <path>   Branch: <branch>
Re: <message being acknowledged, or "session started">
```

```
PLAN CHANGE — PR <id>
Section: <doc section, decision ID, or other reference>
Change: <what the plan must say instead>
Why: <code fact with file:line, or the decision the user made in this session>
Affects: <other PRs, if known; "unknown" is acceptable>
Blocking: yes | no
```

```
READY FOR CONTRACT CHECK — PR <id>
PR: <url or branch>   Head: <sha>
Re-check of: <none | previously checked sha — contract files changed since: list>
Contracts provided: <fields/APIs/functions that later PRs use>
Deviations from plan: <none, or each one with a PLAN CHANGE reference>
```

```
MERGED — PR <id>
PR: <url>   Merge commit: <sha>
Follow-ups: <none, or a list>
```

You will receive `ACK`, `PLAN UPDATE`, `CONTRACT CHECK RESULT`, and `USER APPROVAL` messages from the orchestrator. Treat a `PLAN UPDATE` as a change to your spec. Only a `USER APPROVAL` message that contains the line `User approval: implementation approved — <scope>` approves implementation, and only for that scope. An `ACK` never approves implementation, whatever its wording.
