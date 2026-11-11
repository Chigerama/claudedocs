#!/usr/bin/env python3
"""Maintain the living-docs skills: copy shared files, validate, package, configure.

  python3 tools/skills.py sync       Copy shared/ files into the skills that use them
  python3 tools/skills.py validate   Check frontmatter, links, sizes, shared copies, manifests
  python3 tools/skills.py package    Write dist/<skill>.zip for upload to Claude (Customize → Skills)
  python3 tools/skills.py configure KEY=VALUE [KEY=VALUE ...]
                                     Set a Setup values entry (e.g. GROUP=acme-docs) in every skill

Standard library only, plus PyYAML if installed (falls back to a minimal frontmatter parser).
Exit code 1 on any validation error.
"""
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "living-docs"
SKILLS = PLUGIN / "skills"
SHARED = ROOT / "shared"
DIST = ROOT / "dist"

# shared file -> (skills that get a copy, folder inside the skill)
SHARED_FILES = {
    "public_gate.py": (["doc-sync", "doc-redact"], "scripts"),
    "public-gate.md": (["doc-sync", "doc-redact"], "references"),
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_BODY_LINES = 500
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LINK_RE = re.compile(r"\]\(((?:references|scripts)/[^)#\s]+)\)")
SETUP_ROW = re.compile(r"^\| (?P<key>[A-Z]+) \| (?P<value>[^|]*?) \| (?P<rest>.*)$", re.M)


def skills():
    return sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return None, text
    try:
        import yaml
        data = yaml.safe_load(m.group(1))
    except ImportError:
        data = {}
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip().strip('"')
    return data, text[m.end():]


def cmd_sync(_args):
    for fname, (targets, folder) in SHARED_FILES.items():
        src = SHARED / fname
        for skill in targets:
            dst = SKILLS / skill / folder / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            print(f"copied shared/{fname} -> {dst.relative_to(ROOT)}")
    return 0


def cmd_validate(_args):
    errors, seen = [], set()

    def err(msg):
        errors.append(msg)
        print(f"ERROR {msg}")

    for d in skills():
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        fm, body = frontmatter(text)
        where = d.relative_to(ROOT) / "SKILL.md"
        if fm is None:
            err(f"{where}: no YAML frontmatter")
            continue
        name, desc = str(fm.get("name", "")), str(fm.get("description", ""))
        if set(fm) - {"name", "description", "license", "allowed-tools", "metadata"}:
            print(f"warn  {where}: extra frontmatter keys {sorted(set(fm) - {'name', 'description'})}")
        if not NAME_RE.match(name) or len(name) > 64:
            err(f"{where}: name '{name}' must be kebab-case, at most 64 characters")
        if "claude" in name or "anthropic" in name:
            err(f"{where}: name must not contain 'claude' or 'anthropic'")
        if name != d.name:
            err(f"{where}: name '{name}' doesn't match its folder '{d.name}'")
        if name in seen:
            err(f"{where}: duplicate name '{name}'")
        seen.add(name)
        if not desc or len(desc) > 1024:
            err(f"{where}: description must be 1-1024 characters (is {len(desc)})")
        if "<" in desc or ">" in desc:
            err(f"{where}: description must not contain angle brackets")
        if not re.search(r"\bUse (for|when)\b", desc):
            err(f"{where}: description should say when to use the skill ('Use for …' / 'Use when …')")
        lines = body.count("\n")
        if lines > MAX_BODY_LINES:
            err(f"{where}: body is {lines} lines; move detail into references/ (limit {MAX_BODY_LINES})")
        for ref in LINK_RE.findall(body):
            if not (d / ref).is_file():
                err(f"{where}: links to missing file {ref}")
        for ref in sorted({p.relative_to(d).as_posix() for p in d.rglob("*")
                           if p.is_file() and p.parent != d}):
            if ref.startswith(("references/", "scripts/")) and ref not in text and \
                    not any(ref in (d / r).read_text(encoding="utf-8", errors="ignore")
                            for r in LINK_RE.findall(body) if (d / r).is_file()):
                print(f"warn  {d.name}: {ref} isn't mentioned in SKILL.md or its references")
        print(f"ok    {name}: {len(desc)}-char description, {lines}-line body")

    for fname, (targets, folder) in SHARED_FILES.items():
        src = (SHARED / fname).read_bytes()
        for skill in targets:
            dst = SKILLS / skill / folder / fname
            if not dst.is_file() or dst.read_bytes() != src:
                err(f"{dst.relative_to(ROOT)} differs from shared/{fname}: run 'tools/skills.py sync'")

    for manifest in (PLUGIN / ".claude-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"):
        try:
            json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            err(f"{manifest.relative_to(ROOT)}: {e}")
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    entry = next((p for p in market["plugins"] if p["name"] == plugin["name"]), None)
    if not entry:
        err("marketplace.json doesn't list the living-docs plugin")
    elif entry.get("version") != plugin.get("version"):
        err(f"version mismatch: plugin.json {plugin.get('version')} vs marketplace.json {entry.get('version')}")

    setups = {d.name: dict((m["key"], m["value"]) for m in SETUP_ROW.finditer(
        (d / "SKILL.md").read_text(encoding="utf-8"))) for d in skills()}
    for key in sorted({k for s in setups.values() for k in s} - {"Key"}):
        values = {s[key] for s in setups.values() if key in s}
        if len(values) > 1:
            err(f"Setup value {key} differs between skills: {sorted(values)}")

    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


def cmd_package(_args):
    if cmd_validate(None):
        return 1
    DIST.mkdir(exist_ok=True)
    for d in skills():
        out = DIST / f"{d.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(d.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    z.write(f, (pathlib.Path(d.name) / f.relative_to(d)).as_posix())
        print(f"wrote {out.relative_to(ROOT)}")
    return 0


def cmd_configure(args):
    pairs = dict(a.split("=", 1) for a in args if "=" in a)
    if not pairs or len(pairs) != len(args):
        sys.exit("usage: tools/skills.py configure KEY=VALUE [KEY=VALUE ...]")
    for d in skills():
        path = d / "SKILL.md"
        text = path.read_text(encoding="utf-8")

        def swap(m):
            key = m["key"]
            if key not in pairs:
                return m.group(0)
            value = pairs[key]
            # Names that read as code stay in backticks, as in the shipped tables.
            shown = f"`{value}`" if m["value"].startswith("`") else value
            return f"| {key} | {shown} | {m['rest']}"

        new = SETUP_ROW.sub(swap, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")
    unknown = set(pairs) - {m["key"] for d in skills()
                            for m in SETUP_ROW.finditer((d / "SKILL.md").read_text(encoding="utf-8"))}
    if unknown:
        print(f"warn  no skill has Setup values for: {', '.join(sorted(unknown))}")
    return 0


def main():
    cmds = {"sync": cmd_sync, "validate": cmd_validate, "package": cmd_package, "configure": cmd_configure}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    return cmds[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
