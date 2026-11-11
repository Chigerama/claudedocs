# Images

OWNER uploads image files themselves; the sync only names them, links them and reports what's missing. That keeps image bytes out of the conversation.

1. **Find pictures.** For each tab being synced, read the tab and list its pictures in order. Each one shows in the read as `<media blob='blob/<id>' alt='<caption>'/>`; note the blob id, the caption and the nearest heading above.
2. **Name new ones.** Pictures already in the private doc.yml's `images:` list keep their file name for good, and public uses the same name. A new picture gets `<NN>-<tab-slug>-<what-it-shows>.<ext>`: NN is the tab's number; what-it-shows is two to five lowercase hyphenated words from the caption or the nearest heading; ext is png for screenshots and jpg for photos. Add a numeric suffix if the name is already taken. Add an entry to the private `images:` list with file, tab, blob, where (heading plus picture number) and caption.
3. **Link.** The Markdown export writes each picture as a placeholder line, `&#91;image: <caption>\]` (or `&#91;image\]` with no caption), and drops the image. Replace those lines, in order, with `![<caption>](images/<file>)`. In public, only pictures in the public `images:` list get a link; the rest stay as placeholders.
4. **Removed pictures.** If an `images:` entry's picture is no longer in the doc (or, in public, its tab was removed), delete its file if present and the entry, in the same commit, and say so in the report.
5. **Check presence.** Run list_repository_tree on docs/<slug>/images/ in the target project. Never upload or re-encode images yourself.
6. **Report missing files** after the summary lines:

| Upload as | To | Which picture |
| --- | --- | --- |
| `docs/<slug>/images/<file>` | GROUP/<target> | <Doc> › <Tab> › "<heading>", <n>th picture ("<caption>") |

Then add one line: "Save the original (or right-click the picture in the doc and save it), redact anything private, rename it exactly as shown, and upload it in GitLab signed in as yourself (+ → Upload file, or several at once in the Web IDE). No re-sync needed."

If the export ever writes pictures differently from the placeholder above, say so in the report so the guide and this skill can be updated.
