Once the loop and pipeline work, the system runs on five routines: onboarding a doc, publishing a public twin, cutting a release, restoring, and fixing the odd failure. Each has a prompt you can paste.

## Onboard a doc

```text
/doc-sync private <doc link>
```

The first sync of a doc is its onboarding. Claude suggests a slug for you to confirm, writes `docs/<slug>/doc.yml` with every tab set to publish: true, commits every tab as `docs(<slug>): first mirror`, and gives you the Mirror line to add to the doc's Claude context.

## Publish a public twin

```text
/doc-redact <doc link>
```

Read the whole twin, fix anything in it directly, then run `/doc-sync public <twin link>`. From then on, run `/doc-redact` again after editing the original: it carries the changes into the twin as suggestions for you to accept, then `/doc-sync public` commits the twin.

## Cut a release

Tag `main` when a doc reaches a milestone. The MCP server can list tags but not create them, so tag it yourself:

- **GitLab:** Code → Tags → New tag, name `v1.0`, from `main`, with a one-line message.
- **A local clone:** `git tag -a v1.0 -m "Milestone"` then `git push origin v1.0`.

The tag's pipeline builds the files and the `release` job creates the release with a link to them.

## Restore

| Situation | First try | Then |
| --- | --- | --- |
| A bad edit in one tab | The doc's own version history | Restore that tab from GitLab (below) |
| A tab deleted, or a doc wrecked | Version history | Full restore into a new doc |
| The doc is gone | Nothing in Claude | Full restore into a new doc |
| You want the doc as it was on a date | Version history, if recent | Restore from the commit or tag for that date |

The full restore prompt:

```text
Restore <slug> from my-docs/private at ref <main | tag | commit ID>.
1. Read docs/<slug>/doc.yml and every tab file it lists, at that ref.
2. Create a new doc titled "<title>" with the same tabs, names and order, each
   filled from its Markdown. Recreate each drawing from diagrams/<widget-id>.jsx
   where its caption placeholder sits.
3. Show me the new doc. Once I confirm, update doc.yml with the new doc link and
   ids, set every rev to the new tabs' revisions, and commit
   "docs(<slug>): restored into new doc from <ref>".
```

What comes back as plain text: date chips (in US format), mentions and dropdowns. Recreate the ones that matter, such as a Changelog's Track column.

**Restore test.** Restore one doc from `main` into a scratch doc. Check the tab count matches, tables and code blocks read correctly, and drawings came back. Log the result in Documentation, then delete the scratch doc. Don't commit its ids.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connector errors 403 on every call | MCP client access is off on the group, or the bot isn't a member | Part 2, step 1 |
| Claude can see your other projects | The connector was authorised while signed in as yourself | Revoke the grant in your Authorized applications, then reconnect as the bot (Part 2, step 3) |
| Push to main refused for the bot | main still allows only Maintainers to push | Branch rules → main → Allowed to push and merge: Developers + Maintainers |
| Pipeline fails with a yaml invalid badge and no jobs | The bot account isn't identity-verified | Verify it (Part 2, step 0), then run the pipeline again |
| Connector asks to sign in again | OAuth grant expired or revoked | Reconnect it in Claude's connector settings |
| `add_commit` refused over the author | Author fields were set | Send the commit with no author fields |
| `add_commit` says the file already exists, or doesn't | `doc.yml` is out of step with the repo | Ask Claude to rebuild `doc.yml` from the repo tree and the doc's tab list, then sync |
| Commit not Verified | Sign web-based commits is off | Turn it on (Part 1). Old commits stay unverified |
| 429 Too Many Requests | Rate limit: 60 a minute on Free | Wait for the `Retry-After` time. Don't retry in a loop |
| `build-docs`: missing character warnings | The font lacks a glyph | Change `mainfont` in `pdf.yaml` |
| `no-secrets` fails on the denylist in public | An identifying term reached the public twin | Fix the twin, sync again, and decide whether the history needs rewriting |
| `no-secrets` fails on a secret or `HOME_IP` | A real secret or your IP is in the doc | Fix it in the doc first, then sync. The old commit keeps it: revoke the secret |

## Later

- **Real diagrams in the PDF**: the render job in Part 4, step 6.
- **A second backup**: push mirroring under Settings → Repository → Mirroring repositories, to a self-hosted Git server.
- **Self-hosted GitLab**: the MCP endpoint becomes `https://<your-host>/api/v4/mcp`, and Claude's cloud must be able to reach it.
- **Your own runner**: a GitLab Runner on your own hardware avoids the shared runners, and with them the identity-verification requirement.
