---
name: living-doc
description: Start a new living doc, a Claude Doc built from the living-doc template with topic tabs plus Claude context, Documentation, Task checklist and Changelog tabs, ready to mirror to GitLab with doc-sync. Use for /living-doc, or when asked to start, set up or template a living doc, build guide, project doc or runbook that will be kept current over time.
---

# Living doc

Builds a new Claude Doc in the living-doc template, then offers to onboard it to the GitLab mirror (GROUP/private, and GROUP/public for published tabs).

## Setup values

| Key | Value | Meaning |
| --- | --- | --- |
| GROUP | `my-docs` | GitLab group used in the Mirror rule. Keep it the same as doc-sync's |
| OWNER | the owner | How to refer to the person the doc belongs to |
| ENGLISH | Australian English (en-AU) | Spelling and language for every tab |

## 0. Requirements

The Claude Docs tools (create a doc with tabs, batch, update). If they're missing, stop and say so: this skill can't build the doc anywhere else. Web search is used for current facts; without it, mark such facts "to check" in the doc.

The GitLab connector isn't needed to build the doc, only for the first mirror.

## 1. Inputs

- **Topic:** one line on what it covers and what "done" looks like.
- **Slug:** short kebab-case name. Suggest one from the topic.
- **Topic tabs:** OWNER's list, or suggest 2 to 5 from the goal.

If something is missing, ask for it: at most three questions, all in one go. If the topic is clear, propose the slug and topic tabs and start building.

## 2. Build the doc

Create the doc with every tab in the first call (tabs listed on the left), each holding a pending block that says what's coming. Then fill one tab at a time so OWNER can watch. Tab order values sort as strings, so the Changelog stays last however many Part tabs there are.

| Order | Tab | Contents |
| --- | --- | --- |
| a0 | Title (main) | Lead sentence that states the goal. How it works (a diagram if there's a flow or architecture). Design decisions (table: decision, choice, why). Phases (numbered, each with its effort and a Done when line). Limits and gotchas. |
| a05 | Claude context (CLAUDE.md) | One paragraph saying this is the working brief. Recovery prompt (code block). Who and what. The tabs (table: a link chip to each tab, what it holds). Workflow rules (section 3). Environment as built (table). Key decisions. Gotchas found so far. Where things stand. Next (checklist). Open items. The full template is in [references/claude-context-template.md](references/claude-context-template.md). |
| a1, a11, a12... | Part N · topic | The walkthrough for one topic: steps, settings tables, code blocks, sources. Ends with a Done when checklist. |
| a18 | Documentation | What the tab is for. How entries work. Entry template code block: heading "YYYY-MM-DD · what was done", Machine and Guide lines, Done (with times), Deviations and findings, Result, Guide changes, Next. Then "## Entries". |
| a19 | Task checklist | How to load it into a to-do app. One list as a text code block, one task per line, each ending in a phase tag (#p0, #p1...). Step lists for multi-step tasks. Recurring tasks with a Repeat table. Task counts. |
| a2 | Changelog | Table: Date, Time (local), Track (dropdown: Build, Decision, Guide), What I did, Notes. Newest first. First row: "Created this doc from the living-doc template". |

## 3. Workflow rules (numbered, in Claude context)

1. OWNER sends what they did, with screenshots; Claude writes the Documentation entry.
2. Every piece of work, decision and guide change gets a Changelog row.
3. Tick the matching Done when box and the Task checklist task.
4. When reality differs from the guide, fix it in every tab it appears and log a Guide row.
5. Never put tokens, passwords or the home public IP in chat, the doc or GitLab. Redact screenshots.
6. Mirror: GROUP/private (and GROUP/public), folder docs/<slug>/. Sync only when OWNER runs /doc-sync. Report the short commit ID in chat, never in the doc.
7. Public: only through the doc's public twin (/doc-redact), after OWNER has reviewed it. Never copy text from this doc to public directly.

## 4. Conventions

- Write in ENGLISH. Every time in OWNER's local time.
- Plain and direct. Specifics (numbers, names, dates) over adjectives. Sentences under 25 words.
- Look up anything current (versions, prices, settings paths, product names) and cite the pages in the doc.
- Never put secrets in the doc: tokens, passwords, the home public IP.

## 5. Finish

Reply with one line and the doc link. Offer to run /doc-sync private for its first mirror. If the doc-sync skill isn't available, offer to onboard by hand with [references/manual-onboarding.md](references/manual-onboarding.md).
