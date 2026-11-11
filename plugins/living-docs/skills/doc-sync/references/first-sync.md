# First sync

Use this when docs/<slug>/doc.yml doesn't exist yet in the target project. Names in capitals come from the Setup values table in SKILL.md.

1. Confirm the slug and target (with several docs, in the one up-front message).
2. Write doc.yml:
   - **Private:** title, slug, author AUTHOR, lang LANG, last_sync (local ISO time), doc_url, doc_id, and one entry per tab in order (file, name, tab_id, body_id, rev, publish: true).
   - **Public:** run "Choosing tabs for public" from references/public.md first (every tab counts as "not in public"), then write a doc.yml with title (the twin's, without " (Public)"), slug, lang LANG, last_sync in UTC with a trailing Z, and only the picked tabs (file, name, rev). No author: the denylist check would flag it.
3. Export the in-scope tabs (references/export-as-text.md), save the drawings' code, run the public gate if the target is public (references/public-gate.md), and make one add_commit: `docs(<slug>): first mirror`. Then verify and clean up as SKILL.md steps 9 and 10 say.
4. Tell OWNER to add this line to the doc's Claude context (or offer to add it): `Mirror: GROUP/private (and GROUP/public), docs/<slug>/. Sync with /doc-sync.` The next sync picks that edit up. A doc with no Claude context tab simply has no Mirror line; it shows as "not mirrored yet" in the doc list until a doc.yml with its id exists.
