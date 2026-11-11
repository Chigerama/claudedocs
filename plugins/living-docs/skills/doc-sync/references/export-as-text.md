# Getting the export as text

The Claude Docs export tool returns base64, which is about a third bigger than the text and easy to garble when it's copied into a commit. Get plain text instead (tested: every tab matched to the byte):

1. **Make a text copy of each changed tab.** Claude Docs `create`, object `blob`, container `{kind: project, id: <doc id>}`, payload `{"from": {"object": "file", "id": "<tab id>"}, "format": "markdown"}`. Do every tab in parallel. Each result gives `data.asset` (an asset id), `data.bytes` (the size to verify against) and `rev` (the tab's current revision, which goes into doc.yml).
2. **Read each one.** `read_asset` with the doc's slug and the asset id returns the Markdown as plain text. Read them in parallel.
3. **Commit the text.** Copy it into add_commit with JSON escaping only: `\\` for each backslash, `\"` for each double quote, `\n` for line breaks. Keep the export's own escapes (`\_`, `\]`, `\<`, `\~`, `&#91;`) exactly as they are, and end each file with one newline.
4. **Clean up after the commit is verified.** These copies are attached to the doc as files. Delete each one with `delete_asset`, using only the asset ids returned in step 1. Never delete by type or by listing: pictures in the doc are attachments too, and deleting one removes it from the doc.

If `read_asset` fails, fall back to the export tool and send its `bytes_b64` with `encoding: base64` in add_commit.
