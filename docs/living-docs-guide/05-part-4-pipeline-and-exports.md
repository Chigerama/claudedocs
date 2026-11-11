Every push to `main` that touches `docs/` or `templates/` runs three jobs. `no-secrets` checks the files, `build-docs` turns each doc's published tabs into PDF, Word and HTML, and `pages` publishes them. Tag a commit `vX.Y` and a fourth job, `release`, attaches the files to a GitLab release.

Both projects carry the same files (`.gitlab-ci.yml`, `build.py`, `templates/`). Change them in private first, check the pipeline, then copy the same change to public.

## The jobs

| Job | Image | Runs when | Does |
| --- | --- | --- | --- |
| `no-secrets` | `ghcr.io/gitleaks/gitleaks` | Every pipeline | Fails if gitleaks finds a token or key, if `HOME_IP` appears in `docs/`, or (public only) if a term from `PUBLIC_DENYLIST` does |
| `build-docs` | `pandoc/extra:3.9-ubuntu` | `docs/`, `templates/`, `build.py` or the CI file changed, or a tag | Runs `build.py`. Artifacts: `build/` for 90 days |
| `pages` | `alpine` | Same changes, on `main` | Publishes `build/site/` as the Pages site |
| `release` | `registry.gitlab.com/gitlab-org/cli` | Tags like `v1.0` | Creates a release that links to the build's zip |

## Step 1 · The CI/CD variables

**HOME\_IP**, on the group, so both projects inherit it: **my-docs → Settings → CI/CD → Variables → Add variable**.

| Field | Value |
| --- | --- |
| Type | Variable (default) |
| Environments | All (default) |
| Visibility | **Masked and hidden**: masked in job logs and never shown again in settings. You can still overwrite it |
| Flags | **Protect variable** ticked; **Expand variable reference** unticked |
| Key | `HOME_IP` |
| Value | Your public IPv4 only: no spaces, no trailing newline |

**PUBLIC\_DENYLIST**, on the **public project only** (private legitimately contains these words): **my-docs/public → Settings → CI/CD → Variables → Add variable**.

| Field | Value |
| --- | --- |
| Type | **File** |
| Environments | All (default) |
| Visibility | Visible (a list of several lines can't be masked; only the project's Maintainers can see it, and the job prints only file names) |
| Flags | **Protect variable** ticked; **Expand variable reference** unticked |
| Key | `PUBLIC_DENYLIST` |
| Value | One identifying term per line: your names and usernames, the bot's username, your real group name, machine and project names, your town or time zone. Matching ignores case and works on whole words, so a short name won't match inside an ordinary word |

Protect variable means only pipelines on protected branches and tags see these: `main` and tags `v*` are protected (Part 1). On the group's CI/CD page, also leave **Default role to use pipeline variables** on No one allowed.

## Step 2 · .gitlab-ci.yml

```yaml
# Docs pipeline (same file in private and public): check for secrets, build PDF/Word/HTML, publish.
stages: [test, build, publish]

workflow:
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  auto_cancel:
    on_new_commit: interruptible

default:
  interruptible: true

no-secrets:
  stage: test
  image:
    name: ghcr.io/gitleaks/gitleaks:latest
    entrypoint: [""]
  script:
    - gitleaks dir --redact --no-banner --verbose .
    # HOME_IP is a masked CI/CD variable; only file names are printed.
    - |
      if [ -n "$HOME_IP" ] && grep -rlF "$HOME_IP" docs/; then
        echo "Home public IP found in the files above: remove it in the doc; the next sync overwrites the file."
        exit 1
      fi
    # PUBLIC_DENYLIST is a file variable set only in the public project; only file names are printed.
    - |
      if [ -n "$PUBLIC_DENYLIST" ] && [ -s "$PUBLIC_DENYLIST" ]; then
        grep -v '^[[:space:]]*$' "$PUBLIC_DENYLIST" > /tmp/denylist
        if [ -s /tmp/denylist ] && grep -rliwFf /tmp/denylist docs/; then
          echo "An identifying term appears in the files above: fix the public twin and sync again."
          exit 1
        fi
      fi

build-docs:
  stage: build
  image:
    name: pandoc/extra:3.9-ubuntu
    entrypoint: [""]
  before_script:
    - apt-get update -qq
    - DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-yaml fonts-dejavu-core > /dev/null
  script:
    - python3 build.py
  artifacts:
    name: "$CI_PROJECT_NAME-$CI_COMMIT_REF_SLUG"
    paths: [build/]
    expire_in: 90 days
  rules:
    - if: $CI_COMMIT_TAG
    - changes: [docs/**/*, templates/**/*, build.py, .gitlab-ci.yml]

pages:
  stage: publish
  image: alpine:3.20
  needs: [build-docs]
  script:
    - cp -r build/site public
  artifacts:
    paths: [public]
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      changes: [docs/**/*, templates/**/*, build.py, .gitlab-ci.yml]

release:
  stage: publish
  image: registry.gitlab.com/gitlab-org/cli:latest
  needs: [build-docs]
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+/
  script:
    - echo "Releasing $CI_COMMIT_TAG"
  release:
    tag_name: $CI_COMMIT_TAG
    name: "Living docs $CI_COMMIT_TAG"
    description: "PDF, Word and HTML for every published doc, built from $CI_COMMIT_SHORT_SHA."
    assets:
      links:
        - name: "All files (zip)"
          url: "$CI_PROJECT_URL/-/jobs/artifacts/$CI_COMMIT_TAG/download?job=build-docs"
          link_type: package
```

## Step 3 · build.py

The script reads each `doc.yml`, joins the tabs marked `publish: true` in order, and runs pandoc three times. It strips the byline under each tab title, replaces each diagram placeholder with a short note, and embeds images linked as `images/<name>`. An image that hasn't been uploaded yet becomes a note, so the build still succeeds. Example image links inside inline code are left alone. No author is printed on the outputs.

```python
#!/usr/bin/env python3
"""Build PDF, Word and HTML for every doc under docs/.

Each docs/<slug>/doc.yml lists the doc's tabs in order; tabs with publish: true
are joined into one document per doc. Output goes to build/<slug>/ and a small
site for GitLab Pages goes to build/site/.

Usage: python3 build.py [pdf] [docx] [html]   (default: all three)
"""
import datetime
import html
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
DOCS, TPL, OUT = ROOT / "docs", ROOT / "templates", ROOT / "build"
FORMATS = sys.argv[1:] or ["pdf", "docx", "html"]

# What the Claude Docs Markdown export leaves where a drawing was.
PLACEHOLDER = re.compile(r"^&#91;embedded content: (.*?)\\\][ \t]*$", re.M)
# ...and where a picture was, if /doc-sync didn't link it (for example not published).
PICTURE = re.compile(r"^&#91;image(?:: (.*?))?\\\][ \t]*$", re.M)
# A Markdown image pointing into the doc's images/ folder. Skips examples in inline code
# (right after a backtick) and placeholders like images/<name>.
IMAGE = re.compile(r"(?<!`)!\[([^\]]*)\]\((images/[\w.-]+)\)")
# The byline under each tab title (a date and a mention). The title page carries the title instead.
BYLINE = re.compile(r"\A(# .*\n)\n[A-Z][a-z]{2} \d{1,2}, \d{4} · @.*\n")


def pandoc(*args):
    print("+ pandoc " + " ".join(str(a) for a in args), flush=True)
    subprocess.run(["pandoc", *map(str, args)], check=True)


def missing_image(folder):
    def swap(m):
        if (folder / m.group(2)).exists():
            return m.group(0)
        print(f"warning: {folder.name}/{m.group(2)} not uploaded yet", flush=True)
        return f"> *Image not uploaded yet: {m.group(2)} ({m.group(1) or 'no caption'}).*"
    return swap


def tab_text(path):
    text = path.read_text(encoding="utf-8")
    text = IMAGE.sub(missing_image(path.parent), text)
    text = BYLINE.sub(r"\1", text)
    text = PLACEHOLDER.sub(lambda m: f"> *Diagram: {m.group(1)}. See the live doc.*", text)
    text = PICTURE.sub(lambda m: f"> *Picture: {m.group(1) or 'no caption'}. See the live doc.*", text)
    return text.strip() + "\n"


def build_doc(folder):
    meta = yaml.safe_load((folder / "doc.yml").read_text(encoding="utf-8"))
    slug = meta["slug"]
    tabs = [t for t in meta["tabs"] if t.get("publish")]
    if not tabs:
        print(f"skip {slug}: no tabs marked publish: true")
        return None
    # \newpage is raw LaTeX: a page break in the PDF, ignored by Word and HTML.
    body = "\n\\newpage\n\n".join(tab_text(folder / t["file"]) for t in tabs)

    synced = str(meta.get("last_sync", ""))[:10]
    try:
        date = datetime.date.fromisoformat(synced).strftime("%-d %B %Y")
    except ValueError:
        date = synced
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    src = out / f"{slug}.md"
    src.write_text(body, encoding="utf-8")

    # --resource-path lets pandoc find images/ relative to the doc's folder.
    common = ["-f", "markdown", "-s", "--toc", "--toc-depth=2", f"--resource-path={folder}",
              "-M", f"title={meta['title']}",
              "-M", f"date={date}", "-M", f"lang={meta.get('lang', 'en')}"]
    files = {}
    if "pdf" in FORMATS:
        pdf = out / f"{slug}.pdf"
        extra = ["--metadata-file", TPL / "pdf.yaml"] if (TPL / "pdf.yaml").exists() else []
        pandoc(src, "-o", pdf, *common, "--template", "eisvogel", "--pdf-engine=xelatex", *extra)
        files["PDF"] = pdf
    if "docx" in FORMATS:
        docx = out / f"{slug}.docx"
        extra = ["--reference-doc", TPL / "reference.docx"] if (TPL / "reference.docx").exists() else []
        pandoc(src, "-o", docx, *common, *extra)
        files["Word"] = docx
    if "html" in FORMATS:
        page = out / f"{slug}.html"
        extra = ["--css", TPL / "style.css"] if (TPL / "style.css").exists() else []
        pandoc(src, "-o", page, *common, "--embed-resources", *extra)
        files["HTML"] = page
    return meta, files


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    built = [r for r in (build_doc(f) for f in sorted(DOCS.iterdir()) if (f / "doc.yml").exists()) if r]
    site = OUT / "site"
    site.mkdir(parents=True, exist_ok=True)
    rows = []
    for meta, files in built:
        links = []
        for label, path in files.items():
            (site / meta["slug"]).mkdir(exist_ok=True)
            shutil.copy(path, site / meta["slug"] / path.name)
            links.append(f'<a href="{meta["slug"]}/{path.name}">{label}</a>')
        rows.append(f"<li><strong>{html.escape(meta['title'])}</strong>: {' · '.join(links)}"
                    f" <small>(synced {html.escape(str(meta.get('last_sync', '')))})</small></li>")
    (site / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Living docs</title>"
        "<h1>Living docs</h1><ul>" + "".join(rows) + "</ul>", encoding="utf-8")
    print(f"built {len(built)} doc(s) into {OUT}")


if __name__ == "__main__":
    main()
```

## Step 4 · Templates

**templates/pdf.yaml**: Eisvogel settings for every PDF. A4, a navy title page, contents on its own page, DejaVu Sans so arrows and middots print. Change colours and fonts here.

```yaml
# Eisvogel settings for every PDF (github.com/Wandmalfarbe/pandoc-latex-template).
papersize: a4
geometry: "margin=2.2cm"
fontsize: 10pt
mainfont: "DejaVu Sans"        # has the → · – glyphs the docs use
monofont: "DejaVu Sans Mono"
titlepage: true
titlepage-color: "1F3A5F"
titlepage-text-color: "FFFFFF"
titlepage-rule-color: "FFFFFF"
titlepage-rule-height: 2
# titlepage-logo: "templates/logo.png"
toc-own-page: true
colorlinks: true
header-left: "\\thetitle"
footer-left: "my-docs"
table-use-row-colors: true
code-block-font-size: "\\footnotesize"
```

**templates/style.css**: the HTML look, embedded into each page.

```css
/* HTML look for the docs pages */
body { max-width: 52rem; margin: 2rem auto; padding: 0 1rem; font: 16px/1.55 system-ui, sans-serif; color: #1d1d1f; }
h1, h2, h3 { line-height: 1.25; color: #1f3a5f; }
table { border-collapse: collapse; width: 100%; font-size: 0.92em; }
th, td { border: 1px solid #d0d7de; padding: 0.35rem 0.6rem; vertical-align: top; }
th { background: #f0f3f6; }
code { font-size: 0.9em; background: #f6f8fa; padding: 0.1em 0.3em; border-radius: 4px; }
pre code { display: block; padding: 0.8rem; overflow-x: auto; }
blockquote { color: #57606a; border-left: 3px solid #d0d7de; margin-left: 0; padding-left: 1rem; }
nav#TOC { background: #f6f8fa; padding: 0.5rem 1rem; border-radius: 6px; }
```

**templates/reference.docx**: optional Word styles. Run `pandoc -o reference.docx --print-default-data-file reference.docx` once, change the Heading and Normal styles in Word, and save. `build.py` uses it if it's there.

**templates/logo.png**: optional. Add it, then uncomment `titlepage-logo` in `pdf.yaml`.

## Step 5 · Commit and check

Ask Claude to commit the four files to private in one `add_commit` with message `ci: pipeline, build script and templates`. Then:

1. **Build → Pipelines**: `no-secrets`, `build-docs` and `pages` all go green. The first `build-docs` takes a few minutes while it pulls the image. A pipeline with a yaml invalid badge and no jobs usually means the bot account isn't verified yet (Part 2, step 0); hover the badge for the reason.
2. Open `build-docs` → **Browse** artifacts → `build/<slug>/` and read the PDF: title page, contents, every published tab, diagram notes where the drawings were.
3. Copy the same files to public.
4. **Pages access:** **Deploy → Pages** shows each site's address; access is set in **Settings → General → Visibility, project features, permissions → Pages**. A private project already allows only project members; set public to **Everyone**.
5. Tag `v0.1` in private (**Code → Tags → New tag**, from `main`). The tag's pipeline creates the release by itself; check its **All files (zip)** link downloads.

## Step 6 · Optional: real diagrams in the PDF

The mirror commits each drawing's source to `docs/<slug>/diagrams/<widget-id>.jsx`. Drawings are React code that returns SVG, so a Node job could render them to SVG before `build-docs`, and `build.py` could put an image where each placeholder sits. Not built yet. Until then, the PDF gives the caption, and the doc's own Export → PDF includes the drawings.

## Done when

- [ ] `HOME_IP` is set on the group, and `PUBLIC_DENYLIST` on the public project
- [ ] The pipeline on `main` is green in both projects
- [ ] The PDF, Word and HTML open and read correctly
- [ ] Pages: private for members only, public for everyone
- [ ] A `v0.1` tag produced a release with a working download link
