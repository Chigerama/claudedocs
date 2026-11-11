A sync makes one signed commit per doc, holding only the tabs that changed since the last sync. You start it: `/doc-sync private` or `/doc-sync public`, optionally with a doc link. The `doc-sync` skill holds the full procedure, and the steps below match it. Claude never syncs by itself at the end of a turn; that keeps the token cost down. Private gets every tab of the doc as it is. Public never gets the doc itself: it gets the doc's redacted **public twin**, after you've reviewed it.

## The sync, step by step

1. **Read the manifest.** `get_repository_file` on `docs/<slug>/doc.yml` (branch `main`). If there's none, this is the doc's first sync.
2. **Compare the tab list.** Read the doc's tab list and set it against the manifest:
   - new tab → `create` with the next free number
   - removed tab → `delete`
   - renamed or moved tab → `move` to its new file name, so `git log --follow` keeps its history
3. **Find changed tabs.** For each tab, read its body with `sinceRev` set to the manifest's `rev`. An empty delta means no change: skip it.
4. **Export.** Get each changed tab's Markdown export as plain text: make a Markdown copy of the tab, read it back as text, and use it exactly as given: never retype or tidy it. (The export tool itself returns base64, which is bigger and easy to garble.) Once the commit is verified, delete those copies, and only those: pictures in the doc are attachments too.
5. **Back up drawings.** For each drawing in a changed tab, read the widget and save its code to `docs/<slug>/diagrams/<widget-id>.jsx`, so a restore puts back the real drawing rather than its caption.
6. **Commit once.** One `add_commit` to `main` with every file action plus the updated `doc.yml` (new `rev` per tab, `last_sync`). Small edits to a big tab can go as partial edits (`old_str` → `new_str`); otherwise send the whole file. Never set author fields.
7. **Verify.** Read one line of each changed file with `get_repository_file`: the reply gives the file's size, which must equal the export's byte count. If one differs, recommit that file whole.
8. **Report in chat, not in the doc.** One line: slug, tabs mirrored, short commit ID. Writing it into the doc would change a tab, which the next sync would then have to mirror, and so on forever.

If the commit fails, retry once and then stop: the doc is untouched, so nothing is lost, and the next sync catches up.

## The public twin

Public gets a separate doc, the **public twin**: a copy of the original with everything identifying rewritten generically. Names, usernames, other project names, machine names, links, ids, dates, times and time zones become example names (`my-docs`, `docs-bot`, `my-guide`) or disappear. Personal working tabs become reusable templates. Pictures stay out unless you supply a redacted copy.

**Making it (once per doc).** Run /doc-redact on the doc. It creates "\<doc title> (Public)" (the published files drop "(Public)"), rewrites every tab, relabels drawings, and records which twin belongs to which doc in a `public.yml` beside the doc's `doc.yml` in **private** (never in public). You read the whole twin before its first sync.

**Keeping it current.** `/doc-sync public` only syncs the twin; run /doc-redact again to bring it up to date. It compares the original doc with the revisions recorded in `public.yml`. For each tab that changed, Claude writes the matching, redacted change into the twin as a **suggestion**. You accept or reject the suggestions in the twin, then run /doc-sync public. The sync refuses while suggestions are open, warns and asks if the original has changes not yet carried over, and commits the twin like any other doc after two leak checks. /doc-redact check scans the twin without changing anything.

1. **Before the commit:** Claude scans what it is about to send for email addresses, public IP addresses, tokens, doc links, and every term on your identifier list. Any hit stops the commit.
2. **After the commit:** the pipeline's `no-secrets` job checks `docs/` against the same list, held as a CI/CD variable in the public project only (Part 4). It can't undo a commit, but it fails loudly so you can act.

A leak committed to public stays in Git's history. Removing it means rewriting history with force push turned on for a moment, so treat the review as the real gate.

## Screenshots and images

Pictures don't pass through Claude. You upload each image file to GitLab yourself, under the name `/doc-sync` gives you, and the sync links to it. No image bytes go through the conversation.

1. Put the picture in the doc as usual.
2. Run `/doc-sync`. For each picture in a synced tab, Claude gives it a file name, records it in `doc.yml`, writes the Markdown link `![caption](images/<name>)` where the picture sits, and checks whether that file is already in the repo.
3. The sync report ends with an **Images to upload** table: each missing file's exact name, where it goes, and which picture it is.
4. Upload each file under exactly that name. No second sync is needed; the next pipeline run embeds it. Until then the PDF shows "Image not uploaded yet" in its place, and the build still succeeds.

**Naming rule.** `<NN>-<tab-slug>-<what-it-shows>.<ext>`, all lowercase with hyphens. `NN` is the tab's number; `what-it-shows` is two to five words from the caption or the nearest heading; `.png` for screenshots, `.jpg` for photos. Once a name is in `doc.yml` it never changes.

**What the report looks like**

| Upload as | To | Which picture |
| --- | --- | --- |
| `docs/my-guide/images/07-documentation-first-pipeline.png` | my-docs/private | Documentation › "First pipeline", 1st picture ("pipeline view") |

**Uploading.** Redact the image first: the leak checks can't read pictures. In GitLab, signed in as yourself, open `docs/<slug>/images/` and choose **+ → Upload file**, keeping the exact name. For several at once, use the **Web IDE**.

**Public.** The twin starts with no pictures. To add one, give Claude a redacted copy for the twin, then upload that copy to the public project under the name the sync gives.

**What the export writes.** A pasted picture comes out of the Markdown export as a placeholder line, `&#91;image: <caption>\]`, and the image is dropped. Reading the tab gives each picture's id and caption, which is how /doc-sync matches pictures to `doc.yml` entries.

## Commit message

The subject is the newest Changelog row's "What I did", cut to about 70 characters. The body lists what moved.

```text
docs(my-guide): first pipeline run and Pages access

Tabs: 07-documentation.md, 09-changelog.md, 01-claude-context.md
Revs: Documentation 12→14, Changelog 20→22, Claude context 8→9
Diagrams: none
Target: private
Sync: manual
```

Template and pipeline changes use `ci:` or `templates:` instead of `docs(...)`.

## The rule that goes in each doc's Claude context

```markdown
Mirror: <group>/private, folder docs/<slug>/; public only through the doc's public twin.
Sync with /doc-sync only when asked. Report the short commit ID in chat; never write it into the doc.
Never edit docs/ in GitLab.
```

## Nightly catch-up

Optional. A scheduled task can sweep `my-docs/private` every night to catch anything you forgot to sync. It costs tokens only on nights when something changed. Public is never synced unattended. The task needs Create commit on Always allow (Part 2, step 4), because nobody is there to approve it. Pick a time off the hour.

```text
Nightly Living Docs sync. Use the GitLab connector and the Claude Docs tools.
1. list_repository_tree on my-docs/private, path docs/, branch main. Read each
   folder's doc.yml.
2. For each doc, read every tab with sinceRev = that tab's rev in doc.yml, and compare
   the doc's tab list with doc.yml (added, removed, renamed, moved tabs).
3. If nothing changed anywhere, stop and reply "No changes".
4. Otherwise, per doc with changes: export the changed tabs as Markdown text, save the
   code of any drawing in them to diagrams/<widget-id>.jsx, and make ONE add_commit to
   main with the file actions and the updated doc.yml.
   Subject: docs(<slug>): nightly sync of <tab names>. Body: Tabs, Revs, Diagrams,
   "Sync: nightly".
5. Verify each file's size matches its export. Retry a failed commit once, then report it.
6. Never edit the docs. Never set author fields. Never touch public.
7. Finish with one line per doc: slug, tabs mirrored, short commit ID.
```

## Cost and size

| Tab size (Markdown) | Per sync |
| --- | --- |
| Under 10 KB | Send it whole: cheap |
| 10–50 KB | Partial edits for small changes, whole file for big ones |
| Over 50 KB | Split the tab in the doc (for example Documentation by month), since every full sync re-sends it |
