# Public syncs

Read this before any `/doc-sync public`. Names in capitals come from the Setup values table in SKILL.md.

## Contents

- Public: the twin only
- Choosing tabs for public

## Public: the twin only

`/doc-redact` makes and updates each doc's public twin ("<doc title> (Public)"). This skill only syncs the twin; it never edits it. Before anything else in a public sync:

1. **Find the pair.** Read `docs/<slug>/public.yml` in GROUP/private. Given the original doc, switch to its twin (`twin_doc_id`) and say so. Given the twin, use it. No `public.yml` for the doc: stop and say to run `/doc-redact` first. A doc that is neither: stop.
2. **Open suggestions.** Read each twin tab you'll sync; open suggestions show as `<ins s=…>` or `<del s=…>`. If any are open, stop, list the tabs, and ask OWNER to accept or reject them first.
3. **Changes not yet carried over.** For each `carry: true` tab in `public.yml`, read the original with `sinceRev` = its `source_rev`. If any changed, warn and ask, then wait: "<Doc> has changes in <tabs> that aren't in the public twin yet. Sync the twin as it stands, or run /doc-redact first?"
4. Use `public_slug` as the public folder, and read `public-denylist.txt` from the root of GROUP/private for the public gate.
5. **Drop "(Public)" from what's published.** The twin's own title keeps it, so the two docs are easy to tell apart in Claude, but the public files don't: in the first tab's export, change the opening heading line `# <title> (Public)` to `# <title>` before committing, and verify that file against the size of the text you sent.

## Choosing tabs for public

Run this after reading doc.yml and the doc's tab list (SKILL.md steps 2 and 3), before exporting anything.

1. Read each tab with sinceRev set to the public doc.yml's rev for it (or 0 if it isn't there yet), so you know which tabs changed. This is cheap.
2. Ask OWNER in one message (one section per doc when syncing several), then wait for their answer:

```
Which tabs go to GROUP/public?
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
4. Never sync public without OWNER's answer. On an unattended or scheduled run, skip public entirely and say so.
