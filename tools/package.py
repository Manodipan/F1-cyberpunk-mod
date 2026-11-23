#!/usr/bin/env python3
"""
package.py — keep the installable folder shaped like a normal Cyberpunk 2077 mod.

A CP2077 "legacy" (Vortex/ArchiveXL/TweakXL/redscript) mod is just a mirror of the
game root: every top-level folder in the mod is a folder that already exists in the
game, and the manager copies the tree in. Anything that is not part of that mirror —
a README, a note, a `.pyc`, a stray `.zip` — ends up littering the game folder.

This validates the payload and builds the zip you upload to Nexus.

    python3 tools/package.py --check            # validate Phoenix_aston_cheats/
    python3 tools/package.py --zip              # -> dist/Phoenix_aston_cheats.zip
    python3 tools/package.py --mod path --zip out.zip

Rules enforced (errors)
-----------------------
  * top level contains only game-root folders: archive/, r6/, red4ext/, bin/
  * no documentation / tooling inside the payload (.md .txt .py .pyc .zip,
    __pycache__, .DS_Store, Thumbs.db, .git*)
  * archive/pc/mod: .archive files, at most one loader config each (.archive.xl);
    an asset-only archive may ship without one, a .xl must always have its archive
  * r6/tweaks/<author>/<file>.yaml        (one author folder, as the stock mod does)
  * r6/scripts/<mod folder>/*.reds        (one folder per mod)
  * no empty directories
  * file and folder names are lowercase ASCII [a-z0-9_.-]

Warnings (not errors)
---------------------
  * red4ext/ present: this mod shares the stock AudioXL bank on purpose, so a copy
    of the bank here would be loaded twice
  * a file name does not start with the mod namespace (`phoenix`)
  * archive name and folder namespace disagree
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

GAME_ROOT_DIRS = {"archive", "r6", "red4ext", "bin"}
DOC_SUFFIXES = {".md", ".txt", ".rst", ".pdf", ".doc", ".docx"}
TOOLING_SUFFIXES = {".py", ".pyc", ".pyo", ".zip", ".7z", ".rar", ".ps1", ".bat", ".sh"}
JUNK_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db", "desktop.ini", ".git", ".gitignore"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
NAMESPACE = "phoenix"

# payload path patterns
P_ARCHIVE = re.compile(r"^archive/pc/mod/[^/]+\.archive$")
P_ARCHIVE_XL = re.compile(r"^archive/pc/mod/[^/]+\.archive\.xl$")
P_TWEAK = re.compile(r"^r6/tweaks/[^/]+/[^/]+\.ya?ml$")
P_SCRIPT = re.compile(r"^r6/scripts/[^/]+/[^/]+\.reds$")


def _rel_files(mod: Path) -> list[Path]:
    return sorted(p.relative_to(mod) for p in mod.rglob("*") if p.is_file())


def validate(mod: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not mod.is_dir():
        return [f"{mod}: not a directory"], []

    top = sorted(p.name for p in mod.iterdir() if p.is_dir())
    top_files = sorted(p.name for p in mod.iterdir() if p.is_file())

    for name in top:
        if name not in GAME_ROOT_DIRS:
            errors.append(f"top-level folder {name!r} is not a game-root folder "
                          f"(allowed: {', '.join(sorted(GAME_ROOT_DIRS))})")
    for name in top_files:
        errors.append(f"file {name!r} at the payload root would be copied into the game root; "
                      "documentation belongs in docs/")
    if "red4ext" in top:
        warnings.append("red4ext/ is present: the Phoenix scripts load the stock AudioFX bank, "
                        "so a second copy of xaires_amv.bnk would be loaded twice")
    if not top:
        errors.append("payload is empty")

    files = _rel_files(mod)
    if not files:
        errors.append("payload has no files")

    archive_stems = set()
    xl_stems = set()
    for rel in files:
        posix = rel.as_posix()

        for part in rel.parts:
            if part in JUNK_NAMES:
                errors.append(f"{posix}: junk/tooling entry {part!r} in the payload")
            elif not NAME_RE.match(part):
                warnings.append(f"{posix}: name {part!r} is not lowercase ASCII "
                                "(Windows is case-insensitive, Linux installs are not)")

        suffix = rel.suffix.lower()
        if suffix in DOC_SUFFIXES:
            errors.append(f"{posix}: documentation inside the payload "
                          "(move it to docs/)")
        elif suffix in TOOLING_SUFFIXES:
            errors.append(f"{posix}: tooling/archive inside the payload")

        if P_ARCHIVE.match(posix):
            archive_stems.add(posix[: -len(".archive")])
        elif P_ARCHIVE_XL.match(posix):
            xl_stems.add(posix[: -len(".archive.xl")])
        elif suffix in (".yaml", ".yml"):
            if not P_TWEAK.match(posix):
                errors.append(f"{posix}: tweak must be r6/tweaks/<author>/<file>.yaml")
        elif suffix == ".reds":
            if not P_SCRIPT.match(posix):
                errors.append(f"{posix}: script must be r6/scripts/<mod folder>/<file>.reds")
        elif suffix == ".archive":
            errors.append(f"{posix}: archives belong in archive/pc/mod/")
        elif suffix not in (".archive.xl",):
            warnings.append(f"{posix}: unexpected file type for a CP2077 mod")

        if not rel.name.startswith(NAMESPACE):
            warnings.append(f"{posix}: does not start with the mod namespace {NAMESPACE!r}")

    if not archive_stems:
        errors.append("archive/pc/mod has no .archive")
    for stem in sorted(archive_stems - xl_stems):
        # Legal: a pure asset archive (e.g. the packed onscreens archive) needs no
        # loader config. A .xl without an archive stays an error: that is a typo.
        warnings.append(f"{stem}.archive: no matching .archive.xl (asset-only archive)")
    for stem in sorted(xl_stems - archive_stems):
        errors.append(f"{stem}.archive.xl has no matching .archive")

    for d in sorted(p for p in mod.rglob("*") if p.is_dir()):
        if not any(d.iterdir()):
            errors.append(f"{d.relative_to(mod)}: empty directory")

    for stem in sorted(archive_stems):
        if not Path(stem).name.startswith(f"{NAMESPACE}_"):
            warnings.append(f"{stem}.archive: archive name does not match the mod namespace")
    return errors, warnings


def build_zip(mod: Path, out: Path) -> list[str]:
    files = _rel_files(mod)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            info = zipfile.ZipInfo(rel.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(mod / rel, "rb") as fh:
                zf.writestr(info, fh.read())
    return [rel.as_posix() for rel in files]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    ap.add_argument("--mod", type=Path, default=Path("Phoenix_aston_cheats"),
                    help="payload folder (default: Phoenix_aston_cheats)")
    ap.add_argument("--check", action="store_true", help="validate only (default action)")
    ap.add_argument("--zip", nargs="?", const=Path("dist/Phoenix_aston_cheats.zip"),
                    type=Path, help="build the Nexus zip (default: dist/Phoenix_aston_cheats.zip)")
    args = ap.parse_args(argv)

    errors, warnings = validate(args.mod)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error:   {e}")

    if errors:
        print(f"\n{args.mod}: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    entries = _rel_files(args.mod)
    print(f"{args.mod}: layout OK — {len(entries)} file(s), "
          f"{len(warnings)} warning(s)")

    if args.zip is not None or (argv is not None and "--zip" in argv):
        written = build_zip(args.mod, args.zip)
        print(f"wrote {args.zip} ({args.zip.stat().st_size:,} bytes, {len(written)} entries)")
        for name in written:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
