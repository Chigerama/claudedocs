# claudedocs: the living-docs Claude plugin

Three Claude skills that start, redact and mirror living Claude Docs. This branch holds only the plugin; the mirrored docs and their PDF build live on `main`.

## The skills

| Skill | Start it with | What it does |
| --- | --- | --- |
| `living-doc` | `/living-doc`, or "start a living doc for X" | Builds a new Claude Doc from the template: topic tabs plus Claude context, Documentation, Task checklist and Changelog |
| `doc-redact` | `/doc-redact`, or "make a public version of this doc" | Makes and updates the doc's redacted **public twin**, with later changes carried over as suggestions |
| `doc-sync` | `/doc-sync private\|public`, or "sync this doc" | Commits the changed tabs to GitLab, one signed commit per doc. Public syncs come only from the reviewed twin |

```mermaid
graph LR
  LD[living-doc] -->|new doc| D[(Claude Doc)]
  D -->|/doc-sync private| P[(GROUP/private)]
  D -->|/doc-redact| T[(Public twin)]
  T -->|/doc-sync public + gate| U[(GROUP/public)]
```

### What they need

| Need | Used by |
| --- | --- |
| Claude Docs tools and the asset tools (`read_asset`, `delete_asset`) | All three |
| GitLab's MCP server (`https://gitlab.com/api/v4/mcp`) as a custom connector | doc-sync, doc-redact (and living-doc's first mirror) |
| A shell (optional) | doc-sync, doc-redact run `scripts/public_gate.py`; without a shell they apply the same rules by hand |

Each skill checks for its tools first and stops, naming what's missing, rather than half-running. They load in Claude Code but only run where the Claude Docs tools exist (Claude on the web, desktop or mobile).

The full setup, covering the GitLab group, the bot account, the connector and the pipeline, is in the Living Docs build guide (`docs/living-docs-guide/` on `main`).

### Set your names

Each `SKILL.md` starts with a **Setup values** table (GROUP, BRANCH, OWNER, BOT, AUTHOR, LANG, ENGLISH). Set them all at once:

```sh
python3 tools/skills.py configure GROUP=my-docs OWNER="Your Name" AUTHOR="Your Name" LANG=en-AU "ENGLISH=Australian English (en-AU)"
python3 tools/skills.py validate
```

`validate` fails if the skills disagree on a value.

### Install

**Claude (web, desktop, mobile):** run `python3 tools/skills.py package`, then upload each `dist/<skill>.zip` in **Customize → Skills**. CI builds the same zips as a workflow artifact.

**Claude Code:**

```text
/plugin marketplace add <path to this repo, or owner/repo once it's on GitHub>
/plugin install living-docs@claudedocs
```

## Layout

```text
.claude-plugin/marketplace.json     marketplace entry for the plugin
plugins/living-docs/
  .claude-plugin/plugin.json        plugin manifest (version lives here and in marketplace.json)
  skills/<skill>/SKILL.md           instructions Claude loads when the skill triggers
  skills/<skill>/references/*.md    detail loaded only when a step needs it
  skills/<skill>/scripts/           copies of shared scripts (don't edit)
shared/                             canonical public gate (public_gate.py + public-gate.md)
tools/skills.py                     sync, validate, package, configure
.github/workflows/skills.yml        CI: validate and package on every change
```

`.gitignore` is an allowlist: only the paths above are tracked. Anything else in the folder, such as mirrored docs, build files or private `public.yml` and `public-denylist.txt` files, stays out of git.

## Source of truth

- **Skills:** `plugins/living-docs/skills/` in this repo, versioned with git. The Skills tab of the build guide and the Living Doc Template doc still hold the older one-file versions. Point those tabs here rather than copying the text again, so the two can't drift.
- **The public gate:** `shared/`. Edit it there, then run `python3 tools/skills.py sync`. `validate` fails if a copy has drifted.

## Versioning

Bump `version` in both `plugin.json` and `marketplace.json` when a skill changes, and add a line to `CHANGELOG.md`. `validate` checks that the two versions match.

## License

None yet. Add one before others install or reuse this.
