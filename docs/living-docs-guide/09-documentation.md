This tab is the as-built record: what was actually done, where, and with what result. The Part tabs say what should happen; this tab records what did happen, including anything that went differently and how it was fixed. Clear the example below and start your own entries.

**How entries work**

- One section per piece of work, newest last, titled with the date and what was done.
- Each records the machine, the guide step, what was done, the result and the evidence (screenshots or output), with secrets removed.
- **Deviations and findings** note anything that didn't match the guide, why, and what changed in the guide as a result.
- Every entry also gets a Changelog row, and the matching Done-when box is ticked in its Part tab.

**Entry template**

```markdown
### YYYY-MM-DD · <what was done>

Machine: <machine or "browser">. Guide: <tab, step>.

Done
- HH:MM <step and what happened>

Deviations and findings
- <what differed, why, what changed>

Result: <works / partly / failed, with the evidence>

Guide changes: <tabs edited, or none>

Next: <the next step>
```

## Entries

### YYYY-MM-DD · Example: first pipeline run

Machine: browser, and Claude through the GitLab connector. Guide: Part 4, steps 1 to 5.

Done

- HH:MM Added `HOME_IP` on the group: Protected, Masked and hidden.
- HH:MM Protected tags `v*` in both projects, Maintainers create.
- HH:MM Claude committed the pipeline files to private. The pipeline failed with no jobs and a yaml invalid badge.
- HH:MM Verified the bot account, ran the pipeline again: all three jobs passed.

Deviations and findings

- The yaml invalid badge's tooltip said identity verification was required. Added verification to Part 2, step 0.

Result: works. Both pipelines green; the PDF reads correctly.

Guide changes: Part 2, step 0.

Next: Pages access and a `v0.1` release.
