#!/usr/bin/env python3
"""
port_to_phoenix.py — PORT.md §4: the `_f1` -> `phoenix` rename (and the stock ->
Phoenix physics port), done mechanically instead of by hand.

Why a tool: the rename touches every ID, class, module, service string and file
name; a missed identifier means a duplicate-ID crash, a TEST-name car or a
redscript compile error, and PORT.md §7 shows how expensive those are to debug.
This tool applies one ordered rule set and can prove the result is clean
(`--check`).

Usage
-----
  # single file -> single file
  python3 tools/port_to_phoenix.py --from f1 \
      reference/aston_valkyrie_f1.yaml \
      --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml

  # whole folder (file names are renamed too)
  python3 tools/port_to_phoenix.py --from f1 \
      reference/clone_f1 \
      --out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

  # stock physics -> Phoenix physics (donor = stock reference file)
  python3 tools/port_to_phoenix.py --from stock \
      reference/aston_valkyrie_stock.yaml --out /tmp/phoenix.yaml

  # verify a finished tree: exits 1 on any leftover xaires / _f1 identifier
  python3 tools/port_to_phoenix.py --check Phoenix_aston_cheats

Renamed (PORT.md §4)
--------------------
  Vehicle.xaires_aston_valkyrie_f1[_*]  -> Vehicle.phoenix_aston_valkyrie[_*]
  Vehicle.xaires_amv_f1_gear/wheel/...  -> Vehicle.phoenix_amv_gear/wheel/...
  UIIcon.xaires_aston_valkyrie_f1_*     -> UIIcon.phoenix_aston_valkyrie_*
  XairesAMVF1 / XairesAMV               -> PhoenixAMV
  xaires_amv_engine                     -> phoenix_amv_engine
  VC_* methods                          -> PHX_*  (see --keep-method-names)
  gear 7 ceiling 91.7                   -> 138.89 (500 km/h)
  file / folder names                   -> phoenix_aston_valkyrie*

Kept shared (same assets, same bank, stock LocKeys until §6)
-------------------------------------------------------------
  appearanceName: aston_valkyrie
  xaires\\aston_valkyrie\\...  (.ent, .inkatlas, .xbm ...)
  XairesAMV_Wwise, xaires_amv.bnk, xamw_*, xcm_vol, xaires_cm_vol
  widget names (amvGear / amvLed / amvRev / seg_* / g_* / s_* / led_*)
  LocKeys xaires_aston_valkyrie_name / _info / _layout
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Spans that must survive untouched (shared assets, shared bank, stock LocKeys)
# ---------------------------------------------------------------------------
PROTECT = [
    r"xaires\\aston_valkyrie\\[A-Za-z0-9_.\\]*",     # asset paths inside the shared .archive
    r"appearanceName:[ \t]*aston_valkyrie",          # appearance lives in the shared .ent
    r"XairesAMV[_-]?Wwise[A-Za-z0-9_.\\]*",          # AudioXL bank folder name
    r"xaires_amv\.bnk",                              # shared Wwise bank
    r"xaires_cm_vol",                                # AudioXL fact
    r"xamw_[A-Za-z0-9_]*",                           # Wwise events
    r"xcm_vol",                                      # AudioXL volume fact
    r"xaires_aston_valkyrie_(?:name|info|layout)\b", # LocKeys reused until PORT.md §6
    r"atlasResourcePath:[ \t]*\S+",                  # texture-core paths
    r"atlasPartName:[ \t]*\S+",                       # atlas part names
]

# ---------------------------------------------------------------------------
# 2. Ordered rename rules (most specific first)
# ---------------------------------------------------------------------------
RENAME = [
    (r"xaires_aston_valkyrie_f1", "phoenix_aston_valkyrie"),
    (r"xaires_amv_f1", "phoenix_amv"),
    (r"XairesAMVF1", "PhoenixAMV"),
    (r"xaires_aston_valkyrie", "phoenix_aston_valkyrie"),   # stock ids -> phoenix (--from stock)
    (r"xaires_amv", "phoenix_amv"),                         # covers xaires_amv_engine
    (r"XairesAMV", "PhoenixAMV"),
    (r"F1-interim", "Phoenix"),
]

# Phoenix-only method prefix. The stock mod and the Phoenix build are installed
# side by side (PORT.md §5), and redscript rejects two @addMethod definitions with
# the same class + name + signature. Renaming VC_* -> PHX_* keeps both compilable.
METHOD_RULE = (r"\bVC_", "PHX_")

# ---------------------------------------------------------------------------
# 3. Physics: stock -> Phoenix F1 (PORT.md §3), keyed by field name + stock value
#    Value-based so front/rear presets are unambiguous without block context.
# ---------------------------------------------------------------------------
STOCK_TO_F1 = {
    ("horsepower", "680"): "2000",
    ("engineMaxTorque", "1300"): "3824",
    ("airResistanceFactor", "1.35"): "0.90",
    ("frictionMulLateral", "1.29"): "1.60",
    ("frictionMulLongitudinal", "1.15"): "1.50",
    ("frictionMulLateral", "1.33"): "2.00",
    ("frictionMulLongitudinal", "1.20"): "1.85",
    ("maxBrakingTorque", "1410"): "1850",
    ("maxBrakingTorque", "1200"): "1550",
    ("springStiffness", "23"): "30",
    ("springStiffness", "22"): "28",
    ("springDamping", "2000"): "3000",
    ("swaybarStiffness", "11"): "15",
    ("swaybarStiffness", "16"): "19",
    ("multiplier", "0.95"): "1.45",
    ("downforceFactor", "0.60"): "1.40",
}

# Applied in both modes: gear 7 ceiling + the audio GearSpeed default.
GEAR7_FROM, GEAR7_TO = "91.7", "138.89"

# ---------------------------------------------------------------------------
# 4. Check mode: identifiers that must NOT exist in a Phoenix build
# ---------------------------------------------------------------------------
FORBIDDEN = [
    r"xaires_aston_valkyrie_f1",
    r"xaires_amv_f1",
    r"XairesAMVF1",
    r"Vehicle\.xaires_aston_valkyrie",
    r"Vehicle\.xaires_amv",
    r"UIIcon\.xaires",
    r"xaires_amv_engine",
    r"\bVC_",
]

TEXT_SUFFIXES = {".yaml", ".yml", ".reds", ".tweak", ".json", ".txt", ".md"}

LINE_RE = re.compile(
    r"^(\s*)([A-Za-z_][A-Za-z0-9_.]*)(:[ \t]*)([+-]?\d+(?:\.\d+)?)(.*)$"
)
SENTINEL = "\x00P{}\x00"


# ---------------------------------------------------------------------------
# text transforms
# ---------------------------------------------------------------------------
def _mask(text: str) -> tuple[str, list[str]]:
    """Replace every protected span with a sentinel so rename rules cannot touch it."""
    kept: list[str] = []

    def grab(m: re.Match) -> str:
        kept.append(m.group(0))
        return SENTINEL.format(len(kept) - 1)

    for pattern in PROTECT:
        text = re.sub(pattern, grab, text)
    return text, kept


def _unmask(text: str, kept: list[str]) -> str:
    """Restore sentinels. Loops because later protect patterns can wrap earlier
    sentinels (e.g. `atlasResourcePath: <path>` nests the path span)."""
    pattern = re.compile(r"\x00P(\d+)\x00")

    def put(m: re.Match) -> str:
        return kept[int(m.group(1))]

    for _ in range(32):
        if not pattern.search(text):
            break
        text = pattern.sub(put, text)
    if pattern.search(text):
        raise SystemExit("error: unresolved protected span (bug in PROTECT rules)")
    return text


def _num(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


COMMENT_MARKERS = {
    ".yaml": r"\s#",      # YAML comment needs leading whitespace (LocKey# is not a comment)
    ".yml": r"\s#",
    ".reds": r"//",
    ".tweak": r"//",
}


def split_comment(line: str, suffix: str) -> tuple[str, str]:
    """Split a line into (code, comment) so rewrites never touch prose."""
    marker = COMMENT_MARKERS.get(suffix)
    if marker is None:
        return line, ""
    m = re.search(marker, line)
    if not m:
        return line, ""
    cut = m.start() + (1 if marker == r"\s#" else 0)
    return line[:cut], line[cut:]


def rewrite_line_values(line: str, suffix: str, pairs: dict[tuple[str, str], str]) -> str:
    """Rewrite `key: value` pairs in the code part of a line (YAML style)."""
    newline = ""
    body = line
    if body.endswith("\n"):
        body, newline = body[:-1], "\n"
    if body.endswith("\r"):
        body, newline = body[:-1], "\r" + newline

    code, comment = split_comment(body, suffix)
    m = LINE_RE.match(code)
    if not m:
        return line
    indent, key, sep, value, rest = m.groups()
    target = pairs.get((key.rsplit(".", 1)[-1], value))
    if target is None:
        return line
    return f"{indent}{key}{sep}{target}{rest}{comment}{newline}"


def rewrite_gear7(line: str, suffix: str) -> str:
    """91.7 -> 138.89, in code only (YAML value position or redscript literals)."""
    newline = ""
    body = line
    if body.endswith("\n"):
        body, newline = body[:-1], "\n"
    if body.endswith("\r"):
        body, newline = body[:-1], "\r" + newline

    code, comment = split_comment(body, suffix)
    if suffix in (".yaml", ".yml"):
        m = LINE_RE.match(code)
        if not m:
            return line
        indent, key, sep, value, rest = m.groups()
        num = _num(value)
        if num is None or abs(num - float(GEAR7_FROM)) > 1e-9:
            return line
        return f"{indent}{key}{sep}{GEAR7_TO}{rest}{comment}{newline}"

    rewritten = re.sub(r"(?<![\d.])91\.7(?![\d])", GEAR7_TO, code)
    return rewritten + comment + newline


def apply_physics(text: str, suffix: str, warn: list[str] | None = None) -> str:
    """Rewrite stock physics values to the v2 Phoenix table (PORT.md §3)."""
    out = []
    for line in text.splitlines(keepends=True):
        written = rewrite_line_values(line, suffix, STOCK_TO_F1)
        written = rewrite_gear7(written, suffix)

        if warn is not None:
            code, _ = split_comment(written.rstrip("\r\n"), suffix)
            m = LINE_RE.match(code)
            if m:
                key, value = m.group(2).rsplit(".", 1)[-1], m.group(4)
                current = _num(value)
                known = {v for (k, v) in STOCK_TO_F1 if k == key}
                phoenix = {STOCK_TO_F1[(k, v)] for (k, v) in STOCK_TO_F1 if k == key}
                if current is not None and known:
                    limits = {float(x) for x in known | phoenix}
                    if not any(abs(current - n) < 1e-9 for n in limits):
                        warn.append(f"{key}: {value} is neither stock nor Phoenix v2")
        out.append(written)
    return "".join(out)


def port_text(text: str, suffix: str, physics: bool, keep_method_names: bool,
              warn: list[str] | None = None) -> str:
    if physics:
        text = apply_physics(text, suffix, warn)
    else:
        text = "".join(rewrite_gear7(line, suffix) for line in text.splitlines(keepends=True))

    masked, kept = _mask(text)
    for pattern, repl in RENAME:
        masked = re.sub(pattern, repl, masked)
    if not keep_method_names:
        masked = re.sub(METHOD_RULE[0], METHOD_RULE[1], masked)
    return _unmask(masked, kept)


def rename_path(path: Path) -> Path:
    """Rename each path component with the same identifier rules."""
    parts = []
    for part in path.parts:
        for pattern, repl in RENAME:
            part = re.sub(pattern, repl, part)
        parts.append(part)
    return Path(*parts)


STAMP = {
    ".yaml": (
        "# GENERATED by tools/port_to_phoenix.py ({origin}) from {source}\n"
        "# PORT.md §4 rename output — do not edit by hand, re-run the tool instead.\n\n"
    ),
    ".yml": (
        "# GENERATED by tools/port_to_phoenix.py ({origin}) from {source}\n"
        "# PORT.md §4 rename output — do not edit by hand, re-run the tool instead.\n\n"
    ),
    ".reds": (
        "// GENERATED by tools/port_to_phoenix.py ({origin}) from {source}\n"
        "// PORT.md §4 rename output — do not edit by hand, re-run the tool instead.\n\n"
    ),
}


def stamp(text: str, suffix: str, origin: str, source: str) -> str:
    template = STAMP.get(suffix)
    if template is None:
        return text
    return template.format(origin=origin, source=source) + text


def check_text(text: str, label: str) -> list[str]:
    problems = []
    masked, _ = _mask(text)
    for pattern in FORBIDDEN:
        for m in re.finditer(pattern, masked):
            line_no = masked[: m.start()].count("\n") + 1
            problems.append(f"{label}:{line_no}: leftover {m.group(0)!r} (rule {pattern})")
    for (key, value), _new in STOCK_TO_F1.items():
        for m in re.finditer(rf"^[ \t]*{key}:[ \t]*{re.escape(value)}(?![.\d])", masked, re.M):
            line_no = masked[: m.start()].count("\n") + 1
            problems.append(f"{label}:{line_no}: stock physics leftover {key}: {value}")
    return problems


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def iter_sources(sources: list[Path]):
    for src in sources:
        if src.is_dir():
            for path in sorted(src.rglob("*")):
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                    yield path, path.relative_to(src)
        elif src.is_file():
            yield src, Path(src.name)
        else:
            raise SystemExit(f"error: no such file or directory: {src}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="PORT.md §4: rename the interim _f1 mod to the Phoenix namespace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("sources", nargs="+", type=Path, help="files or folders to port / check")
    ap.add_argument("--from", dest="origin", choices=["f1", "stock"], default="f1",
                    help="f1 = physics already applied (rename only); stock = also port physics (default: f1)")
    ap.add_argument("--out", type=Path, help="output file or directory")
    ap.add_argument("--in-place", action="store_true", help="rewrite sources (renames file names too)")
    ap.add_argument("--check", action="store_true", help="verify a finished tree; no writing")
    ap.add_argument("--keep-method-names", action="store_true",
                    help="do not rename VC_* methods to PHX_* (unsafe when stock mod is also installed)")
    ap.add_argument("--no-stamp", action="store_true",
                    help="do not prepend the 'GENERATED ...' provenance header")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    physics = args.origin == "stock"
    warn: list[str] = []
    rc = 0

    # ---- check mode -------------------------------------------------------
    if args.check:
        problems: list[str] = []
        scanned = 0
        for path, _rel in iter_sources(args.sources):
            scanned += 1
            problems += check_text(path.read_text(encoding="utf-8", errors="replace"), str(path))
        for p in problems:
            print(p, file=sys.stderr)
        print(f"\n{scanned} file(s) scanned, {len(problems)} problem(s).", file=sys.stderr)
        return 1 if problems else 0

    # ---- port mode --------------------------------------------------------
    sources = list(iter_sources(args.sources))
    if not sources:
        raise SystemExit("error: nothing to port")

    multi = len(sources) > 1 or args.sources[0].is_dir()
    if not args.out and not args.in_place and multi:
        raise SystemExit("error: give --out DIR or --in-place when porting several files")

    for path, rel in sources:
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        ported = port_text(text, suffix, physics, args.keep_method_names, warn)
        if not args.no_stamp:
            ported = stamp(ported, suffix, args.origin, str(rename_path(path)))

        if args.in_place:
            target = rename_path(path.parent) / rename_path(Path(path.name)).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(ported, encoding="utf-8")
            if target != path:
                path.unlink()
            action = "renamed" if target != path else "rewrote"
            if not args.quiet:
                print(f"{action}: {path} -> {target}")
        elif args.out:
            if multi or args.out.is_dir() or str(args.out).endswith(("/", "\\")):
                target = args.out / rename_path(rel)
            else:
                target = args.out
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(ported, encoding="utf-8")
            if not args.quiet:
                print(f"wrote: {target}")
        else:
            sys.stdout.write(ported)

    for w in warn:
        print(f"warning: {w}", file=sys.stderr)
        rc = 0  # warnings do not fail the port; --check is the gate
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
