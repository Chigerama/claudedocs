# Onboarding without doc-sync

The first /doc-sync onboards the doc: the doc-sync skill writes doc.yml and commits every tab. Use these steps only if doc-sync isn't available. They need the GitLab connector (add_commit). Names in capitals come from the Setup values table in SKILL.md.

1. Write docs/<slug>/doc.yml: title, slug, doc link and id, author (OWNER's name), lang (the language code for ENGLISH, e.g. en-AU), last_sync (local ISO time), one entry per tab in order (file NN-<tab-slug>.md, name, tab_id, body_id, rev). Set publish: true for every tab.
2. Export every tab as Markdown and save each drawing's code to docs/<slug>/diagrams/<widget-id>.jsx. Make one add_commit to main in GROUP/private through the GitLab connector: "docs(<slug>): first mirror". Never set author fields.
3. Add the Mirror rule to the doc's Claude context, add a Changelog row, then run a normal sync.
