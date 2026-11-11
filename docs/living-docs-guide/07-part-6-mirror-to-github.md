If GitLab.com Pages asks anonymous visitors to sign in more often than you'd like, the public project can also go to GitHub. GitLab push-mirrors `my-docs/public` to a GitHub repo after every push, and a GitHub Actions workflow builds the same PDF, Word and HTML and publishes them on GitHub Pages. Private never leaves GitLab.

## How it works

| Piece | Where | Does |
| --- | --- | --- |
| Push mirror | my-docs/public → Settings → Repository → Mirroring repositories | After each push to `main`, pushes the same commits to GitHub, usually within a few minutes |
| GitHub repo | github.com/\<your GitHub username>/\<repo> | A read-only copy. Anything changed there is overwritten by the next mirror |
| `.github/workflows/pages.yml` | In both GitLab projects, like the other pipeline files | Runs only on GitHub (GitLab ignores `.github/`): builds with `build.py` and deploys `build/site/` to GitHub Pages |
| Fine-grained token | Your GitHub account | Lets GitLab push to that one repo. Expires; renew it before it does |

## Step 0 · What becomes public on GitHub

- The whole Git history of `my-docs/public`: every commit message, author name and date. The commits are by `docs-bot`, so its username goes across too.
- Your GitHub username, in the repo and Pages addresses.
- GitHub attributes a commit to a GitHub user only when the commit email matches a verified email on that user; otherwise it shows the name and email from the commit. The bot uses its no-reply address, so nothing private shows.
- Nothing from `my-docs/private`. The mirror is set on the public project only.

## Step 1 · Create the GitHub repo

1. Signed in to GitHub, go to **+ → New repository**.
2. Name it, for example `living-docs`. Visibility **Public**.
3. Leave **Add a README**, **.gitignore** and **license** unticked: the repo must start empty, or the first mirror is refused.
4. **Create repository**.

## Step 2 · Create the token

1. GitHub → your avatar → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Name `gitlab-push-mirror`. Expiration: up to a year; put the date in your recurring tasks.
3. **Repository access: Only select repositories** → the new repo.
4. **Repository permissions:** **Contents: Read and write** and **Workflows: Read and write**. The second is needed because the repo contains `.github/workflows/`; without it GitHub refuses the push. Metadata (read) is added by itself.
5. **Generate token**. Copy it straight into your password manager; GitHub shows it once. Never paste it into chat or the doc.

## Step 3 · Turn on GitHub Pages

In the GitHub repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Do this before the first mirror, so the first workflow run can deploy.

## Step 4 · The workflow file

Claude commits `.github/workflows/pages.yml` to `my-docs/private`, then the same file to `my-docs/public`, with message `ci: GitHub Pages workflow for the GitHub mirror`. It reuses the GitLab build: same image, same `build.py`.

```yaml
# GitHub Pages for the GitHub mirror of the public project (same file in private and public).
# GitLab ignores .github/; this only runs on GitHub, after the push mirror delivers a commit.
name: pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    container: pandoc/extra:3.9-ubuntu
    steps:
      - uses: actions/checkout@v5
      - name: Install Python and fonts
        run: |
          apt-get update -qq
          DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-yaml fonts-dejavu-core > /dev/null
      - name: Build PDF, Word and HTML
        run: python3 build.py
      - uses: actions/upload-pages-artifact@v4
        with:
          path: build/site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## Step 5 · Set up the push mirror

In GitLab, signed in as yourself (not the bot): **my-docs/public → Settings → Repository → Mirroring repositories → Add new**.

| Field | Value |
| --- | --- |
| Git repository URL | `https://github.com/<your GitHub username>/<repo>.git` |
| Mirror direction | Push |
| Authentication method | Username and Password |
| Username | Your GitHub username |
| Password | The token from step 2 |
| Keep divergent refs | Off |
| Mirror only protected branches | **On**, so only `main` goes across |

Then **Mirror repository**. Never add a mirror to `my-docs/private`.

## Step 6 · Test it

1. In the mirror's row, select **Update now**. After a minute the row shows the last successful update.
2. On GitHub, the repo now has the same commits. **Actions** shows a `pages` run: `build`, then `deploy`.
3. Open `https://<your GitHub username>.github.io/<repo>/` without signing in: the same index of PDF, Word and HTML as GitLab Pages.

## Running it

- **Never edit on GitHub.** The mirror overwrites anything that differs, the same rule as `docs/` in GitLab.
- **Token expiry.** When the token expires the mirror stops quietly; the row under Mirroring repositories shows the error. Make a new token, then edit the mirror's password.
- **A failed GitHub build** doesn't touch GitLab. Read the run under the repo's **Actions** tab; the GitLab pipeline still runs the leak checks before anything is pushed.
- **GitLab Pages** can stay on, or be turned off in `my-docs/public` once GitHub Pages works.

## Done when

- [ ] The GitHub repo exists, public, and started empty
- [ ] The fine-grained token covers only that repo, with Contents and Workflows read and write, and is saved in your password manager
- [ ] GitHub Pages source is GitHub Actions
- [ ] `.github/workflows/pages.yml` is in both GitLab projects
- [ ] The push mirror on `my-docs/public` shows a successful update
- [ ] The GitHub Pages site opens without signing in
- [ ] Token renewal is in your recurring tasks
