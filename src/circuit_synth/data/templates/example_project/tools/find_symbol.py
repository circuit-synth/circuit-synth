#!/usr/bin/env python3
"""Find KiCad symbol or footprint library IDs by substring.

Usage:
    uv run python tools/find_symbol.py <query> [--footprints] [--limit N]

Prints matching ``LibName:SymbolName`` (or ``LibName:FootprintName``) ids, one
per line, so you can copy an exact ``symbol=`` / ``footprint=`` into a
circuit-synth Component. Stdlib-only; does not import circuit_synth.
"""

import argparse
import os
import re
import sys
from pathlib import Path

VER_RE = re.compile(r"\d+(?:\.\d+)*$")
# Top-level symbols are indented one tab; sub-units are deeper, so this
# naturally excludes them.
TOPSYM_RE = re.compile(r'^\t\(symbol "([^"]+)"', re.MULTILINE)
DESC_RE = re.compile(r'\(property "(?:Description|ki_description)" "([^"]*)"')
KEYW_RE = re.compile(r'\(property "ki_keywords" "([^"]*)"')
# A derived symbol inherits the parent's pinout; ARMZ/MSOP mismatches hide here.
EXTENDS_RE = re.compile(r'\(extends "([^"]+)"')
PINNUM_RE = re.compile(r'\(number "([^"]+)"')


def _pin_annotation(name, blocks, _seen=None):
    """``[N pins]`` / ``[N pins, extends PARENT]`` / ``[extends PARENT]`` for a
    symbol, resolving the pin count through an ``(extends ...)`` parent in the
    same library. Returns "" when nothing is derivable. ASCII only.
    """
    block = blocks.get(name, "")
    ext = EXTENDS_RE.search(block)
    parent = ext.group(1) if ext else None
    if parent:
        seen = _seen or set()
        if parent in blocks and parent not in seen:
            seen.add(parent)
            pcount = _pin_count(parent, blocks, seen)
        else:
            pcount = None
    else:
        pcount = _pin_count(name, blocks)
    parts = []
    if pcount is not None:
        parts.append(f"{pcount} pins")
    if parent:
        parts.append(f"extends {parent}")
    return f"  [{', '.join(parts)}]" if parts else ""


def _pin_count(name, blocks, _seen=None):
    """Unique pin-number count for a symbol, following ``extends`` if present."""
    block = blocks.get(name, "")
    ext = EXTENDS_RE.search(block)
    if ext:
        parent = ext.group(1)
        seen = _seen or set()
        if parent in blocks and parent not in seen:
            seen.add(parent)
            return _pin_count(parent, blocks, seen)
        return None
    nums = set(PINNUM_RE.findall(block))
    return len(nums) if nums else None


def _versioned_roots():
    """Newest-first KiCad install dirs across common locations."""
    roots = [
        Path.home() / ".local" / "share" / "kicad",
        Path.home() / "Library" / "Application Support" / "kicad",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "KiCad",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "KiCad",
    ]
    dirs = []
    for root in roots:
        if not root.is_dir():
            continue
        versioned = [
            c for c in root.iterdir() if c.is_dir() and VER_RE.fullmatch(c.name)
        ]
        versioned.sort(key=lambda c: [int(p) for p in c.name.split(".")], reverse=True)
        dirs.extend(versioned)
    return dirs


def _share_dir(kind):
    """Return the first existing symbols/ or footprints/ dir.

    Honors ``KICAD_SYMBOL_DIR`` for symbols; otherwise globs versioned installs.
    """
    if kind == "symbols":
        env = os.environ.get("KICAD_SYMBOL_DIR", "")
        for part in env.split(os.pathsep):
            if part and Path(part).is_dir():
                return Path(part)
    for ver in _versioned_roots():
        for cand in (ver / kind, ver / "share" / "kicad" / kind):
            if cand.is_dir():
                return cand
    return None


def find_symbols(query, limit):
    d = _share_dir("symbols")
    if not d:
        print("No KiCad symbol directory found. Set KICAD_SYMBOL_DIR.", file=sys.stderr)
        return 1
    q = query.lower()
    hits = []
    for sym_file in sorted(d.glob("*.kicad_sym")):
        lib = sym_file.stem
        try:
            text = sym_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        marks = list(TOPSYM_RE.finditer(text))
        # Map every top-level symbol name -> its body first, so an (extends ...)
        # parent's pin count is resolvable even when the parent didn't match.
        blocks = {}
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            blocks[m.group(1)] = text[m.end() : end]
        for name, block in blocks.items():
            desc = DESC_RE.search(block)
            keyw = KEYW_RE.search(block)
            hay = (
                f"{lib}:{name} {desc.group(1) if desc else ''} "
                f"{keyw.group(1) if keyw else ''}".lower()
            )
            if q in hay:
                hits.append(f"{lib}:{name}{_pin_annotation(name, blocks)}")
    return _report(hits, limit, d)


def find_footprints(query, limit):
    d = _share_dir("footprints")
    if not d:
        print("No KiCad footprint directory found.", file=sys.stderr)
        return 1
    q = query.lower()
    hits = []
    for pretty in sorted(d.glob("*.pretty")):
        lib = pretty.stem
        for mod in pretty.glob("*.kicad_mod"):
            fid = f"{lib}:{mod.stem}"
            if q in fid.lower():
                hits.append(fid)
    return _report(hits, limit, d)


def _report(hits, limit, searched):
    hits = sorted(set(hits))
    total = len(hits)
    for h in hits[:limit]:
        print(h)
    shown = min(total, limit)
    print(
        f"\n# {total} match(es) in {searched}"
        + (f" (showing {shown})" if total > shown else ""),
        file=sys.stderr,
    )
    return 0 if total else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find KiCad symbol/footprint lib IDs.")
    ap.add_argument("query", help="case-insensitive substring, e.g. AMS1117")
    ap.add_argument("--footprints", action="store_true", help="search footprints")
    ap.add_argument("--limit", type=int, default=50, help="max results (default 50)")
    args = ap.parse_args(argv)
    if args.footprints:
        return find_footprints(args.query, args.limit)
    return find_symbols(args.query, args.limit)


if __name__ == "__main__":
    sys.exit(main())
