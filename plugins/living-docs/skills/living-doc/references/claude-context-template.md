# Claude context tab template

Fill the angle-bracket parts for the new doc. GROUP comes from the Setup values table in SKILL.md. Keep the headings in this order.

The tab opens with one paragraph: "This tab is the doc's working brief for Claude, like a CLAUDE.md file. If a chat is lost, start a new one, paste the doc link and say 'read the Claude context tab first, then carry on'."

## Recovery prompt

```markdown
This is my <doc name> (link). Read the "Claude context" tab first, then the last entry in Documentation and the top rows of Changelog. Carry on with the same workflow: as-built entries in Documentation, every change and decision in Changelog (newest first, local time), Done-when boxes ticked in the Part tabs, guide fixed where reality differs, Task checklist kept in step. Keep the Claude context tab current.
```

## Who and what

- Owner: <your name or handle>, <your role>. Language: <your preferred English or language>.
- Goal: <what this doc is for, in one sentence>.
- Mirror: GROUP/private (and GROUP/public through its public twin), folder `docs/<slug>/`.

## The tabs

| Tab | Holds |
| --- | --- |
| <Overview tab> | What the doc is for, how it works, decisions, phases, limits |
| <Topic tabs> | One tab per part of the work |
| Claude context | This brief |
| Documentation | As-built record, one section per piece of work, newest last |
| Task checklist | Task lists to paste into a to-do app |
| Changelog | Date · Time · Track · What I did · Notes, newest first |

## Workflow rules

1. The owner sends what they did, with screenshots. Claude writes the Documentation entry: heading "YYYY-MM-DD · what was done", then **Machine:** and **Guide:** lines, **Done** (with times), **Deviations and findings**, **Result**, **Guide changes**, **Next**.
2. Every piece of work, decision and guide change gets a Changelog row. Track: Build for setup work, Decision for choices, Guide for edits to the doc. Newest first.
3. Tick the matching Done-when box in the Part tab and the task in the Task checklist.
4. When reality differs from the guide, fix the guide in every tab it appears in and log it as a Guide row.
5. Never put tokens, passwords or a home public IP in chat, the doc or GitLab. Redact them in screenshots.
6. Mirror: GROUP/private, folder `docs/<slug>/`. Sync with /doc-sync only when the owner asks. Report the short commit ID in chat, never in the doc.
7. Public: only through the doc's public twin, after the owner has reviewed it. Never copy text from this doc to public directly.

## Environment as built

| Item | Detail |
| --- | --- |
| GitLab | GROUP/private (Private) and GROUP/public (Public); `main` protected, force push off, signed web commits |
| Connector | GitLab MCP server, https://gitlab.com/api/v4/mcp, authorised as <bot account>, a Developer on GROUP only |
| Pipeline | no-secrets, build-docs, pages, release |

## Key decisions

- <Decision, with the date it was made>

## Gotchas found so far

- <Anything that behaved differently from the guide>

## Where things stand

- <One short paragraph: what's done and what's next>

## Next

- [ ] <The next phase or task>

## Open items

- <Questions still to answer>
