The two Claude skills that run this system, ready to paste. `/doc-redact` makes and updates a doc's public twin; `/doc-sync` commits a doc (or its twin) to GitLab. Before you save them, replace the example names (`my-docs`, `docs-bot`, "the owner") with your own, and adjust anything that doesn't match your setup.

## Install a skill

1. In Claude, open **Customize → Skills** and create a new skill, or paste the text into a chat and ask Claude to propose it as a skill.
2. Use the name and description from the skill's frontmatter (the lines between `---`) and everything below it as the instructions.
3. Skills saved to your account are available in every Claude app you sign in to, and in Claude Code.
4. Keep a copy of each skill in your own doc, like this tab, so the doc stays the record when a skill changes.

## What each skill needs

| Skill | Needs |
| --- | --- |
| doc-sync | The GitLab connector (Part 2), the Claude Docs tools, both projects (Part 1), and the asset tools that read and delete a doc's attachments |
| doc-redact | The Claude Docs tools, the GitLab connector, and two files in `my-docs/private`: `public-denylist.txt` at the root and, per doc, `docs/<slug>/public.yml` (the skill writes this one) |

## doc-sync

````markdown
---
name: "doc-sync"
description: "Sync one or more Claude Docs to GitLab on demand: my-docs/private (every tab of the doc) or my-docs/public (only the doc's public twin made by /doc-redact, once the owner has reviewed it), changed tabs only, one signed commit per doc. Use for /doc-sync or \"sync this doc\"."
---

# Doc sync

Mirrors Claude Docs into GitLab, only when the owner asks. Never sync on your own at the end of a turn: manual syncs are how this system saves tokens.

Tools: the GitLab connector (GitLab's MCP server: get_repository_file, list_repository_tree, add_commit, get_commit) and the Claude Docs tools (read, export). Branch: main.

## Arguments

`/doc-sync [private|public] [doc link(s) | numbers | both | all] [slug] [tabs <numbers>|all|same]`, in any order.

- Target: `private` means my-docs/private and `public` means my-docs/public. If none is given, use the target on each doc's Mirror line in its Claude context tab. If a doc has no Mirror line, ask (one question, covering every doc that needs it).
- Docs: see "Which doc".
- Slug: from the Mirror line or doc.yml. On a first sync, suggest a kebab-case slug from the title and confirm it.
- Tabs (public only): `tabs 1,3,5`, `all` or `same` answers the tab question in advance. When several docs are being synced, it applies to all of them.

## Which doc

1. **Links given:** sync exactly those docs.
2. **`both`, `all` or numbers given:** take them from the candidate list (step 4) without asking.
3. **Nothing given, and a doc is open in the owner's viewer:** sync that doc, and name it in the report.
4. **Otherwise, build the candidate list:** the docs this chat has created, edited or read. With one candidate, sync it. With two or more, ask in one message and wait:

```
Which doc should I sync to my-docs/<target>?
 1. <Doc title>   mirrored as <slug>
 2. <Doc title>   not mirrored yet
Reply with a number, several numbers, or "all".
```

Fill "mirrored as" from each doc's Mirror line in its Claude context tab, if it has one. Otherwise write "not mirrored yet". Never guess a doc id.

## Several docs in one run

- Ask all the up-front questions in **one** message before any export: slugs for first syncs, a target for docs with no Mirror line and, for public, each doc's tab-and-picture question in its own section.
- Then sync each doc in turn with the full steps below. Each doc gets its **own** add_commit, so its history stays separate.
- If one doc fails (gate, commit error), report it and carry on with the others.
- Report one line per doc, then one combined Images to upload table, if any are missing.

## Private vs public

| | my-docs/private | my-docs/public |
| --- | --- | --- |
| Source | The doc itself | **Never the doc.** Only its public twin, made and kept current by `/doc-redact` (see "Public: the twin only") |
| Tabs | Every tab, every time. No questions | Only the twin's tabs the owner picks for this sync (see "Choosing tabs for public") |
| doc.yml | Every tab, with doc_url, doc_id, tab_id, body_id, rev, publish | Only the picked tabs: names, files, revs. No doc link or ids |
| Drawings | Code saved to diagrams/<widget-id>.jsx | The same, for picked tabs only |
| Images | Every picture linked as images/<file> | Only pictures the owner has cleared for public |
| Before commit | Normal checks | The public gate must pass |

In private, `publish` in doc.yml only decides what goes into the private PDF build. Default: true for every tab, working tabs included.

If the Mirror line names one target and the owner asks for the other, confirm before going on. A doc can live in both projects, each with its own doc.yml.

## Public: the twin only

`/doc-redact` makes and updates each doc's public twin ("<doc title> (Public)"). This skill only syncs the twin; it never edits it. Before anything else in a public sync:

1. **Find the pair.** Read `docs/<slug>/public.yml` in my-docs/private. Given the original doc, switch to its twin (`twin_doc_id`) and say so. Given the twin, use it. No `public.yml` for the doc: stop and say to run `/doc-redact` first. A doc that is neither: stop.
2. **Open suggestions.** Read each twin tab you'll sync; open suggestions show as `<ins s=…>` or `<del s=…>`. If any are open, stop, list the tabs, and ask the owner to accept or reject them first.
3. **Changes not yet carried over.** For each `carry: true` tab in `public.yml`, read the original with `sinceRev` = its `source_rev`. If any changed, warn and ask, then wait: "<Doc> has changes in <tabs> that aren't in the public twin yet. Sync the twin as it stands, or run /doc-redact first?"
4. Use `public_slug` as the public folder, and read `public-denylist.txt` from the root of my-docs/private for the public gate.
5. **Drop "(Public)" from what's published.** The twin's own title keeps it, so the two docs are easy to tell apart in Claude, but the public files don't: in the first tab's export, change the opening heading line `# <title> (Public)` to `# <title>` before committing, and verify that file against the size of the text you sent.

## Choosing tabs for public

Run this after reading doc.yml and the doc's tab list (steps 2 and 3), before exporting anything.

1. Read each tab with sinceRev set to the public doc.yml's rev for it (or 0 if it isn't there yet), so you know which tabs changed. This is cheap.
2. Ask the owner in one message (one section per doc when syncing several), then wait for their answer:

```
Which tabs go to my-docs/public?
 1. <Tab name>   in public, changed
 2. <Tab name>   in public, unchanged
 3. <Tab name>   not in public, 2 pictures
 ...
Pictures not yet cleared for public (in the tabs above):
 a. <Tab> › "<heading>", picture 1 ("<caption>")
 ...
Reply with tab numbers and picture letters (e.g. "1, 3, a"), "all", or "same" (now: 1, 2).
Tabs in public now that you don't pick are removed from public.
```

3. Apply the answer:
   - A picked tab that's not in public yet: export it and `create` its file.
   - A picked tab already in public: sync it only if it changed.
   - A tab in public that wasn't picked: `delete` its file and its pictures' links. Say so in the report.
   - `same`: keep the current set; sync changes only.
   - `all`: every tab, and only pictures already cleared. Uncleared pictures are listed again next time.
   - Pictures: a letter clears that picture for public. Record it in the public doc.yml `images:` list. A picture that isn't cleared stays a placeholder in public.
4. Never sync public without the owner's answer. On an unattended or scheduled run, skip public entirely and say so.

## Steps (per doc)

1. **Resolve** the target project, the doc and the slug.
2. **Read** docs/<slug>/doc.yml from the target project. If it's missing, this is a first sync (see below). In private, if doc.yml's doc_id isn't this doc's id, stop: that slug belongs to another doc. Report it and ask for a different slug.
3. **Compare the tab list** with doc.yml. A new tab becomes a `create`, a removed tab a `delete`, and a renamed or moved tab a `move` to its new name. File names are NN-<tab-slug>.md, numbered in the doc's tab order (the same numbers in both projects, even when public skips some).
4. **Public only:** run "Choosing tabs for public" now (already answered if several docs were asked about up front).
5. **Find changes.** Read each in-scope tab's body with sinceRev set to its rev in doc.yml. An empty delta means skip it. If nothing changed and the tab list matches, report "No changes" for this doc and move on.
6. **Export** each changed tab as Markdown, as plain text (see "Getting the export as text"), and use the text exactly as exported. To keep output tokens down:
   - For a tab under about 10 KB, send the whole file.
   - For a bigger tab with a small change, read the repo copy (input is cheaper than output), then send `update` actions with `old_str`/`new_str` for just the changed passages. Each `old_str` must be unique in the file.
   - Save a drawing's code only when the drawing is new or changed.
   - Handle pictures as in "Images" below. Never put image bytes in a commit.
7. **Public gate** (public only). Scan everything you're about to commit for: email addresses; IPv4 addresses outside 10/8, 172.16/12, 192.168/16 and the documentation ranges; words like token, password, secret, api_key, PRIVATE KEY; claude.ai artifact links; every term in `public-denylist.txt` from my-docs/private (whole words, any case); and dates or times (`\b\d{2}:\d{2}\b`, a month name with a year). Also confirm the source is the twin named in `public.yml`, not the original doc. If anything turns up, list it (redacted) with its tab, commit nothing for this doc, and ask the owner whether to fix the doc or leave that tab out.
8. **Commit once per doc.** One `add_commit` to main holding every file action for this doc plus its updated doc.yml (each changed tab's new rev, and last_sync: in private as your local ISO time; in public as UTC with a trailing Z, so no time zone shows). Never set author_name or author_email.
   - Subject: `docs(<slug>): <the newest Changelog "What I did", cut to about 70 characters>`, or `docs(<slug>): sync of <tab names>` if there's no new Changelog row.
   - Body lines: `Tabs: ...`, `Removed: ...` (public, if any), `Revs: <tab> old→new, ...`, `Diagrams: ...`, `Images: <linked>, <missing>`, `Target: private|public`, `Sync: manual`.
   - **Moved tabs that also changed:** GitLab refuses a `move` and an `update` of the same file in one commit ("file not found"; nothing is written). Either give the `move` the whole new content, or, when partial edits save a lot of output, make a moves-only commit first (`docs(<slug>): renumber tabs after <reason>`, moving the highest numbers first), then the content commit with its partial edits on the new paths. Found when a new tab shifted three tabs down.
9. **Verify.** Run get_commit. For each whole-file update, run get_repository_file with `limit: 1` and check `metadata.size_bytes` against the blob's `bytes` (or, if image links were written in, the size of the text you sent); if one doesn't match, recommit that file whole. Then delete the temporary text files (see "Getting the export as text", step 4). If the commit fails, retry once, then report the error. The doc is untouched, so nothing is lost.
10. **Report in chat** in one line per doc: doc title, target, slug, tabs synced (and removed, for public), short SHA. If any linked image file is missing from the repo, follow with the **Images to upload** table. Never write the SHA or the sync result into a doc, because that would change a tab and make the next sync dirty.

## Getting the export as text

The Claude Docs export tool returns base64, which is about a third bigger than the text and easy to garble when it's copied into a commit. Get plain text instead (tested: every tab matched to the byte):

1. **Make a text copy of each changed tab.** Claude Docs `create`, object `blob`, container `{kind: project, id: <doc id>}`, payload `{"from": {"object": "file", "id": "<tab id>"}, "format": "markdown"}`. Do every tab in parallel. Each result gives `data.asset` (an asset id), `data.bytes` (the size to verify against) and `rev` (the tab's current revision, which goes into doc.yml).
2. **Read each one.** `read_asset` with the doc's slug and the asset id returns the Markdown as plain text. Read them in parallel.
3. **Commit the text.** Copy it into add_commit with JSON escaping only: `\\` for each backslash, `\"` for each double quote, `\n` for line breaks. Keep the export's own escapes (`\_`, `\]`, `\<`, `\~`, `&#91;`) exactly as they are, and end each file with one newline.
4. **Clean up after the commit is verified.** These copies are attached to the doc as files. Delete each one with `delete_asset`, using only the asset ids returned in step 1. Never delete by type or by listing: pictures in the doc are attachments too, and deleting one removes it from the doc.

If `read_asset` fails, fall back to the export tool and send its `bytes_b64` with `encoding: base64` in add_commit.

## Images

The owner uploads image files themselves; the sync only names them, links them and reports what's missing. That keeps image bytes out of the conversation.

1. **Find pictures.** For each tab being synced, read the tab and list its pictures in order. Each one shows in the read as `<media blob='blob/<id>' alt='<caption>'/>`; note the blob id, the caption and the nearest heading above.
2. **Name new ones.** Pictures already in the private doc.yml's `images:` list keep their file name for good, and public uses the same name. A new picture gets `<NN>-<tab-slug>-<what-it-shows>.<ext>`: NN is the tab's number; what-it-shows is two to five lowercase hyphenated words from the caption or the nearest heading; ext is png for screenshots and jpg for photos. Add a numeric suffix if the name is already taken. Add an entry to the private `images:` list with file, tab, blob, where (heading plus picture number) and caption.
3. **Link.** The Markdown export writes each picture as a placeholder line, `&#91;image: <caption>\]` (or `&#91;image\]` with no caption), and drops the image. Replace those lines, in order, with `![<caption>](images/<file>)`. In public, only pictures in the public `images:` list get a link; the rest stay as placeholders.
4. **Removed pictures.** If an `images:` entry's picture is no longer in the doc (or, in public, its tab was removed), delete its file if present and the entry, in the same commit, and say so in the report.
5. **Check presence.** Run list_repository_tree on docs/<slug>/images/ in the target project. Never upload or re-encode images yourself.
6. **Report missing files** after the summary lines:

| Upload as | To | Which picture |
| --- | --- | --- |
| `docs/<slug>/images/<file>` | my-docs/<target> | <Doc> › <Tab> › "<heading>", <n>th picture ("<caption>") |

Then add one line: "Save the original (or right-click the picture in the doc and save it), redact anything private, rename it exactly as shown, and upload it in GitLab signed in as yourself (+ → Upload file, or several at once in the Web IDE). No re-sync needed."

If the export ever writes pictures differently from the placeholder above, say so in the report so the guide and this skill can be updated.

## First sync

1. Confirm the slug and target (with several docs, in the one up-front message).
2. Private: write doc.yml with title, slug, author <your name>, lang <your language code>, last_sync, doc_url, doc_id, and one entry per tab in order (file, name, tab_id, body_id, rev, publish: true). Public: run "Choosing tabs for public" first (every tab counts as "not in public"), then write a doc.yml with title (the twin's, without " (Public)"), slug, lang, last_sync in UTC and only the picked tabs (file, name, rev). No author: the denylist check would flag it.
3. Export the in-scope tabs, save the drawings' code, run the public gate if the target is public, and make one add_commit: `docs(<slug>): first mirror`.
4. Tell the owner to add this line to the doc's Claude context (or offer to add it): `Mirror: my-docs/private (and my-docs/public), docs/<slug>/. Sync with /doc-sync.` The next sync picks that edit up. A doc with no Claude context tab simply has no Mirror line; it shows as "not mirrored yet" in the doc list until a doc.yml with its id exists.

## Never

- Sync without being asked, or sync public without the owner's tab answer.
- Guess which doc the owner means when several are candidates.
- Commit to my-docs/public from anything but a doc's public twin, or while the twin has open suggestions.
- Edit a twin doc: only `/doc-redact` does that.
- Write `public.yml` or `public-denylist.txt`, or any term from that list, to my-docs/public.
- Put two docs in one commit, or sync a doc into a folder whose doc.yml names a different doc_id.
- Push to my-docs/public a tab the owner didn't pick, a tab that failed the gate, or a picture they haven't cleared.
- Edit files under docs/ by any other route, or force anything onto main.
- Put image bytes (base64) in a commit. Images always come from the owner's upload.
````

## doc-redact

```markdown
---
name: "doc-redact"
description: "Make or update a Claude Doc's public twin: a generic, redacted copy for my-docs/public, with later changes carried over as suggestions for the owner to review. Use for /doc-redact."
---

# Doc redact

Makes and maintains each doc's **public twin**: a separate Claude Doc, "<doc title> (Public)", with everything identifying rewritten generically, so it can go to my-docs/public. This skill is the only thing that writes to a twin. It never commits to my-docs/public: `/doc-sync public` does that, from the twin, after the owner has reviewed it. Run only when the owner asks.

Tools: the Claude Docs tools (read, batch, update, create) and the GitLab connector (get_repository_file, list_repository_tree, add_commit) for the two private files below. Branch: main.

## Arguments

`/doc-redact [doc link(s) | numbers] [check | new]`, in any order.

- No mode: if the doc has no twin yet, **make** one; if it has, **carry over** changes.
- `check`: only scan the twin for leaks (see "Leak scan") and report. Change nothing.
- `new`: make a fresh twin even though one exists. The old twin is left alone; ask the owner before pointing `public.yml` at the new one.
- The doc can be given as the original or its twin: either finds the other through `public.yml`. Pick the doc as doc-sync's "Which doc" does: links, then the open doc, then a numbered list of this chat's docs. Never guess.

## The two files in my-docs/private

- **`docs/<slug>/public.yml`** pairs a doc with its twin: `twin_title`, `twin_doc_id`, `twin_url`, `public_slug`, and per original tab `name`, `tab_id`, `twin_tab_id`, `twin_body_id`, `source_rev` (the original's revision last carried into the twin) and `carry` (false for tabs whose twin is a standing template). The slug comes from the doc's private `doc.yml`. Never write this file to public.
- **`public-denylist.txt`** at the repo root: identifying terms, one per line. Read it at the start of every run. If the owner names a new identifier, add it (one commit, `public-denylist: add <n> terms`, without echoing the terms in chat) and remind them to add it to the public project's `PUBLIC_DENYLIST` file variable too.

## What gets rewritten

Rewrite, never black out: the twin must read as a usable guide for anyone.

- **Out:** the owner's names and usernames, the bot account, group and project names, machine names, other projects and docs of theirs, self-hosted service names, password-manager names, doc links and ids, commit ids, exact dates, times and time zones, and every term in `public-denylist.txt`.
- **Example names instead:** `my-docs`, `my-docs/private`, `my-docs/public`, `docs-bot`, `my-guide`, "your account", "your password manager", "your computer", "local time", placeholders like `<doc link>`. Keep them consistent with the twin's own "Names used in this guide" table, if it has one.
- **Stays:** generic technology names (GitLab, Proxmox, OPNsense, Cisco and the like), the language and spelling, the structure and the technical content.
- **Working tabs become templates:** Claude context becomes fill-in-the-blanks; Documentation and Changelog become their template plus one invented example entry or a few example rows dated YYYY-MM-DD and HH:MM; a task checklist becomes generic. Their `carry` is false: later changes to the original never reach them.
- **Tab names** are copied unless a name identifies (rename it generically, e.g. a named app's checklist to "Task checklist").
- **No date chips or mentions** anywhere in the twin. **No pictures** unless the owner hands over a redacted copy for the twin. **Drawings** are copied with their labels rewritten.

## Make a twin

1. Read the original's tab list and its private `doc.yml` (for the slug). If the doc isn't mirrored to private yet, stop and say to run `/doc-sync private` first.
2. Create the twin in one birth `batch`: title "<doc title> (Public)", every tab in the same order with a pending block, then open it for the owner (link in chat).
3. Fill one tab per call, rewritten as above. Read each original tab's Markdown first (a text copy via blob plus `read_asset`, as in doc-sync, deleting those copies afterwards; or a view read).
4. Run the leak scan on every twin tab and fix every hit.
5. Read each original tab's current revision (a view read with `sinceRev` far ahead returns `rev`). Commit `public.yml` to private: `docs(<slug>): public twin pairing`.
6. Report: the twin's link, tabs made, scan result, and "Read the whole twin, fix anything in it directly, then run /doc-sync public." Stop.

## Carry changes over

1. Read `public.yml` and `public-denylist.txt`.
2. For each tab with `carry: true`, read the original with `sinceRev` = `source_rev`. Skip tabs with an empty delta. If none changed, report "Twin is up to date" and stop.
3. Read the matching twin tab where needed, then write the redacted equivalent of each change into the twin as a **suggestion**: `"suggest": true` on the update payload. Never a direct edit, and never over text the owner changed themselves in the twin: if their wording is there, suggest around it.
   - **Where a suggestion is refused** (text inside a `markdown`, `csv`, `latex` or `mermaid` code block, such as the Skills tab, is refused with `shape_mismatch`): stop, tell the owner which tab and what the redacted change is, and ask before editing the twin directly. Only with their OK in this chat, write it as a plain edit, run the leak scan on that tab, and say in the report that it went in directly so they can check it before syncing.
4. **Tab changes** in the original: a new tab becomes a new twin tab whose content arrives as suggestions (add it to `public.yml`); a removed or renamed tab is listed for the owner to decide. Never delete or rename a twin tab on your own.
5. Run the leak scan on the text you suggested and fix any hit before finishing.
6. Commit the new `source_rev` values (and any new tab entries) to `public.yml`: `docs(<slug>): public twin carry-over`.
7. Report: how many suggestions are waiting, in which twin tabs, and "Accept or reject them in the twin, then run /doc-sync public." Stop.

## Leak scan

For each twin tab, one Claude Docs read with `{"kind": "search", "pattern": "<regex>"}`. Build the regex as `(?i)` plus, joined with `|`: each denylist term escaped and wrapped in `\b`; email addresses; IPv4 addresses; `claude\.ai/artifact`; times `\b\d{1,2}:\d{2}\b`; years `\b20\d{2}\b`; month names followed by a day or year. Example placeholders like `HH:MM` and `YYYY-MM-DD` don't match. Report each hit with its tab and the words around it, fix it in the twin (in `check` mode, only report), and search again until clean.

## Never

- Edit the original doc, or commit to my-docs/public.
- Write a twin edit as anything but a suggestion once the twin has been reviewed (only the first build writes directly), except where suggestions are refused and the owner has said yes in this chat.
- Put a picture in the twin that the owner hasn't redacted and handed over.
- Write `public.yml`, `public-denylist.txt` or any listed term anywhere public, or repeat listed terms in chat beyond what the owner typed.
- Run on a schedule or without being asked.
```
