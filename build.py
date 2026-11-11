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
# The byline under each tab title: "Nov 11, 2026 · @Dan". The title page carries it instead.
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
              "-M", f"date={date}", "-M", f"lang={meta.get('lang', 'en-AU')}"]
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
