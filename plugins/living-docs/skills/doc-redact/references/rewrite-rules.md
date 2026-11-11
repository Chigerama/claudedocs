# What gets rewritten

Rewrite, never black out: the twin must read as a usable guide for anyone. Names in capitals come from the Setup values table in SKILL.md.

## Out

- OWNER's names and usernames, the bot account (BOT), group and project names, machine names
- Their other projects and docs, self-hosted service names, password-manager names
- Doc links and ids, commit ids
- Exact dates, times and time zones
- Every term in `public-denylist.txt`

## Example names instead

`my-docs`, `my-docs/private`, `my-docs/public`, `docs-bot`, `my-guide`, "your account", "your password manager", "your computer", "local time", and placeholders like `<doc link>`. Keep them consistent with the twin's own "Names used in this guide" table, if it has one.

## Stays

Generic technology names (GitLab, Proxmox, OPNsense, Cisco and the like), the language and spelling, the structure and the technical content.

## Working tabs become templates

- **Claude context** becomes fill-in-the-blanks.
- **Documentation** and **Changelog** become their template plus one invented example entry, or a few example rows dated `YYYY-MM-DD` and `HH:MM`.
- **A task checklist** becomes generic.
- Their `carry` in `public.yml` is false: later changes to the original never reach them.

## Other rules

- **Tab names** are copied unless a name identifies. Then rename it generically, for example a named app's checklist becomes "Task checklist".
- **No date chips or mentions** anywhere in the twin.
- **No pictures** unless OWNER hands over a redacted copy for the twin.
- **Drawings** are copied with their labels rewritten.
