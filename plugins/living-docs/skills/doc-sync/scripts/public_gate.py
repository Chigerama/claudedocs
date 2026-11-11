#!/usr/bin/env python3
"""Public gate for living docs: one set of leak rules for doc-sync and doc-redact.

Canonical copy: shared/public_gate.py. tools/skills.py sync copies it into each
skill's scripts/ folder, so every skill zip stays self-contained. Edit this file,
never the copies.

Usage:
  public_gate.py scan PATH [PATH ...] [--denylist FILE]
      Scan files or folders (*.md, *.yml, *.yaml, *.jsx, *.txt). Exit 0 if clean,
      1 on any BLOCK hit, 0 with warnings printed if only WARN hits.
  public_gate.py regex [--denylist FILE]
      Print one case-insensitive regex for a Claude Docs search read
      ({"kind": "search", "pattern": ...}) covering every BLOCK rule, plus
      every IPv4 address (the search can't tell public from private ranges).

Denylist terms are never printed: a hit shows as "denylist term #N" and the
matched text is masked.

Standard library only. Python 3.8+.
"""
import argparse
import ipaddress
import pathlib
import re
import sys

MONTHS = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|"
          r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")

# (rule id, severity, regex). BLOCK stops a public commit; WARN is reported for review.
RULES = [
    ("email", "BLOCK", r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    ("claude-link", "BLOCK", r"claude\.ai/\S+"),
    ("private-key", "BLOCK", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("token-literal", "BLOCK",
     r"\b(?:glpat-[\w-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|"
     r"sk-[A-Za-z0-9_-]{20,}|xox[abp]-[\w-]{10,}|AKIA[0-9A-Z]{16})"),
    ("secret-assignment", "BLOCK",
     r"\b(?:token|password|passwd|secret|api[_-]?key)\b\s*[:=]\s*[\"']?[^\s\"'<>`]{6,}"),
    ("time", "BLOCK", r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
    ("iso-date", "BLOCK", r"\b(?:19|20)\d{2}-\d{2}-\d{2}(?:T[\d:.]+Z?)?\b"),
    ("month-date", "BLOCK",
     rf"\b{MONTHS}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+(?:19|20)\d{{2}}\b"
     rf"|\b\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTHS}\.?,?\s+(?:19|20)\d{{2}}\b"
     rf"|\b{MONTHS}\.?\s+(?:19|20)\d{{2}}\b"),
    ("year", "WARN", r"\b(?:19|20)\d{2}\b"),
]
IPV4 = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
# Ranges that are safe in public text: RFC 1918 private, loopback, link-local,
# CGNAT and the RFC 5737 documentation ranges. Private ranges still WARN because
# a real LAN layout can identify a home network.
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
PRIVATE_NETS = [ipaddress.ip_network(n) for n in
                ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8",
                 "169.254.0.0/16", "100.64.0.0/10", "0.0.0.0/8")]
SCAN_SUFFIXES = {".md", ".yml", ".yaml", ".jsx", ".txt"}
# The one timestamp public files are meant to carry: doc.yml's last_sync in UTC.
ALLOWED_LINE = re.compile(r'^\s*last_sync:\s*"?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z"?\s*$')


def load_denylist(path):
    if not path:
        return []
    terms = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def denylist_pattern(term):
    # Whole words, any case. \b only works next to word characters.
    left = r"\b" if re.match(r"\w", term) else ""
    right = r"\b" if re.search(r"\w$", term) else ""
    return left + re.escape(term) + right


def ip_hit(text):
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return None  # not a real address, e.g. a version number like 1.2.3.400
    if any(ip in n for n in DOC_NETS):
        return None
    if any(ip in n for n in PRIVATE_NETS):
        return "WARN"
    return "BLOCK"


def mask(text):
    return text[0] + "*" * (len(text) - 2) + text[-1] if len(text) > 2 else "**"


def scan_text(text, denylist):
    hits = []  # (line, severity, rule, shown)
    for lineno, line in enumerate(text.splitlines(), 1):
        if ALLOWED_LINE.match(line):
            continue
        for n, term in enumerate(denylist, 1):
            for m in re.finditer(denylist_pattern(term), line, re.I):
                hits.append((lineno, "BLOCK", f"denylist term #{n}", mask(m.group(0))))
        for m in re.finditer(IPV4, line):
            sev = ip_hit(m.group(0))
            if sev:
                hits.append((lineno, sev, "ipv4", m.group(0) if sev == "WARN" else mask(m.group(0))))
        blocked_spans = []
        for rule, sev, pattern in RULES:
            for m in re.finditer(pattern, line, re.I):
                if sev == "WARN" and any(a <= m.start() < b for a, b in blocked_spans):
                    continue  # a year already reported inside a date
                if sev == "BLOCK":
                    blocked_spans.append(m.span())
                shown = mask(m.group(0)) if rule in ("email", "token-literal", "secret-assignment",
                                                      "private-key") else m.group(0)
                hits.append((lineno, sev, rule, shown))
    return hits


def iter_files(paths):
    for p in map(pathlib.Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SCAN_SUFFIXES)
        elif p.is_file():
            yield p
        else:
            sys.exit(f"public_gate: no such file or folder: {p}")


def cmd_scan(args):
    denylist = load_denylist(args.denylist)
    blocks = warns = 0
    for f in iter_files(args.paths):
        for lineno, sev, rule, shown in scan_text(f.read_text(encoding="utf-8", errors="replace"), denylist):
            print(f"{sev}\t{f}:{lineno}\t{rule}\t{shown}")
            blocks += sev == "BLOCK"
            warns += sev == "WARN"
    print(f"public_gate: {blocks} block, {warns} warn"
          + ("" if args.denylist else " (no denylist given: denylist terms NOT checked)"),
          file=sys.stderr)
    return 1 if blocks else 0


def cmd_regex(args):
    parts = [denylist_pattern(t) for t in load_denylist(args.denylist)]
    parts += [p for _, sev, p in RULES if sev == "BLOCK"]
    parts.append(IPV4)
    print("(?i)" + "|".join(f"(?:{p})" for p in parts))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("paths", nargs="+")
    s.add_argument("--denylist")
    r = sub.add_parser("regex")
    r.add_argument("--denylist")
    args = ap.parse_args()
    return {"scan": cmd_scan, "regex": cmd_regex}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
