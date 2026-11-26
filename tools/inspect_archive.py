#!/usr/bin/env python3
"""Look inside a Cyberpunk 2077 .archive without WolvenKit.

The archive file table stores every resource path as plain text (only the
*buffers* are compressed), so the two questions that decide whether the onscreens
step worked can be answered with a byte scan:

  * does the archive contain a `.json` resource at all,
  * at which path exactly (a single wrong folder silently disables the name lookup).

Usage:
    python3 tools/inspect_archive.py phoenix_strings.archive
    python3 tools/inspect_archive.py phoenix_strings.archive --expect 'phoenix\\aston_valkyrie\\en-us.json'
    python3 tools/inspect_archive.py <any file> --grep phoenix_aston_valkyrie_name

`--grep` searches the raw bytes (UTF-8 and UTF-16LE) and works on both the packed
archive and the uncompressed CR2W under source/archive, so it can prove that the
onscreen entries really made it into the binary before anything is installed.

Exit code: 0 = the expected path is present (or no --expect given), 1 = missing,
2 = the file is not an archive.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAGIC = b"RDAR"
# paths inside an archive use backslashes and end with a resource extension
PATH_RE = re.compile(rb"[A-Za-z0-9_][A-Za-z0-9_\\/.:+-]{2,150}\.(?:json|xl|yaml|reds|ent|app|xbm|csv)")


def read_paths(data: bytes) -> list[str]:
    seen: dict[str, int] = {}
    for m in PATH_RE.finditer(data):
        name = m.group(0).decode("ascii", "replace")
        if name.startswith("RDAR"):        # header bytes glued to a path by the regex
            continue
        seen[name] = seen.get(name, 0) + 1
    return sorted(seen)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="list resource paths inside a CP2077 .archive")
    ap.add_argument("archive", type=Path)
    ap.add_argument("--expect", help="path that must be present (backslashes)")
    ap.add_argument("--json-only", action="store_true", help="only show *.json resources")
    ap.add_argument("--grep", action="append", metavar="TEXT",
                    help="count occurrences of TEXT in the file bytes (repeatable); "
                         "skips the archive check, so it also works on a bare CR2W file")
    args = ap.parse_args(argv)

    if not args.archive.is_file():
        raise SystemExit(f"error: no such file: {args.archive}")

    data = args.archive.read_bytes()

    if args.grep:
        print(f"{args.archive}: {len(data):,} bytes")
        missing = 0
        for text in args.grep:
            raw = text.encode("utf-8")
            wide = text.encode("utf-16-le")
            hits = data.count(raw) + data.count(wide)
            print(f"  {text}: {hits} hit(s)")
            if not hits:
                missing += 1
        if missing:
            print(f"\n{missing} string(s) not found: the file does not contain them",
                  file=sys.stderr)
            return 1
        return 0

    if data[:4] != MAGIC:
        print(f"error: {args.archive} does not start with {MAGIC!r} — not a .archive",
              file=sys.stderr)
        return 2
    print(f"{args.archive}: {len(data):,} bytes")
    paths = read_paths(data)
    shown = [p for p in paths if p.endswith(".json")] if args.json_only else paths
    jsons = [p for p in paths if p.endswith(".json")]

    print(f"{len(paths)} resource path(s), {len(jsons)} of them .json")
    for p in shown[:40]:
        print(f"  {p}")
    if len(shown) > 40:
        print(f"  … and {len(shown) - 40} more")

    if args.expect:
        want = args.expect.replace("/", "\\")
        # exact byte match: the path string is stored verbatim in the file table
        if want.encode() in data:
            print(f"\nOK: {want} is in the archive")
            return 0
        print(f"\nMISSING: {want} is not in the archive", file=sys.stderr)
        near = [p for p in paths if p.rsplit("\\", 1)[-1].lower() == want.rsplit("\\", 1)[-1].lower()]
        if near:
            print("  same file name, different folder:", file=sys.stderr)
            for p in near:
                print(f"    {p}", file=sys.stderr)
            print("  -> the .xl must list exactly the path above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
