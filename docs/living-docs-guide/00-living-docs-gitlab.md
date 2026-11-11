Every Claude Doc in this system has a twin in GitLab. Claude exports each changed tab as Markdown and commits it through GitLab's own MCP server. A pipeline then builds PDF, Word and HTML from the repo, giving you version history with real diffs, your own branded templates, one place to publish from, and an off-platform backup.

## How it works

&#91;embedded content: mirror flow · doc to GitLab to published files\]

You and Claude edit the doc as usual. When you run /doc-sync with private or public as the target, Claude exports the tabs that changed as Markdown and commits them to `main` in a single commit. GitLab signs the commit, and the pipeline rebuilds the published files. If the doc is ever lost, the repo holds every tab's Markdown and its full history, enough to rebuild it.

## Names used in this guide

The guide uses example names. Swap in your own everywhere they appear.

| In this guide | What it is |
| --- | --- |
| `my-docs` | Your GitLab group for the mirror |
| `my-docs/private` | The full mirror: every tab of every doc, and the backup |
| `my-docs/public` | Generic, redacted copies you're happy to publish |
| `docs-bot` | Claude's own GitLab account, a Developer on `my-docs` only |
| Your account | Your normal GitLab account, Owner of `my-docs` |
| `my-guide` | An example doc's folder name (its slug) |
| `HOME_IP` | A CI/CD variable holding your home public IP, so the pipeline can check it never appears |

## Design decisions

The doc is the source of truth and GitLab is a one-way mirror of it: Claude writes, GitLab keeps history and builds outputs.

| Decision | Choice | Why |
| --- | --- | --- |
| Where the mirror lives | A group with two projects: `my-docs/private` (every tab) and `my-docs/public` (redacted copies). One folder per doc under `docs/` in each | One pipeline and one template set for every doc. Each doc's history still filters by path: `git log -- docs/<slug>/` |
| How Claude writes to GitLab | GitLab's official MCP server, `https://gitlab.com/api/v4/mcp`, added to Claude as a custom connector with OAuth | Works on GitLab's Free tier. Its `add_commit` tool writes several files in one commit, from any Claude session: phone, web, desktop and scheduled tasks |
| Why not `git push` from Claude | Not used | Claude's cloud workspace can't reach gitlab.com directly, so there is nothing to push from |
| Commit path | Straight to `main`. `main` stays protected: Developers and Maintainers may push, force push is off | Review happens in the doc. A merge request per sync is ceremony with nobody else to review it |
| Signing | Sign web-based commits on for the group | Commits made through the API count as web-based commits, so GitLab signs them and they show Verified. No keys on Claude's side |
| Source format | Markdown, one file per tab, from the Claude Docs export | Clean GitHub-style Markdown with tables and task lists, so diffs read line by line |
| Trigger | Manual: the /doc-sync command, with private or public as the target. A nightly catch-up is optional | A sync costs tokens only when you ask for one |
| What gets published | Private: every tab. Public: a separate, redacted twin of the doc that you review before each sync | Nothing personal can reach the public repo without passing your review and two leak checks |
| Builder | `pandoc/extra` image: pandoc, LaTeX and the Eisvogel template | One image builds PDF, Word and HTML |
| Secrets | gitleaks, a home-IP check and, in public, a check against your own list of identifying words | A private repo is still another copy, and a public one is forever |

## Build phases

About half a day all told: five phases, each with its own tab and a Done-when check. The Task checklist tab has them as tasks.

1. **Phase 0 · Decide (15 min).** Pick the group and project names and how each doc's folder is named.
   - Done when: the names are in the Claude context tab.
2. **Phase 1 · GitLab project (30 min).** Create the group and both projects, protect `main`, turn on signing. See Part 1.
   - Done when: both projects exist with every setting in Part 1's table applied.
3. **Phase 2 · Connector (30–60 min).** Create Claude's own account, verify it, add it to the group as a Developer, allow MCP access, add the custom connector, run the lock test and a test commit. See Part 2.
   - Done when: Claude lists only your two projects through the connector, and its test commit shows Verified.
4. **Phase 3 · First mirror (30 min).** Run /doc-sync private on your first doc. See Part 3.
   - Done when: every tab has its `.md` in `docs/<slug>/`, and the Changelog has the matching row.
5. **Phase 4 · Pipeline (1–2 h).** Add the CI/CD variables, `.gitlab-ci.yml`, the build script and the templates. Tune the PDF's look. See Part 4.
   - Done when: a push to `main` builds PDF, Word and HTML, and a version tag makes a release.
6. **Phase 5 · Public and proof (1 h).** Make the public twin of a doc, review it, run /doc-sync public, and run a restore test into a scratch doc. See Parts 3 and 5.
   - Done when: public has a redacted doc that passed both leak checks, and the restore test passed.

## Limits and gotchas

- **Not live.** A commit only happens when you run /doc-sync (or the optional nightly task runs). Until then, GitLab is one sync behind.
- **One way only.** An edit made in GitLab is overwritten by the next mirror. The only time the repo flows back into a doc is a restore (Part 5).
- **Tokens per sync.** Each sync sends whole tabs through the conversation, so Claude mirrors only the tabs whose revision changed (tracked in `doc.yml`).
- **Not everything survives Markdown.** A drawing becomes a one-line placeholder with its caption; a date chip becomes plain text in US format; a mention becomes "@Name". So the mirror also commits each drawing's source code (Part 3) so restores are exact.
- **Claude's account needs identity verification.** A new GitLab.com account can't run CI jobs on GitLab's shared runners until it's verified, and its pipelines fail with a "yaml invalid" badge. Part 2 covers it.
- **Never set commit author fields.** With signing on, GitLab rejects API commits whose author differs from the caller.
- **Rate limits.** GitLab.com Free allows 60 MCP requests a minute and 3,600 an hour per user. A sync uses a handful.
- **Prompt injection.** MCP tools act on whatever they read. Use the connector only on your own group, and keep its write tools on Needs approval until the loop has proven itself.
- **Escaped underscores.** The export writes `SOME\_NAME`, not `SOME_NAME`. It renders correctly and the diffs stay stable, so leave it.
