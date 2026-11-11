# Public gate

One rule set, shared by `/doc-sync` (before a public commit) and `/doc-redact` (the leak scan). The rules live in `scripts/public_gate.py`; this file describes them for sessions without a shell. If the two ever disagree, the script wins.

## With a shell (preferred)

1. Write every file you're about to commit, exactly as you'll send it, into a scratch folder (for example `gate/docs/<slug>/...`), including doc.yml.
2. Save `public-denylist.txt` from GROUP/private to the scratch area (outside `gate/`).
3. Run `python3 scripts/public_gate.py scan gate/ --denylist public-denylist.txt` (the script sits next to this skill's SKILL.md).
4. Exit 1 means at least one **BLOCK**: commit nothing for that doc. **WARN** lines don't block, but list them for OWNER in the report.
5. Delete the scratch files afterwards. They hold denylist terms.

The script never prints denylist terms: a hit shows as `denylist term #N` with the match masked. Report it that way too.

## Without a shell

Check everything you're about to commit for these by hand:

| Rule | Severity | What matches |
| --- | --- | --- |
| Denylist | BLOCK | Every line of `public-denylist.txt` (skip blanks and `#` comments), whole words, any case |
| Email | BLOCK | Any email address |
| Claude links | BLOCK | Anything starting `claude.ai/` |
| Private key | BLOCK | `-----BEGIN … PRIVATE KEY-----` |
| Token literal | BLOCK | `glpat-…`, `ghp_…` and other `gh?_` tokens, `github_pat_…`, `sk-…`, `xox?-…`, `AKIA…` |
| Secret assignment | BLOCK | `token`, `password`, `secret` or `api_key` followed by `:` or `=` and a value of 6+ characters. The bare word (for example "personal access token") is fine |
| Time | BLOCK | `H:MM` or `HH:MM` (with optional seconds) |
| ISO date | BLOCK | `YYYY-MM-DD` with real digits, with or without a time |
| Month date | BLOCK | A month name with a year, with or without a day |
| Public IPv4 | BLOCK | Any IPv4 address outside the ranges below |
| Private IPv4 | WARN | 10/8, 172.16/12, 192.168/16, loopback, link-local, 100.64/10 |
| Documentation IPv4 | allowed | 192.0.2/24, 198.51.100/24, 203.0.113/24 |
| Bare year | WARN | A four-digit year on its own (product names like "Server 2022" are usually fine) |

**Allowed:** a doc.yml line `last_sync: "YYYY-MM-DDTHH:MMZ"` in UTC. That's the one timestamp public files are meant to carry. Placeholders written as letters (`HH:MM`, `YYYY-MM-DD`) never match.

## For a Claude Docs search read

`/doc-redact` scans twin tabs with a Claude Docs search read. Get the pattern with `python3 scripts/public_gate.py regex --denylist public-denylist.txt`, or build it by hand: `(?i)` plus every BLOCK rule above joined with `|`, with each denylist term escaped and wrapped in `\b`. The search can't tell public IPv4 ranges from private ones, so judge each IPv4 hit against the table.
