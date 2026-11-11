# Changelog

Changes to the `living-docs` plugin and its skills. Doc syncs are tracked in each doc's own Changelog tab and in git history.

## 1.0.0

First release as a Claude plugin. Rewritten from the skill text in the build guide's Skills tab and the Living Doc Template doc.

### Structure

- Each skill is a folder with `SKILL.md`, plus `references/` for detail that's loaded only when needed. `doc-sync` went from about 165 lines to 110.
- Added `.claude-plugin/marketplace.json` and `plugins/living-docs/.claude-plugin/plugin.json`, so Claude Code can install it with `/plugin`.
- Added `tools/skills.py` (sync, validate, package, configure) and CI jobs that validate the skills and build upload zips.

### Behaviour

- **Requirements first:** every skill checks for its tools before doing anything and stops, naming what's missing.
- **Better triggers:** `doc-redact` and `living-doc` descriptions now include plain-language requests, not only the slash command. `living-doc`'s "use when" moved from the body into the description, where Claude can see it before the skill loads.
- **Setup values:** names like `my-docs`, `docs-bot` and the owner now come from one table at the top of each skill. Fixed `living-doc`, which shipped with an unfilled `<Your English…>` placeholder.

### Public gate

doc-sync's gate and doc-redact's leak scan now share one definition (`shared/public_gate.py` and `shared/public-gate.md`). Differences between the old versions, and how each was resolved:

| Rule | Old doc-sync | Old doc-redact | Now |
| --- | --- | --- | --- |
| Times | `HH:MM` only (missed `9:30`) | `H:MM` | `H:MM` and `HH:MM`, with optional seconds |
| Years | Month name and year | Any bare year | Month dates and ISO dates block; a bare year warns |
| IPv4 | Ignored private ranges | Flagged every address | Public blocks, private warns, documentation ranges allowed |
| Secrets | The bare words token, password, secret, api_key | Not checked | Real token shapes and `key: value` assignments block; the bare word no longer flags guide text such as "personal access token" |
| Links | claude.ai artifact links | claude.ai artifact links | Any `claude.ai/` link |

The gate allows a doc.yml `last_sync` line in UTC, the one timestamp public files are meant to carry, and never prints denylist terms.
