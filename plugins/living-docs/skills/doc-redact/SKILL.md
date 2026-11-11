---
name: doc-redact
description: Make or update a Claude Doc's public twin, a generic redacted copy for publishing, with later changes carried over as suggestions for the owner to review. Use for /doc-redact, "make a public version of this doc", "redact this doc", "update the public twin", or "check the twin for leaks". Never runs unasked.
---

# Doc redact

Makes and maintains each doc's **public twin**: a separate Claude Doc, "<doc title> (Public)", with everything identifying rewritten generically, so it can go to GROUP/public. This skill is the only thing that writes to a twin. It never commits to GROUP/public: `/doc-sync public` does that, from the twin, after OWNER has reviewed it. Run only when OWNER asks.

## Setup values

Every name in capitals below comes from this table. Keep it the same as doc-sync's.

| Key | Value | Meaning |
| --- | --- | --- |
| GROUP | `my-docs` | GitLab group. Projects are GROUP/private and GROUP/public |
| BRANCH | `main` | Branch every commit goes to |
| OWNER | the owner | How to refer to the person who runs this |
| BOT | `docs-bot` | Claude's own GitLab account (it must never appear in a twin) |

## 0. Requirements: check before anything else

| Need | Tools |
| --- | --- |
| Claude Docs tools | read (including search reads), batch, update, create |
| Asset tools | read_asset, delete_asset (only for the text copies this skill makes) |
| GitLab connector | get_repository_file, list_repository_tree, add_commit, for the two private files below |

If any is missing from the session, stop before creating or editing anything, name what's missing, and say where to add it. Never leave a half-built twin.

A shell is optional. With one, build the leak-scan pattern with `scripts/public_gate.py regex` (next to this file). Without one, build it by hand from [references/public-gate.md](references/public-gate.md).

## Arguments

`/doc-redact [doc link(s) | numbers] [check | new]`, in any order.

- **No mode:** if the doc has no twin yet, **make** one; if it has, **carry over** changes.
- **`check`:** only scan the twin for leaks (see "Leak scan") and report. Change nothing.
- **`new`:** make a fresh twin even though one exists. The old twin is left alone; ask OWNER before pointing `public.yml` at the new one.
- The doc can be given as the original or its twin: either finds the other through `public.yml`. Pick the doc the way doc-sync's "Which doc" does: links, then the open doc, then a numbered list of this chat's docs. Never guess.

## The two files in GROUP/private

- **`docs/<slug>/public.yml`** pairs a doc with its twin: `twin_title`, `twin_doc_id`, `twin_url`, `public_slug`, and per original tab `name`, `tab_id`, `twin_tab_id`, `twin_body_id`, `source_rev` (the original's revision last carried into the twin) and `carry` (false for tabs whose twin is a standing template). The slug comes from the doc's private `doc.yml`. Never write this file to public.
- **`public-denylist.txt`** at the repo root: identifying terms, one per line. Read it at the start of every run. If OWNER names a new identifier, add it (one commit, `public-denylist: add <n> terms`, without echoing the terms in chat) and remind them to add it to the public project's `PUBLIC_DENYLIST` file variable too.

## What gets rewritten

Rewrite, never black out: the twin must read as a usable guide for anyone. The full rules are in [references/rewrite-rules.md](references/rewrite-rules.md); read them before writing any twin text. In short: identifying names, ids, links, dates, times and denylist terms go; consistent example names come in; generic technology names and the technical content stay; working tabs become templates with `carry: false`.

## Make a twin

1. Read the original's tab list and its private `doc.yml` (for the slug). If the doc isn't mirrored to private yet, stop and say to run `/doc-sync private` first.
2. Create the twin in one birth `batch`: title "<doc title> (Public)", every tab in the same order with a pending block, then open it for OWNER (link in chat).
3. Fill one tab per call, rewritten as references/rewrite-rules.md says. Read each original tab's Markdown first: a text copy via blob plus `read_asset`, as in doc-sync, deleting those copies afterwards (only by the asset ids you created); or a view read.
4. Run the leak scan on every twin tab and fix every hit.
5. Read each original tab's current revision (a view read with `sinceRev` far ahead returns `rev`). Commit `public.yml` to GROUP/private on BRANCH: `docs(<slug>): public twin pairing`.
6. Report: the twin's link, tabs made, scan result, and "Read the whole twin, fix anything in it directly, then run /doc-sync public." Stop.

## Carry changes over

1. Read `public.yml` and `public-denylist.txt`.
2. For each tab with `carry: true`, read the original with `sinceRev` = `source_rev`. Skip tabs with an empty delta. If none changed, report "Twin is up to date" and stop.
3. Read the matching twin tab where needed, then write the redacted equivalent of each change into the twin as a **suggestion**: `"suggest": true` on the update payload. Never a direct edit, and never over text OWNER changed themselves in the twin: if their wording is there, suggest around it.
   - **Where a suggestion is refused** (text inside a `markdown`, `csv`, `latex` or `mermaid` code block is refused with `shape_mismatch`): stop, tell OWNER which tab and what the redacted change is, and ask before editing the twin directly. Only with their OK in this chat, write it as a plain edit, run the leak scan on that tab, and say in the report that it went in directly so they can check it before syncing.
4. **Tab changes** in the original: a new tab becomes a new twin tab whose content arrives as suggestions (add it to `public.yml`); a removed or renamed tab is listed for OWNER to decide. Never delete or rename a twin tab on your own.
5. Run the leak scan on the text you suggested and fix any hit before finishing.
6. Commit the new `source_rev` values (and any new tab entries) to `public.yml`: `docs(<slug>): public twin carry-over`.
7. Report: how many suggestions are waiting, in which twin tabs, and "Accept or reject them in the twin, then run /doc-sync public." Stop.

## Leak scan

The same rules as doc-sync's public gate, so a twin that passes here also passes there.

1. Build the pattern: `python3 scripts/public_gate.py regex --denylist public-denylist.txt` (save the denylist to a scratch file outside any published folder, and delete it afterwards), or by hand from references/public-gate.md.
2. For each twin tab, one Claude Docs read with `{"kind": "search", "pattern": "<that regex>"}`.
3. Judge each IPv4 hit against the ranges in references/public-gate.md: documentation ranges are fine, private ranges are a warning, anything else must go. Treat every other hit as a leak.
4. Report each hit with its tab and the words around it, with denylist matches masked. Fix it in the twin (in `check` mode, only report) and search again until clean.

## Never

- Edit the original doc, or commit to GROUP/public.
- Write a twin edit as anything but a suggestion once the twin has been reviewed (only the first build writes directly), except where suggestions are refused and OWNER has said yes in this chat.
- Put a picture in the twin that OWNER hasn't redacted and handed over.
- Write `public.yml`, `public-denylist.txt` or any listed term anywhere public, or repeat listed terms in chat beyond what OWNER typed.
- Run on a schedule or without being asked.
