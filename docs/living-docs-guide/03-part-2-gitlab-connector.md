Claude writes to GitLab through [GitLab's own MCP server](https://docs.gitlab.com/user/model_context_protocol/mcp_server/) at `https://gitlab.com/api/v4/mcp`. It's on the Free tier and signs in with OAuth. Add it once as a custom connector and it works in every Claude session on your account, including your phone and scheduled tasks.

## Pick the route

| Route | Reaches GitLab from | Auth | Use it when |
| --- | --- | --- | --- |
| **Custom connector** (recommended) | Anthropic's cloud, so any session | OAuth, scope `mcp` | Always, unless step 3 fails |
| Claude Desktop with `mcp-remote` | Only a session linked to that computer | OAuth in the browser | Fallback if the custom connector's OAuth won't complete |
| Fine-grained personal access token | Either of the above | Token with the MCP tool resource and Execute | If OAuth is a dead end. Legacy, project and group tokens are refused |

A community GitLab MCP server isn't needed: GitLab's own server has `add_commit`, which commits several files in one call.

## Step 0 · Claude's own GitLab account

Claude connects as a separate GitLab user, `docs-bot`, who belongs to `my-docs` and nothing else. The boundary is GitLab's own membership check on every call, not a setting Claude could get around. Do this before connecting anything.

|  | docs-bot can | docs-bot can't |
| --- | --- | --- |
| Reach | `my-docs/private` and `my-docs/public`. Public projects anywhere, read-only, like any signed-in user | Any other group or project of yours |
| Write | Commit and push to `main` in both projects; create branches and merge requests | Change project or group settings, branch rules or CI/CD variables; create projects or release tags; force push |
| Sign-in | OAuth through the Claude connector only | SSH keys and personal access tokens: it has none |

**Create the account**

1. Pick an email address you control that isn't on your main account. GitLab needs a unique, verified address per user; an alias works.
2. Open a **private browser window**, so your own session isn't affected, and go to gitlab.com → **Register**. Username `docs-bot` (or similar), full name something like `Claude (docs bot)`. Save the login in your password manager.
3. Verify the email.
4. **Complete identity verification** at `https://gitlab.com/-/identity_verification`: a phone number, or a credit card if asked. Nothing is charged. Sign-up doesn't insist on it, and account settings have no link to it, but without it every pipeline started by the bot's commits fails with "Identity verification is required in order to run CI jobs", shown as a yaml invalid badge.
5. Turn on two-factor authentication. Save the recovery codes in your password manager and on paper.
6. **Edit profile**: tick **Private profile**. Under **Emails**, set the commit email to the private no-reply address.
7. Add no SSH keys and no access tokens. The account only ever signs in through the connector's OAuth.
8. GitLab's sign-up makes a new account create a first group and project. Delete them so the account owns nothing: open that group → Settings → General → Advanced → Delete group. GitLab.com may keep it, marked for deletion, for a waiting period. Then sign out.

**Give it the two projects, and nothing else**

1. Signed in as yourself (Owner of `my-docs`), go to **my-docs → Manage → Members → Invite members**.
2. Username `docs-bot`, role **Developer**. An access expiry date is optional. **Invite**.
3. In **both** projects, check **Settings → Repository → Branch rules → main**: **Allowed to push and merge** is **Developers + Maintainers**, **Allowed to merge** is Maintainers, **Allowed to force push** is off.
4. Never add `docs-bot` to another group or project. If you need another docs project, create it inside `my-docs`.

## Step 1 · Allow MCP on the group

1. Go to **my-docs → Settings → General → Permissions and group features → MCP client access**, select **Allow connection to GitLab**, and save. GitLab turns this on by default for top-level groups; check it anyway.
2. Optional extra layer: clear the same setting on your other top-level groups. Treat it only as a backup: the real lock is the separate account.

## Step 2 · Add the custom connector

Custom connectors need a paid Claude plan.

1. In Claude, open **Settings → Connectors** (in the desktop app, **Customize → Connectors**) and choose **Add custom connector**.
2. Name: `GitLab`. Remote MCP server URL: `https://gitlab.com/api/v4/mcp`.
3. **Authentication: Sign in now.** Every GitLab tool needs a signed-in user.
4. **OAuth client: Register automatically.** GitLab supports dynamic client registration. Only pick "Use your own OAuth client" if step 3 fails.
5. **Request headers:** add none.
6. **Add**. Then sign in to GitLab as `docs-bot` (step 3) before you click **Connect**.

## Step 3 · Approve the OAuth request

The OAuth page approves for **whoever is signed in to GitLab in that browser**, so get this right:

1. Before you click **Connect** in Claude, sign out of your own account in that browser and sign in as **docs-bot**.
2. Click **Connect**. GitLab opens an authorisation page asking for the `mcp` scope.
3. Check the URL is gitlab.com and the avatar at the top right is **docs-bot**, then **Authorize**.
4. Sign out of docs-bot and back in as yourself.

The grant appears under docs-bot's **User settings → Applications → Authorized applications**, which is where you revoke it. If you ever connected while signed in as yourself, revoke that grant in your own Authorized applications, then disconnect and reconnect.

Fallback if it won't complete: Claude Desktop with this in `claude_desktop_config.json` (Settings → Developer → Edit Config); it needs Node.js 20 or later. It only works from sessions linked to that computer.

```json
{
  "mcpServers": {
    "GitLab": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://gitlab.com/api/v4/mcp"]
    }
  }
}
```

## Step 4 · Tool permissions

Claude's connector settings list tools by display name, in two groups:

| Group / tool (display name) | GitLab tool | Setting | Why |
| --- | --- | --- | --- |
| **Read-only tools** (whole group) | get\_*, list\_*, search | Always allow | Claude checks state before every sync |
| Create commit | add\_commit | Needs approval, then **Always allow** after three clean syncs | The sync's one write. A scheduled sync can't stop for approval |
| Create branch | add\_branch | Needs approval | Only for changes you ask for |
| Create or update merge request | save\_merge\_request | Needs approval | Same |
| Add comment | save\_note | Needs approval | Same |
| Merge merge request | accept\_merge\_request | Off | You merge, not Claude |
| Comment on or review merge request | save\_merge\_request\_review | Off | Not part of this system |
| Fork project | fork\_repository | Off | Not part of this system |
| Create project | save\_project | Off | Also blocked in GitLab (Maintainers only) |
| Run or update pipeline | save\_pipeline | Off | Pipelines run on push |
| Create or update work item | save\_work\_item | Off | Not part of this system |
| Link work items | link\_work\_items | Off | Not part of this system |

**Manual vs Auto mode.** These choices apply in **Manual** mode. In **Auto** mode Claude may act without asking unless an automated check flags the action. Use Manual mode in chats where you want to approve each commit.

## Step 5 · Smoke test, which commits the skeleton

Paste into a new chat:

```text
Using the GitLab connector:
1. get_user for the signed-in user: confirm it is docs-bot. If it's my own account, stop.
2. list_projects, membership only: expect exactly my-docs/private and my-docs/public.
3. get_project <one of my other private projects>: this must FAIL (not found).
   If it succeeds, stop and tell me.
4. In each my-docs project, one add_commit to main, message "Skeleton": update
   README.md and create .gitignore, .gitattributes, docs/.gitkeep and
   templates/.gitkeep with the contents in Part 1, step 5 of the build guide.
5. get_commit on both new commits and report the author.
```

In GitLab, open **Code → Commits** in each project. Each commit's author should be **docs-bot**, with the green **Verified** badge. Step 3 is the lock test: if Claude can read your other project, the connector is signed in as the wrong user.

## Step 6 · Security notes

- The OAuth grant acts as **docs-bot**: a Developer on `my-docs` and nothing else. GitLab checks its permissions on every call.
- GitLab warns that MCP tools can be steered by text they read. With this account, the most such text could touch is `my-docs`.
- Never let Claude set `author_name` or `author_email` on a commit.
- Rate limits on Free are 60 MCP requests a minute and 3,600 an hour, per user. docs-bot has its own allowance.
- If something looks wrong: remove docs-bot from `my-docs` (Members → Remove), then revoke its grant.

## Done when

- [ ] docs-bot exists, verified, with 2FA, a private profile and the no-reply commit email
- [ ] docs-bot is a Developer on `my-docs` and a member of nothing else
- [ ] MCP client access is allowed on `my-docs`
- [ ] The GitLab connector shows Connected and is authorised as docs-bot
- [ ] The tool permissions match the table
- [ ] Smoke test: your other project not found; skeleton commits by docs-bot, Verified
