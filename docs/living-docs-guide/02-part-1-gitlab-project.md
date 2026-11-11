The group `my-docs` holds two projects with the same layout. `my-docs/private` is the full mirror: every tab of every doc, and the backup. `my-docs/public` holds redacted copies you're happy to share. Developers may push to `main` in both, because Claude's sync commits go straight there from its own Developer account, `docs-bot` (Part 2, step 0).

## Step 1 · Create the group and projects

In a browser, signed in as yourself:

1. **Group.** Create the group `my-docs`. It must be public if you want a public project in it; a private project inside it stays private.
2. **Group settings first.** In **my-docs → Settings → Repository → General**, tick **Sign web-based commits**. Both projects inherit it.
3. **Private project.** In **my-docs → New project → Create blank project**, name it `private` with visibility **Private**. Tick **Initialize repository with a README**. Leave **SAST**, **Secret Detection** and **SHA-256** unticked: the pipeline brings its own checks (Part 4), and SHA-256 is experimental and can't be undone.
4. **Public project.** Do the same with name `public` and visibility **Public**.
5. Apply Step 2's table to **both** projects.

## Step 2 · Project settings

| Setting | Where | Value | Why |
| --- | --- | --- | --- |
| Protect `main` | Settings → Repository → Branch rules → main | Allowed to merge: Maintainers. Allowed to push and merge: Developers + **Maintainers**. Allowed to force push: **off** | `docs-bot` (Developer) commits to `main` directly. History can't be rewritten |
| Protect tags `v*` | Settings → Repository → Protected tags | Allowed to create: **Maintainers** | Release pipelines get protected variables, and only you can cut a release |
| Sign web-based commits | Settings → Repository → General | **On** (inherited from the group) | GitLab signs commits made through the API, so every mirror commit shows Verified |
| Delete source branch by default | Settings → Merge requests | On | Only for the odd hand-made merge request |
| Merge method | Settings → Merge requests | Merge commit | Simple history |
| Instance runners | Settings → CI/CD → Runners | On (the default) | The pipeline runs on GitLab's shared runners |
| Minimum role to use pipeline variables | Settings → CI/CD → Variables | No one allowed | Nobody can override variables when starting a pipeline by hand |
| Labels | Manage → Labels | `docs`, `template`, `pipeline`, `restore` | Optional; for issues about the system itself |

On the group, under **Settings → General → Permissions and group features**, also set **Minimum role required to create projects** to **Maintainers** and require two-factor authentication for all members.

## Step 3 · Repository layout

```text
private/   (public/ is laid out the same)
├── README.md
├── .gitlab-ci.yml            # Part 4
├── .gitignore                # build/
├── .gitattributes            # line endings
├── build.py                  # Part 4: turns docs/ into PDF, Word, HTML
├── templates/
│   ├── pdf.yaml              # Eisvogel settings: colours, logo, title page
│   ├── reference.docx        # Word styles (optional)
│   ├── style.css             # HTML look
│   └── logo.png              # optional
└── docs/
    └── my-guide/             # one folder per doc, named by its slug
        ├── images/           # pictures you upload, named by /doc-sync (Part 3)
        ├── diagrams/         # each drawing's source code
        ├── doc.yml           # the manifest: doc link, tabs, order, revisions
        ├── 00-my-guide.md
        ├── 01-claude-context.md
        └── ...
```

File names are the tab's position (two digits) plus a slug of its name. Claude keeps the numbers in step with the doc's tab order; a renamed or moved tab becomes a `move` action in the same commit, so its history follows it.

## Step 4 · The manifest, doc.yml

Each doc folder has one `doc.yml`. Claude writes it and keeps it current; you only change `publish`. The `rev` per tab is the tab's revision at the last sync: Claude asks the doc for changes since that revision and skips tabs that have none.

```yaml
# docs/my-guide/doc.yml  (kept current by Claude)
title: "My guide"
slug: my-guide
doc_url: <the doc's link>
doc_id: <doc id>
author: <you>
lang: en
last_sync: "<date and time of the last sync>"
tabs:
  - file: 00-my-guide.md
    name: "My guide"
    tab_id: <tab id>
    body_id: <body id>
    rev: 0
    publish: true
  - file: 01-claude-context.md
    name: "Claude context (CLAUDE.md)"
    tab_id: <tab id>
    body_id: <body id>
    rev: 0
    publish: true
  # ...one entry per tab, in the doc's order
```

`publish` decides which tabs go into the built PDF, Word and HTML. Default: true for every tab. In `my-docs/public`, `doc.yml` lists only names, files and revisions, with no doc link or ids, so nothing in the public repo points back to a private doc.

## Step 5 · Skeleton files

These go in with the first commit. The easiest way is to let Claude commit them as the connector test in Part 2, step 5, which proves the whole write path.

**README.md**

```markdown
# my-docs/private   (in public: # my-docs/public)

Mirror of Claude Docs. The Claude doc is the source of truth: don't edit docs/ here,
changes are overwritten by the next sync. Templates and the pipeline are edited here.

- docs/<slug>/doc.yml lists each doc's tabs and what gets published
- Each push to main builds PDF, Word and HTML (job artifacts; Pages from main)
- Tag vX.Y to cut a release with the files attached
```

**.gitignore**

```text
build/
public/
*.log
.env
```

**.gitattributes**

```text
* text=auto eol=lf
*.docx binary
*.png binary
*.pdf binary
```

## Done when

- [ ] `my-docs/private` (Private) and `my-docs/public` (Public) exist, each with a README
- [ ] `main` is protected: Developers + Maintainers push, Maintainers merge, force push off
- [ ] Tags `v*` are protected, Maintainers create
- [ ] Sign web-based commits is on at the group
- [ ] Instance runners are on
