# Runbooks

| Runbook | URL | Fetch with |
|---|---|---|
| Confluence | https://alationcorp.atlassian.net/wiki/x/AYCfcgM | Atlassian MCP: `fetch` the short link to get the page ID, then `getConfluencePage` (and `getConfluencePageDescendants` if it has child pages) |
| GitHub Pages | https://fantastic-memory-e28g88z.pages.github.io/reference/runbook/ (private; WebFetch is redirected to GitHub auth) | Source is in `~/alation-ai`: `git -C ~/alation-ai fetch -q origin main && git -C ~/alation-ai show origin/main:docs/src/content/docs/reference/runbook.mdx` (also `reference/flows-runbook.mdx`) |

## Cache
Save the content to `<session dir>/.runbooks/confluence.md` and `<session dir>/.runbooks/gh-pages.md`. Record the Confluence page ID and version in `state.json.runbook_cache`, with `fetched_at`. Refresh when older than 24 h.

## Matching
For each investigated issue, search both caches for the alert name, error text, and component. Record the section title and URL as the match, or "no match" (a gap).

## Proposals
Create a proposal when: there is no match (gap); a step was wrong or out of date; an investigation found a useful query or procedure.
- Add it to `state.json.proposals` and to the dashboard `## Runbook proposals` with state `pending`.
- Put the full text (current text → proposed text, and the reason) in the issue file, or in `<session dir>/proposals/<n>.md` if there is no issue file.
- Notify once (key `proposal:<n>`).
- States: `pending` / `approved` / `rejected` / `applied`. A rejected proposal keeps its row and a "revisit when …" note (for example when the owning engineer's fix ships).
- Do not write runbook text about a cause that another engineer owns and has not fixed yet.

## Applying — only with explicit approval
1. The user approves proposal `n`.
2. Show the exact final edit (before → after) and ask "Apply this edit?".
3. Only after yes:
   - Confluence: `updateConfluencePage` replaces the WHOLE page body. A full-body update dropped block `data-local-id` attributes and needed the body retyped. So:
     - One-item insertion: `getConfluencePage` (current version; if it changed since the cache, show the diff again and ask again), then an executor may apply it with `updateConfluencePage`. The proposal is `applied` only after the user compares the page versions (history diff) and confirms.
     - Whole new section: do not call the MCP. Write paste-ready text to `<session dir>/proposals/<n>-<slug>.md` and let the user paste it in the editor.
   - GitHub Pages: it is a change in another repo — use `handoff.md`.
4. Set the state to `applied` (see the Confluence rules above). If the user declines, set `rejected` and keep the row.
Never apply an approval to a proposal whose text changed after the approval.
