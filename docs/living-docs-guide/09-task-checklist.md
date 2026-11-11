Every build step, ready to paste into a to-do app such as TickTick. The Part tabs stay the source of truth; this list points back at them.

## How to load it

1. Make a list called **Living Docs**.
2. Copy the block below and paste it into the add-task box. If the app asks whether to add each line as a separate task, choose yes.
3. If your app turns hashtags into tags, you can filter by phase (#p0 to #p5).
4. For tasks with several steps, paste their step list into the task's description.
5. Set the recurring tasks' repeat by hand.

## List · Living Docs

```text
P0: choose the group and project names and how doc folders are named #p0
P1: create the group; turn on Sign web-based commits #p1
P1: create <group>/private (Private) with a README #p1
P1: create <group>/public (Public) with a README #p1
P1: apply the project settings table to both projects #p1
P1: protect main (Developers + Maintainers push) and tags v* (Maintainers) in both #p1
P2: create Claude's GitLab account (own email, 2FA, private profile) #p2
P2: complete identity verification for Claude's account #p2
P2: save its login and recovery codes in your password manager #p2
P2: invite it to the group as Developer, nothing else #p2
P2: group: MCP client access, Allow connection to GitLab #p2
P2: add the GitLab custom connector; approve OAuth signed in as the bot #p2
P2: set the connector's tool permissions (Part 2 table) #p2
P2: lock test: your other project not found; skeleton commits Verified #p2
P3: save the doc-sync skill #p3
P3: /doc-sync private on your first doc (first mirror) #p3
P3: add the Mirror line to its Claude context #p3
P3: make one small edit, /doc-sync private, check only that tab moved #p3
P3: paste a test screenshot, /doc-sync, upload it under the name given #p3
P4: add HOME_IP on the group (masked and hidden, protected) #p4
P4: Claude commits .gitlab-ci.yml, build.py and templates to private #p4
P4: pipeline green; check the PDF, Word and HTML #p4
P4: copy the pipeline files to public #p4
P4: Pages: private members only, public Everyone #p4
P4: tag v0.1 in private and check the release download #p4
P5: add PUBLIC_DENYLIST to the public project #p5
P5: make the public twin of one doc and review every tab #p5
P5: /doc-sync public; check both leak checks passed #p5
P5: switch Create commit to Always allow after three clean syncs #p5
P5: restore test into a scratch doc, then delete it #p5
Later: optional nightly sweep of private #later
Later: diagram render job for the PDF #later
Later: push mirror to a self-hosted Git server #later
```

## Step lists

**P2: smoke test**

```text
get_user is the bot account
list_projects shows only your two docs projects
get_project on another of your projects fails
One add_commit per project: README.md, .gitignore, .gitattributes, docs/.gitkeep, templates/.gitkeep
Code → Commits: author is the bot, Verified badge
```

**P5: public twin**

```text
Ask Claude for the public twin of the doc
Read every tab; search it for your names, usernames and places
Fix anything left, in the twin
/doc-sync public; answer the tab question
Check the public pipeline's no-secrets job passed
```

## Recurring tasks

| Task | Repeat |
| --- | --- |
| Run /doc-sync on edited docs | Weekly |
| Cut release tags | Monthly |
| Review the bot's memberships and authorised application | Every 3 months |
| Restore test | Every 6 months |
