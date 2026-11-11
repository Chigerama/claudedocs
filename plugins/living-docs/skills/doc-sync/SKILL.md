---
name: doc-sync
description: Mirror one or more Claude Docs into GitLab on demand, as one signed commit per doc holding only the changed tabs. The private target gets every tab of the doc; the public target gets only the doc's reviewed public twin. Use for /doc-sync, "sync this doc", or a request to mirror, back up, push or commit a Claude Doc to GitLab. Never runs unasked.
---

# Doc sync

Mirrors Claude Docs into GitLab, only when the owner asks. Never sync on your own at the end of a turn: manual syncs are how this system saves tokens.

## Setup values

Every name in capitals below comes from this table. Edit it once (or run `tools/skills.py configure` in the source repo); nothing else in this skill needs changing.

| Key | Value | Meaning |
| --- | --- | --- |
| GROUP | `my-docs` | GitLab group. Projects are GROUP/private and GROUP/public |
| BRANCH | `main` | Branch every commit goes to |
| OWNER | the owner | How to refer to the person who runs the sync |
| AUTHOR | Your Name | `author` in private doc.yml files |
| LANG | `en-AU` | `lang` in doc.yml files |

## 0. Requirements: check before anything else

| Need | Tools |
| --- | --- |
| GitLab connector (GitLab's MCP server, `https://gitlab.com/api/v4/mcp`) | get_repository_file, list_repository_tree, add_commit, get_commit |
| Claude Docs tools | read, export, create (a `blob` text copy) |
| Asset tools (may come from a different server than the Docs tools) | read_asset, delete_asset |

If any of these is missing from the session, stop before reading or exporting anything. Name what's missing and say where to add it (the GitLab connector is a custom connector in Claude's settings). Never half-run a sync. This skill can't run where the Claude Docs tools don't exist, such as a Claude Code CLI session.

A shell is optional. With one, run the public gate with `scripts/public_gate.py` (next to this file). Without one, apply the same rules by hand from [references/public-gate.md](references/public-gate.md).

## Arguments

`/doc-sync [private|public] [doc link(s) | numbers | both | all] [slug] [tabs <numbers>|all|same]`, in any order.

- **Target:** `private` means GROUP/private and `public` means GROUP/public. If none is given, use the target on each doc's Mirror line in its Claude context tab. If a doc has no Mirror line, ask: one question, covering every doc that needs it.
- **Docs:** see "Which doc".
- **Slug:** from the Mirror line or doc.yml. On a first sync, suggest a kebab-case slug from the title and confirm it.
- **Tabs (public only):** `tabs 1,3,5`, `all` or `same` answers the tab question in advance. When several docs are being synced, it applies to all of them.

## Which doc

1. **Links given:** sync exactly those docs.
2. **`both`, `all` or numbers given:** take them from the candidate list (step 4) without asking.
3. **Nothing given, and a doc is open in OWNER's viewer:** sync that doc, and name it in the report.
4. **Otherwise, build the candidate list:** the docs this chat has created, edited or read. With one candidate, sync it. With two or more, ask in one message and wait:

```
Which doc should I sync to GROUP/<target>?
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

| | GROUP/private | GROUP/public |
| --- | --- | --- |
| Source | The doc itself | **Never the doc.** Only its public twin, made and kept current by `/doc-redact` |
| Tabs | Every tab, every time. No questions | Only the twin's tabs OWNER picks for this sync |
| doc.yml | Every tab, with doc_url, doc_id, tab_id, body_id, rev, publish | Only the picked tabs: names, files, revs. No doc link or ids |
| Drawings | Code saved to diagrams/<widget-id>.jsx | The same, for picked tabs only |
| Images | Every picture linked as images/<file> | Only pictures OWNER has cleared for public |
| Before commit | Normal checks | The public gate must pass |

In private, `publish` in doc.yml only decides what goes into the private PDF build. Default: true for every tab, working tabs included.

If the Mirror line names one target and OWNER asks for the other, confirm before going on. A doc can live in both projects, each with its own doc.yml.

**For any public sync, read [references/public.md](references/public.md) first.** It covers finding the twin, the checks before syncing it, and choosing tabs.

## Steps (per doc)

1. **Resolve** the target project, the doc and the slug.
2. **Read** docs/<slug>/doc.yml from the target project. If it's missing, this is a first sync: follow [references/first-sync.md](references/first-sync.md) instead of the steps below. In private, if doc.yml's doc_id isn't this doc's id, stop: that slug belongs to another doc. Report it and ask for a different slug.
3. **Compare the tab list** with doc.yml. A new tab becomes a `create`, a removed tab a `delete`, and a renamed or moved tab a `move` to its new name. File names are NN-<tab-slug>.md, numbered in the doc's tab order (the same numbers in both projects, even when public skips some).
4. **Public only:** run "Choosing tabs for public" from references/public.md now (already answered if several docs were asked about up front).
5. **Find changes.** Read each in-scope tab's body with sinceRev set to its rev in doc.yml. An empty delta means skip it. If nothing changed and the tab list matches, report "No changes" for this doc and move on.
6. **Export** each changed tab as Markdown, as plain text: follow [references/export-as-text.md](references/export-as-text.md). Use the text exactly as exported. To keep output tokens down:
   - For a tab under about 10 KB, send the whole file.
   - For a bigger tab with a small change, read the repo copy (input is cheaper than output), then send `update` actions with `old_str`/`new_str` for just the changed passages. Each `old_str` must be unique in the file.
   - Save a drawing's code only when the drawing is new or changed.
   - If a changed tab has pictures, follow [references/images.md](references/images.md). Never put image bytes in a commit.
7. **Public gate** (public only). Run it on everything you're about to commit, as [references/public-gate.md](references/public-gate.md) says. Also confirm the source is the twin named in `public.yml`, not the original doc. If anything blocks, list it (redacted) with its tab, commit nothing for this doc, and ask OWNER whether to fix the doc or leave that tab out.
8. **Commit once per doc.** One `add_commit` to BRANCH holding every file action for this doc plus its updated doc.yml (each changed tab's new rev, and last_sync: in private as your local ISO time; in public as UTC with a trailing Z, so no time zone shows). Never set author_name or author_email.
   - Subject: `docs(<slug>): <the newest Changelog "What I did", cut to about 70 characters>`, or `docs(<slug>): sync of <tab names>` if there's no new Changelog row.
   - Body lines: `Tabs: ...`, `Removed: ...` (public, if any), `Revs: <tab> old→new, ...`, `Diagrams: ...`, `Images: <linked>, <missing>`, `Target: private|public`, `Sync: manual`.
   - **Moved tabs that also changed:** GitLab refuses a `move` and an `update` of the same file in one commit ("file not found"; nothing is written). Either give the `move` the whole new content, or, when partial edits save a lot of output, make a moves-only commit first (`docs(<slug>): renumber tabs after <reason>`, moving the highest numbers first), then the content commit with its partial edits on the new paths.
9. **Verify.** Run get_commit. For each whole-file update, run get_repository_file with `limit: 1` and check `metadata.size_bytes` against the blob's `bytes` (or, if image links were written in, the size of the text you sent). If one doesn't match, recommit that file whole. Then delete the temporary text copies (references/export-as-text.md, step 4). If the commit fails, retry once, then report the error. The doc is untouched, so nothing is lost.
10. **Report in chat** in one line per doc: doc title, target, slug, tabs synced (and removed, for public), short SHA. If any linked image file is missing from the repo, follow with the **Images to upload** table from references/images.md. Never write the SHA or the sync result into a doc, because that would change a tab and make the next sync dirty.

## Never

- Sync without being asked, or sync public without OWNER's tab answer. On an unattended or scheduled run, skip public entirely and say so.
- Guess which doc OWNER means when several are candidates.
- Commit to GROUP/public from anything but a doc's public twin, or while the twin has open suggestions.
- Edit a twin doc: only `/doc-redact` does that.
- Write `public.yml` or `public-denylist.txt`, or any term from that list, to GROUP/public.
- Put two docs in one commit, or sync a doc into a folder whose doc.yml names a different doc_id.
- Push to GROUP/public a tab OWNER didn't pick, a tab that failed the gate, or a picture they haven't cleared.
- Edit files under docs/ by any other route, or force anything onto BRANCH.
- Put image bytes (base64) in a commit. Images always come from OWNER's upload.
- Delete assets by type or by listing: only the asset ids this run created.
