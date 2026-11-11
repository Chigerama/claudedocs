# Living Doc Template: Prompt and Skill

These build a new living doc in the shape of the Living Docs build guide: topic tabs, a Claude context tab, Documentation, a Task checklist and a Changelog, ready to mirror to GitLab. Save it as a skill and type `/living-doc`, or paste the prompt into any chat.

## Prompt or skill

Use the skill. It's the right tool for a procedure you'll repeat: you save it once, start it with `/living-doc` or just "start a living doc for X", and when the template changes you edit it in one place. Keep the prompt for chats where your skills aren't loaded, or to show someone else the pattern.

|  | Skill | Prompt |
| --- | --- | --- |
| Start it | `/living-doc`, or ask in plain words | Paste the block, fill in three placeholders |
| Where it works | Every Claude chat on your account once saved | Anywhere, including someone else's account |
| Changing the template | Edit the skill once | Edit this doc, then re-copy |
| Drift between docs | None: every doc comes from the same file | Some, if old copies are reused |

## The prompt

Fill in the three lines at the top and paste the whole block into a new chat. Claude asks at most three questions, and only if the goal is unclear.

```text
Start a new living doc.
Topic: <one line: what it covers and what "done" looks like>
Slug: <short-kebab-name>
Topic tabs: <list them, or "suggest 2-5 from the goal">

Build it as a Claude Doc with the tabs listed on the left, in this order:
1. <Title> (main): a lead sentence that states the goal; How it works (a diagram if
   the topic has a flow or architecture); Design decisions (table: decision, choice,
   why); Phases (numbered, each with its effort and a Done when line); Limits and
   gotchas.
2. Claude context (CLAUDE.md): one paragraph saying this is the working brief;
   Recovery prompt (code block); Who and what; The tabs (table, with a link chip to
   each tab and what it holds); Workflow rules (below); Environment as built (table);
   Key decisions; Gotchas found so far; Where things stand; Next (checklist);
   Open items.
3. One tab per topic, named "Part N · <topic>", each ending in a Done when checklist.
4. Documentation: what the tab is for; How entries work; an Entry template code block
   (heading "YYYY-MM-DD · what was done", Machine and Guide lines, Done with times,
   Deviations and findings, Result, Guide changes, Next); then "## Entries".
5. Task checklist: How to load it into your to-do app; one list as a text code block,
   one task per line, each ending in a phase tag (#p0, #p1...); Step lists for
   multi-step tasks; Recurring tasks with a Repeat table; task counts.
6. Changelog: a table of Date, Time (local), Track (dropdown: Build, Decision, Guide),
   What I did, Notes. Newest first. First row: the doc was created.

Workflow rules for Claude context:
1. I send what I did, with screenshots; you write the Documentation entry.
2. Every piece of work, decision and guide change gets a Changelog row.
3. Tick the matching Done when box and the Task checklist task.
4. When reality differs from the guide, fix it in every tab it appears and log a
   Guide row.
5. Never put tokens, passwords or my home public IP in chat, the doc or GitLab.
6. Mirror: after its first /doc-sync, Claude context names the GitLab target
   (<group>/private, and <group>/public if published). Sync only when I run
   /doc-sync.

Conventions: <your English, e.g. Australian or US>, local time, plain and direct,
specifics over adjectives. Look up current facts and cite them in the doc. Fill one
tab at a time so I can watch. When it's built, offer to run /doc-sync private
for its first mirror.
```

## What it builds

Every living doc has the same frame: the topic tabs in the middle, with the same five working tabs around them. The tab order values sort them as strings, so the Changelog stays last however many Part tabs there are.

| Order | Tab | Holds | Published |
| --- | --- | --- | --- |
| a0 | *Title* (main) | Goal, how it works, decisions, phases, limits | Yes |
| a05 | Claude context (CLAUDE.md) | The working brief a fresh chat reads first | Yes |
| a1, a11, a12… | Part 1 · *topic*, Part 2… | The walkthrough, one topic per tab, each ending in Done when | Yes |
| a18 | Documentation | As-built record, newest last | Yes |
| a19 | Task checklist | Paste-ready tasks with phase tags | Yes |
| a2 | Changelog | Date · Time · Track · What I did · Notes, newest first | Yes |

Every tab defaults to `publish: true` in `doc.yml`. To keep a tab out of the PDF and the public project, set it to false.

## The skill

This is the same template as a skill. To save it, open **Customize → Skills** in Claude and create a new skill from the text below, or paste it into a chat and ask Claude to propose it as a skill. To change it later, ask Claude to update the living-doc skill, or edit it in your skill settings. Then update this copy to match.

```markdown
---
name: living-doc
description: Start a new living doc in the living-doc template (topic tabs plus Claude context, Documentation, Task checklist and Changelog), ready to mirror to GitLab.
---

# Living doc

Builds a new Claude Doc in the living-doc template, then offers to onboard it to the GitLab mirror (my-docs/private, and my-docs/public for published tabs). Use it when the owner asks to start, set up or template a living doc, guide or project doc.

## 1. Inputs

- Topic: one line on what it covers and what "done" looks like.
- Slug: short kebab-case name. Suggest one from the topic.
- Topic tabs: the owner's list, or suggest 2 to 5 from the goal.

If something is missing, ask for it: at most three questions, all in one go. If the topic is clear, propose the slug and topic tabs and start building.

## 2. Build the doc

Create the doc with every tab in the first call (tabs listed on the left), each holding a pending block that says what's coming. Then fill one tab at a time so the owner can watch.

| Order | Tab | Contents |
| --- | --- | --- |
| a0 | Title (main) | Lead sentence that states the goal. How it works (a diagram if there's a flow or architecture). Design decisions (table: decision, choice, why). Phases (numbered, each with its effort and a Done when line). Limits and gotchas. |
| a05 | Claude context (CLAUDE.md) | One paragraph saying this is the working brief. Recovery prompt (code block). Who and what. The tabs (table: a link chip to each tab, what it holds). Workflow rules (section 3). Environment as built (table). Key decisions. Gotchas found so far. Where things stand. Next (checklist). Open items. |
| a1, a11, a12... | Part N · topic | The walkthrough for one topic: steps, settings tables, code blocks, sources. Ends with a Done when checklist. |
| a18 | Documentation | What the tab is for. How entries work. Entry template code block: heading "YYYY-MM-DD · what was done", Machine and Guide lines, Done (with times), Deviations and findings, Result, Guide changes, Next. Then "## Entries". |
| a19 | Task checklist | How to load it into a to-do app. One list as a text code block, one task per line, each ending in a phase tag (#p0, #p1...). Step lists for multi-step tasks. Recurring tasks with a Repeat table. Task counts. |
| a2 | Changelog | Table: Date, Time (local), Track (dropdown: Build, Decision, Guide), What I did, Notes. Newest first. First row: "Created this doc from the living-doc template". |

## 3. Workflow rules (numbered, in Claude context)

1. The owner sends what they did, with screenshots; Claude writes the Documentation entry.
2. Every piece of work, decision and guide change gets a Changelog row.
3. Tick the matching Done when box and the Task checklist task.
4. When reality differs from the guide, fix it in every tab it appears and log a Guide row.
5. Never put tokens, passwords or the home public IP in chat, the doc or GitLab. Redact screenshots.
6. Mirror: my-docs/private (and my-docs/public), folder docs/<slug>/. Sync only when the owner runs /doc-sync. Report the short commit ID in chat, never in the doc.

## 4. Conventions

- <Your English, e.g. Australian or US>. Every time in the owner's local time.
- Plain and direct. Specifics (numbers, names, dates) over adjectives. Sentences under 25 words.
- Look up anything current (versions, prices, settings paths, product names) and cite the pages in the doc.
- Never put secrets in the doc: tokens, passwords, the home public IP.

## 5. Finish

Reply with one line and the doc link. Offer to run /doc-sync private for its first mirror.

## Onboarding

The first /doc-sync onboards the doc: the doc-sync skill writes doc.yml and commits every tab. If doc-sync isn't available, do it by hand following the Living Docs build guide, Part 3:

1. Write docs/<slug>/doc.yml: title, slug, doc link and id, author <your name>, lang <your language code>, one entry per tab in order (file NN-<tab-slug>.md, name, tab_id, body_id, rev). Set publish: true for every tab.
2. Export every tab as Markdown and save each drawing's code to docs/<slug>/diagrams/<widget-id>.jsx. Make one add_commit to main through the GitLab connector: "docs(<slug>): first mirror". Never set author fields.
3. Add the Mirror rule to the doc's Claude context, add a Changelog row, then run a normal sync.
```
