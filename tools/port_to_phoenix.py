#!/usr/bin/env python3
"""
port_to_phoenix.py — PORT.md §4: the stock -> `phoenix` rename, plus the §3 physics
port, done mechanically instead of by hand.

Why a tool: the rename touches record IDs, wheel roles, every gear record, TweakDBID
literals inside four redscript files, the audio metadata name and the file names.
A missed identifier means duplicate IDs, a TEST-name car, HUD hooks that never fire,
or scripts that silently target the stock car — and PORT.md §7 shows how expensive
those are to debug. This applies one ordered rule set and can prove the result is
clean (`--check`).

Usage
-----
  # build the installable Phoenix tree from the stock mod on main
  python3 tools/port_to_phoenix.py --from stock reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml \
      --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
  python3 tools/port_to_phoenix.py --from stock reference/stock/r6/scripts/xaires_aston_valkyrie \
      --out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

  # audit a finished tree (identifiers, stock physics, script<->YAML references)
  python3 tools/port_to_phoenix.py --check Phoenix_aston_cheats

  # port your own staging copy in place (never the game folder — Vortex overwrites)
  python3 tools/port_to_phoenix.py --from stock "C:/mods/aston_valkyrie" --in-place

Renamed (PORT.md §4)
--------------------
  Vehicle.xaires_aston_valkyrie[_data|_purchasable|_manufacturer|_icon|_logo]
                                        -> Vehicle.phoenix_aston_valkyrie[...]
  Vehicle.xaires_amv_wheel_front/back   -> Vehicle.phoenix_amv_wheel_front/back
  Vehicle.xaires_amv_gear_r, _1 .. _7   -> Vehicle.phoenix_amv_gear_r, _1 .. _7
  UIIcon.xaires_aston_valkyrie_*        -> UIIcon.phoenix_aston_valkyrie_*
  enumName: xaires_aston_valkyrie_logo  -> enumName: phoenix_aston_valkyrie_logo
  XairesAMVEngineState / XairesAMV*     -> PhoenixAMVEngineState / PhoenixAMV*
  n"xaires_amv_engine", t"Vehicle.xaires_*" literals
  gear 7 ceiling 91.7                   -> 138.89 (500 km/h), YAML + reds
  file / folder names                   -> phoenix_aston_valkyrie*

Kept shared (same assets, same bank, same Wwise events)
-------------------------------------------------------------
  appearanceName: aston_valkyrie
  xaires\\aston_valkyrie\\...  (.ent, .inkatlas, .xbm, onscreens .json)
  XairesAMV_Wwise / xaires_amv.bnk     (one AudioXL bank for both mods)
  xamw_* / xcm_vol / xaires_cm_vol      (Wwise events + Car Manager fact)
  widget paths (amvGear, amvLed, amvRev, seg_*, g_*, s_*, led_*, amvSpd*)
  VC_DeepCopyAudioMetadata             (VehicleCore API, not ours to rename)

Not renamed on purpose: `VC_DeepCopyAudioMetadata` is provided by the VehicleCore
module (`import VehicleCore.*`), so it must stay byte-identical — an earlier draft
of this tool prefixed it and would have broken the audio metadata copy.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Spans that must survive untouched (shared assets, shared bank, shared Wwise)
# ---------------------------------------------------------------------------
PROTECT = [
    r"xaires\\aston_valkyrie\\[A-Za-z0-9_.\\]*",       # assets inside the shared .archive
    r"appearanceName:[ \t]*aston_valkyrie",            # appearance lives in the shared .ent
    r"XairesAMV_Wwise[/\\][A-Za-z0-9_.\\/]*",           # AudioXL bank folder (path form only:
    r"xaires_amv\.bnk",                                # shared Wwise bank file
    r"xaires_cm_vol",                                  # Car Manager volume fact
    r"xamw_[A-Za-z0-9_]*",                             # Wwise events / parameters
    r"xcm_vol",                                        # AudioXL volume parameter
    r"atlasResourcePath:[ \t]*\S+",                    # texture-core paths
    r"atlasPartName:[ \t]*\S+",                        # atlas part names
    r'(?:dealerAtlasPath|dealerPartName):[ \t]*"[^"]*"',  # Virtual Car Dealer preview
]

# ---------------------------------------------------------------------------
# 2. Ordered rename rules (most specific first)
# ---------------------------------------------------------------------------
RENAME = [
    (r"xaires_aston_valkyrie", "phoenix_aston_valkyrie"),   # records, UIIcon, enumName
    (r"xaires_amv", "phoenix_amv"),                         # wheels, gears, audio resource
    (r"XairesAMV", "PhoenixAMV"),                           # classes, services, functions
]

# ---------------------------------------------------------------------------
# 3. Physics: stock -> Phoenix F1 (PORT.md §3), keyed by (field, stock value).
#    Value-keyed so the front and rear wheel presets are unambiguous without
#    block context, and so an unknown field name cannot move the wrong number.
# ---------------------------------------------------------------------------
STOCK_TO_F1 = {
    ("horsepower", "680"): "2000",                 # scanner hp        (VehicleUIData)
    ("engineMaxTorque", "1300"): "3824",           # torque
    ("airResistanceFactor", "1.35"): "0.90",       # drag
    ("frictionMulLateral", "1.29"): "1.60",        # front grip, lateral
    ("frictionMulLongitudinal", "1.15"): "1.50",   # front grip, longitudinal
    ("frictionMulLateral", "1.33"): "2.00",        # rear grip, lateral
    ("frictionMulLongitudinal", "1.20"): "1.85",   # rear grip, longitudinal
    ("maxBrakingTorque", "1410"): "1850",          # front brakes
    ("maxBrakingTorque", "1200"): "1550",          # rear brakes
    ("springStiffness", "23"): "30",               # front spring
    ("springStiffness", "22"): "28",               # rear spring
    ("springDamping", "2000"): "3000",             # damping (both axles)
    ("swaybarStiffness", "11"): "15",              # front anti-roll
    ("swaybarStiffness", "16"): "19",              # rear anti-roll
    ("minLatFrictionCoef", "0.95"): "1.45",        # RearWheelsFrictionModifier_Exotic
    ("minLongFrictionCoef", "0.95"): "1.45",
    ("maxSpeedFactorGround", "0.6"): "1.40",       # DynamicDownforceHelper_Exotic
}

# Applied in both port modes: gear 7 `maxSpeed` + XairesAMV_GearSpeed default.
GEAR7_FROM, GEAR7_TO = "91.7", "138.89"

# ---------------------------------------------------------------------------
# 4. Check mode
# ---------------------------------------------------------------------------
# After masking, any surviving `xaires`/`Xaires`/`_f1` in *code* is a bug. Comments
# are exempt so credits ("(xaires)") and the port notes survive.
FORBIDDEN_TOKEN = re.compile(r"xaires|_f1", re.IGNORECASE)

TEXT_SUFFIXES = {".yaml", ".yml", ".xl", ".reds", ".tweak", ".json", ".txt", ".md"}

LINE_RE = re.compile(
    r"^(\s*)([A-Za-z_][A-Za-z0-9_.]*)(:[ \t]*)([+-]?\d+(?:\.\d+)?)(.*)$"
)
RECORD_RE = re.compile(
    r"^([A-Z][A-Za-z0-9_]*\.[A-Za-z0-9_]+)(?:\.[A-Za-z0-9_]+)?:(?:[ \t]|$)"
)
TWEAKDB_LITERAL_RE = re.compile(r't"((?:Vehicle|UIIcon)\.[A-Za-z0-9_]+)"')
SENTINEL = "\x00P{}\x00"

COMMENT_MARKERS = {
    # YAML: a comment starts at a "#" that is at line start or preceded by space
    # (so `LocKey#xaires_...` and `t"Vehicle.x"` are never treated as comments).
    ".yaml": r"(?P<c>(?<!\S)#)",
    ".yml": r"(?P<c>(?<!\S)#)",
    ".xl": r"(?P<c>(?<!\S)#)",   # ArchiveXL loader config is YAML
    ".reds": r"(?P<c>//)",
    ".tweak": r"(?P<c>//)",
}


# ---------------------------------------------------------------------------
# masking helpers
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
    """Restore sentinels. Loops because later patterns can wrap earlier sentinels
    (e.g. `atlasResourcePath: <path>` nests the path span)."""
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


def split_comment(line: str, suffix: str) -> tuple[str, str]:
    """Split a line into (code, comment) so rewrites and checks ignore prose."""
    marker = COMMENT_MARKERS.get(suffix)
    if marker is None:
        return line, ""
    m = re.search(marker, line)
    if not m:
        return line, ""
    cut = m.start("c")
    return line[:cut], line[cut:]


def _split_eol(line: str) -> tuple[str, str]:
    body, newline = line, ""
    if body.endswith("\n"):
        body, newline = body[:-1], "\n"
    if body.endswith("\r"):
        body, newline = body[:-1], "\r" + newline
    return body, newline


# ---------------------------------------------------------------------------
# physics rewrite
# ---------------------------------------------------------------------------
def _num(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def rewrite_line_values(line: str, suffix: str,
                        pairs: dict[tuple[str, str], str]) -> str:
    """Rewrite `key: value` pairs in the code part of a line (YAML style)."""
    body, newline = _split_eol(line)
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
    """91.7 -> 138.89 in code only (YAML value position or redscript literals)."""
    body, newline = _split_eol(line)
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

    return re.sub(r"(?<![\d.])91\.7(?![\d])", GEAR7_TO, code) + comment + newline


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


# ---------------------------------------------------------------------------
# Structural fix: explicit gear list instead of inherited-gears surgery
# ---------------------------------------------------------------------------
# The stock mod declares its gearbox as
#     gears:
#       - !remove Vehicle.VehicleEngineData_4_SuperSport_inline0   (x8)
#       - !append Vehicle.xaires_amv_gear_r                        (x8)
# i.e. "delete the base engine's eight inline gears, then add mine". If a single
# !remove misses its target (inline record renamed in a game patch), the inherited
# gear set survives in front of ours and the car drives the gearbox it inherited
# from. The Phoenix reproduced exactly that: a 500 km/h record that plateaued on
# the stock car's 330 km/h (2026-11-24).
#
# The reference car that does 572 km/h (reference/vehicles/jesko_attack) does not
# touch inherited gears at all - its engine record carries one explicit list. So
# the port emits that form: no !remove, no !append, eight gear records, in order.
GEARS_BLOCK = re.compile(
    r"(?m)^(?P<indent>[ \t]*)gears:[ \t]*\r?\n"
    r"(?P<body>(?:(?P=indent)[ \t]+-[^\r\n]*(?:\r?\n|\Z))+)"
)
GEAR_ITEM = re.compile(r"^[ \t]*-[ \t]*!(?:append|remove)\b")


def explicit_gears(text: str) -> str:
    """Rewrite the remove/append gear surgery into one explicit `gears: [ ... ]`."""
    def repl(m: re.Match) -> str:
        body = m.group("body")
        items = [ln for ln in body.splitlines() if ln.strip()]
        if not all(GEAR_ITEM.match(ln) for ln in items):
            return m.group(0)                      # not the shape we expect: leave it alone
        names = [n for n in re.findall(r"!\s*append\s+(\S+)", body)]
        if not names:
            return m.group(0)
        eol = "\r\n" if "\r\n" in m.group(0) else "\n"
        return f"{m.group('indent')}gears: [ {', '.join(names)} ]{eol}"

    return GEARS_BLOCK.sub(repl, text, count=1)


def _rename_code(code: str) -> str:
    """Apply the identifier rules to a single code fragment."""
    masked, kept = _mask(code)
    for pattern, repl in RENAME:
        masked = re.sub(pattern, repl, masked)
    return _unmask(masked, kept)


def port_text(text: str, suffix: str, physics: bool,
              warn: list[str] | None = None) -> str:
    if physics:
        text = apply_physics(text, suffix, warn)
    else:
        text = "".join(rewrite_gear7(line, suffix) for line in text.splitlines(keepends=True))

    # Rename in code only: the source's Turkish engineering notes stay verbatim
    # (they are provenance — dates of in-game tests, and the credit to xaires).
    out = []
    for line in text.splitlines(keepends=True):
        body, newline = _split_eol(line)
        code, comment = split_comment(body, suffix)
        out.append(_rename_code(code) + comment + newline)
    return explicit_gears("".join(out))


FILE_RENAME = [
    (r"^aston_valkyrie", "phoenix_aston_valkyrie"),   # aston_valkyrie_audio.reds -> ...
]


def rename_path(path: Path) -> Path:
    """Rename each path component with the same identifier rules."""
    parts = list(path.parts)
    for i, part in enumerate(parts):
        for pattern, repl in RENAME:
            part = re.sub(pattern, repl, part)
        if i == len(parts) - 1:            # file name gets the explicit prefix
            for pattern, repl in FILE_RENAME:
                part = re.sub(pattern, repl, part)
        parts[i] = part
    return Path(*parts)


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def check_text(text: str, label: str, suffix: str) -> list[str]:
    problems: list[str] = []
    masked, _ = _mask(text)

    for no, line in enumerate(masked.splitlines(), 1):
        code, _comment = split_comment(line, suffix)
        for m in FORBIDDEN_TOKEN.finditer(code):
            problems.append(f"{label}:{no}: leftover {m.group(0)!r} in code")
        m = LINE_RE.match(code)
        if m:
            key, value = m.group(2).rsplit(".", 1)[-1], m.group(4)
            if (key, value) in STOCK_TO_F1:
                problems.append(f"{label}:{no}: stock physics leftover {key}: {value}")
    return problems


def collect_refs(files: list[tuple[Path, str]]) -> list[str]:
    """Cross-check script TweakDBID literals against records defined in the YAML."""
    records: set[str] = set()
    literals: dict[str, str] = {}
    audio_resources: set[str] = set()
    audio_cnames: set[str] = set()

    for path, text in files:
        suffix = path.suffix.lower()
        for line in text.splitlines():
            code, _ = split_comment(line, suffix)
            if suffix in (".yaml", ".yml"):
                m = RECORD_RE.match(code)
                if m:
                    records.add(m.group(1))
                m = re.match(r"^\s*player_audio_resource:[ \t]*(\S+)", code)
                if m:
                    audio_resources.add(m.group(1))
            for m in TWEAKDB_LITERAL_RE.finditer(code):
                literals[m.group(1)] = str(path)
            for m in re.finditer(r'n"([a-z0-9_]*amv_engine)"', code):
                audio_cnames.add(m.group(1))

    problems = []
    for ident, source in sorted(literals.items()):
        if ident.startswith("Vehicle.phoenix_") and ident not in records:
            problems.append(
                f"{source}: TweakDBID literal {ident!r} has no matching record in the YAML"
            )
    for resource in sorted(audio_resources):
        if resource.startswith("phoenix_") and resource not in audio_cnames:
            problems.append(
                f"YAML player_audio_resource {resource!r} is never created by the scripts"
                " (audio metadata copy)"
            )
    for cname in sorted(audio_cnames):
        if cname not in audio_resources:
            problems.append(
                f"scripts create audio metadata {cname!r} but no YAML record uses it"
            )
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


def _origin_source(src: Path) -> str:
    """Pre-rename location to record in the provenance stamp (repo-relative if possible)."""
    try:
        return str(src.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(src)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="PORT.md §4/§3: rename the stock Valkyrie mod to the Phoenix namespace"
                    " and port the F1 physics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("sources", nargs="+", type=Path, help="files or folders to port / check")
    ap.add_argument("--from", dest="origin", choices=["stock", "f1"], default="stock",
                    help="stock = rename + apply v2 physics (default); "
                         "f1 = physics already applied, rename only")
    ap.add_argument("--out", type=Path, help="output file or directory")
    ap.add_argument("--in-place", action="store_true", help="rewrite sources (renames file names too)")
    ap.add_argument("--check", action="store_true", help="verify a finished tree; no writing")
    ap.add_argument("--no-stamp", action="store_true",
                    help="do not prepend the 'GENERATED ...' provenance header")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    physics = args.origin == "stock"
    warn: list[str] = []

    # ---- check mode -------------------------------------------------------
    if args.check:
        problems: list[str] = []
        texts: list[tuple[Path, str]] = []
        for path, _rel in iter_sources(args.sources):
            text = path.read_text(encoding="utf-8", errors="replace")
            texts.append((path, text))
            problems += check_text(text, str(path), path.suffix.lower())
        problems += collect_refs(texts)
        for p in problems:
            print(p, file=sys.stderr)
        print(f"\n{len(texts)} file(s) scanned, {len(problems)} problem(s).", file=sys.stderr)
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
        ported = port_text(text, suffix, physics, warn)
        if not args.no_stamp:
            template = STAMP.get(suffix)
            if template:
                ported = template.format(origin=args.origin,
                                         source=_origin_source(path)) + ported

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
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
