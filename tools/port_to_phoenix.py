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
    ("maxRPM", "10100"): "7900",                   # the curve's real ceiling, not the wish
    ("airResistanceFactor", "1.35"): "0.60",       # drag (0.90 could not pass 300)
    ("turnUpdateMaxSpeedThreshold", "26"): "45",   # steering: authority still alive at 162 km/h
    ("turnUpdateMaxSpeedTurnMul", "0.33"): "0.21",  # ...then cut to 21% - the 572 km/h car's band
    ("frictionMulLateral", "1.29"): "1.60",        # front grip, lateral
    ("frictionMulLongitudinal", "1.15"): "1.50",   # front grip, longitudinal
    ("frictionMulLateral", "1.33"): "1.70",        # rear grip, lateral (25% over the
    ("frictionMulLongitudinal", "1.20"): "1.68",   # rear grip, longitudinal
    # 2026-11-24: ours were the strongest brakes of the five cars we have (1850/1550 against
    # 1165-1410 everywhere else) - "the car hits the brakes at 350 and stops" literally.
    ("maxBrakingTorque", "1410"): "1400",          # front brakes (was 1850)
    ("maxBrakingTorque", "1200"): "1150",          # rear brakes  (was 1550)
    ("handbrakeBrakingTorque", "2600"): "1600",    # 1.6x nothing: the Jesko runs 1600, the Quadra 1156
    ("springStiffness", "23"): "30",               # front spring
    ("springStiffness", "22"): "28",               # rear spring
    ("springDamping", "2000"): "3000",             # damping (both axles)
    ("swaybarStiffness", "11"): "15",              # front anti-roll
    ("swaybarStiffness", "16"): "19",              # rear anti-roll
    ("minLatFrictionCoef", "0.95"): "1.45",        # RearWheelsFrictionModifier_Exotic
    ("minLongFrictionCoef", "0.95"): "1.45",
    ("maxSpeedFactorGround", "0.6"): "0.70",       # DynamicDownforceHelper_Exotic (was 1.40)
    # Damping: rebound vs bound was wildly asymmetric (front low-rate rebound 5000 against
    # a 2900 bound = 1.72x, rear the same part at 2900 = 1.00x). Every reference car sits
    # near 1.25x. On a bumpy Badlands straight at 300+, an inconsistent rebound pair is
    # an oscillator, and oscillation is what "wobbly" looks like from the driver seat.
    ("springReboundDamping", "4300"): "3750",       # front, 1.25x the 3000 bound
    ("springReboundDamping", "4500"): "3900",       # rear,  1.30x
    ("springReboundDampingLowRate", "5000"): "3600",  # front low rate, 1.24x bound
    ("springReboundDampingLowRate", "2900"): "3600",  # rear low rate, same
}

# ---------------------------------------------------------------------------
# 3a. Drivetrain - "rwd" (shipped) or "awd" (one flag)
# ---------------------------------------------------------------------------
# The real AMR-LMH is rear-drive, so rwd is what we ship. Flipping this to "awd" makes the
# front role record drive as well: our fronts share one VehicleWheelRole record, so it is a
# single `isDrive` flag, not a rebuild.
#
# What it does and does not do: it does **not** raise top speed - drag, gearing and any
# native cap still govern that. What it changes is what the rear tyres are doing at full
# throttle, and that is precisely the condition Auto Drive tests in: 3824 Nm through two
# tyres at 100 % throttle keeps them at the friction limit for the whole run, which is
# where yaw instability lives. Four driven wheels halve the longitudinal demand per tyre.
#
# So: AWD is the cheapest way to ask "is the wobble power oversteer?". If it fixes it, the
# answer is yes - and the RWD-authentic version of that fix is rear grip / torque curve, not
# permanent AWD.
DRIVETRAIN = "awd"

FRONT_ROLE_RE = re.compile(r"(?m)^Vehicle\.[A-Za-z0-9_]*_wheel_front:[ \t]*$")
ISDRIVE_FALSE_RE = re.compile(r"(?P<key>isDrive:[ \t]*)false")


def apply_drivetrain(text: str) -> str:
    """Make the front wheels drive too, when DRIVETRAIN is "awd"."""
    if DRIVETRAIN != "awd":
        return text
    out: list[str] = []
    in_front = False
    for line in text.splitlines(keepends=True):
        if FRONT_ROLE_RE.match(line):
            in_front = True
        elif line[:1] and not line[0].isspace():
            in_front = False
        if in_front:
            line = ISDRIVE_FALSE_RE.sub(r"\g<key>true", line, count=1)
        out.append(line)
    return "".join(out)


# Applied in both port modes: gear 7 `maxSpeed` + XairesAMV_GearSpeed default.
GEAR7_FROM, GEAR7_TO = "91.7", "138.89"

# ---------------------------------------------------------------------------
# 3b. The gear ladder (2026-11-24, after the car stopped at ~300 km/h twice)
# ---------------------------------------------------------------------------
# A gear is not a speed cap - it is a *ratio window*. Stock's 7th spans
# 77 -> 91.7 m/s (1.19x) on the box's weakest multiplier (0.306) and the stock car
# tops out at exactly 91.7 m/s. The Phoenix's 7th spanned 77 -> 138.89 (1.80x) at
# 0.306: one overdrive asked to cover 277 -> 500 km/h on a third of the torque,
# while 6th still ended at 80.6 m/s (290 km/h). In game the car stopped where 6th
# ended - 6th was the last gear with a ratio it could pull (2026-11-24, twice).
#
# So the ladder is rebuilt the way a real 7-speed that has to reach 500 km/h is:
# equal ~1.28x steps from a sane first gear, top window 101 -> 138.89 (1.37x), and a
# torque-multiplier curve that tapers instead of falling off a cliff. The virtual
# gearbox in the redscript (PhoenixAMV_GearSpeed) is regenerated from the same table,
# so HUD revs and shift points stay honest.
# 2026-11-24, after the second in-game run: the box revved to 10 050 rpm because that is
# what a record can *say*. Two different gearboxes both stopped at ~7 850 and ~8 020 rpm -
# 308 km/h in 6th of this ladder, ~300 km/h in 7th of the previous one. Different gearing,
# same rpm. That is not gearing: it is the **torque curve**. Our engine inherits the
# SuperSport `gearCurvesPath`, and no curve in the game reaches 10 100 - past its top the
# engine makes nothing, so the car stops wherever it hits the end of the curve.
#
# Both working reference cars write their own `gearCurvesPath` and both top out around
# 7 600-7 900 rpm. So the box is now geared to finish at 7 800 rpm: 500 km/h at 130 km/h
# per 1 000 rpm is reachable *inside* the curve instead of past it.
PHOENIX_GEARBOX = {
    #  gear: (minSpeed, maxSpeed, torqueMultiplier, minEngineRPM, maxEngineRPM)
    "1": (0.0,    32.0,  0.780,  900, 7800),
    "2": (29.8,   40.9,  0.720, 5680, 7800),
    "3": (38.0,   52.2,  0.665, 5680, 7800),
    "4": (48.5,   66.6,  0.610, 5680, 7800),
    "5": (61.9,   85.0,  0.560, 5680, 7800),
    "6": (79.1,  108.6,  0.530, 5680, 7800),
    "7": (101.0, 138.89, 0.500, 5670, 7800),
}
GEAR_FIELDS = ("minSpeed", "maxSpeed", "torqueMultiplier", "minEngineRPM", "maxEngineRPM")

GEAR_RECORD_RE = re.compile(r"^Vehicle\.[A-Za-z0-9_]*_gear_(?P<g>[1-7]):[ \t]*$")
GEAR_FIELD_RE = re.compile(
    r"^(?P<indent>[ \t]+)(?P<key>" + "|".join(GEAR_FIELDS) + r")"
    r"(?P<sep>:[ \t]*)(?P<value>[^ \t\r\n#]+)(?P<rest>[^\r\n]*)(?P<eol>\r?\n|$)"
)

# The stock file's own note about the ceiling is now false, and it is *generated*
# output, so it gets corrected rather than preserved as provenance.
STALE_GEAR_NOTE = (
    "# 7 ileri sirali (hizlar m/s), V12 10000 devir sinirli; azami hiz = son vitesin "
    "maxSpeed'i (91.7 m/s = 330 km/h)"
)
FRESH_GEAR_NOTE = (
    "# 7 ileri sirali (hizlar m/s), V12 10000 devir sinirli. Vites = oran penceresi, hiz siniri "
    "degil: araliklar ~1.28x, son vites 101 -> 138.89 m/s (500 km/h)"
)


def fmt_num(value: float) -> str:
    """138.89 -> '138.89', 32.0 -> '32' (YAML reads both, but keep the file tidy)."""
    return str(int(value)) if float(value).is_integer() else repr(float(value))


# ---------------------------------------------------------------------------
# 3c. The engine record: stop inheriting the half that governs top gear
# ---------------------------------------------------------------------------
# Our engine is `$base: Vehicle.VehicleEngineData_4_SuperSport` + four overrides. The
# fields that shape how hard the car pulls in its *last* gear - flywheel inertia, the
# final-gear torque decimation, shift timing - are still whatever a 911-class base record
# says. The car that actually does 572 km/h (reference/jesko_attack.yaml) inherits none of
# them: it writes its engine out in full. These are that car's values, applied explicitly,
# so nothing invisible is left between us and the ladder (2026-11-24).
ENGINE_EXPLICIT = {
    "flyWheelMomentOfInertia": "0.12",            # lower = easier to gain/lose speed
    "finalGearTorqueDecimationScalor": "1.0",     # do not tax the top gear's torque
    "gearChangeTime": "0.1",                      # sequential box: 100 ms shifts
    "gearChangeCooldown": "0.15",
    "fastR1GearChange": "true",
    "wheelsResistanceRatio": "15",                # vanilla sample value; docs do not say more
    # Engine braking. Documented as "the decrease in torque during throttle lift-off", so a
    # large inherited value is a brake you never asked for - and with AWD it now acts through
    # four driven wheels instead of two, which is exactly the moment the car started parkinging
    # itself at 350. Reference values: Jesko 150, Quadra 202.78. Inherited value unknown, so
    # it is written out (2026-11-24).
    "resistanceTorque": "150",
}
ENGINE_BLOCK_RE = re.compile(r"(?m)^(?P<indent>[ \t]+)vehEngineData:[ \t]*\r?\n")
ENGINE_HEAD_RE = re.compile(r"(?m)^(?P<indent>[ \t]+)engineMaxTorque:[^\r\n]*\r?\n")


def ensure_engine_fields(text: str) -> str:
    """Add the ENGINE_EXPLICIT fields to the engine record when they are not set yet."""
    m = ENGINE_BLOCK_RE.search(text)
    if not m:
        return text
    body_start = m.end()
    head = ENGINE_HEAD_RE.search(text, body_start)
    if not head:
        return text
    # The keys are unique to the engine record, so a whole-file scan is the safe test
    # (and makes this function idempotent: a second pass inserts nothing).
    missing = [(k, v) for k, v in ENGINE_EXPLICIT.items()
               if not re.search(rf"(?m)^\s*{k}:", text)]
    if not missing:
        return text
    indent = head.group("indent")
    note = (f"{indent}# 2026-11-24: motor kaydinin gizli yarisi (son vites torku, debriyaj ataleti,\n"
            f"{indent}# sanziman suresi) SuperSport'tan miras kaliyordu; 572 km/h'lik referans arabanin\n"
            f"{indent}# degerleri acikca yazildi.\n")
    add = note + "".join(f"{indent}{k}: {v}\n" for k, v in missing)
    return text[:head.end()] + add + text[head.end():]


# The stock mod bases every gear on a *game-internal inline record*:
#     $base: Vehicle.v_sport1_quadra_turbo_r_inline10 ... _inline14
# (gears 4, 5, 6 and 7 all base on the SAME one). TweakXL's own docs are blunt about this:
# "NEVER use inlineX records as base in your items ... the number generated will be
# dependent on the position of the inline record inside another record and can change
# without ANY warning on every single game update." If that base fails to resolve, the
# gear record is not registered - and a gear list pointing at records that do not exist
# leaves the engine record unusable, i.e. the car silently keeps its parent's physics.
# Which is one of the two explanations left for a car that ignores every number we change.
#
# We already write all five gear fields explicitly, so the base bought us nothing: the
# records now declare their type (as the working Jesko mod does) and inherit nothing.
GEAR_TYPE = "gamedataVehicleGear_Record"
GEAR_BASE_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]+)\$base:[ \t]*Vehicle\.[A-Za-z0-9_]*_inline[0-9]+[ \t]*\r?\n")


def declare_gear_type(text: str) -> str:
    """Inside the forward/reverse gear records, swap the inlineX $base for a $type."""
    out: list[str] = []
    gear = False
    for line in text.splitlines(keepends=True):
        if GEAR_RECORD_RE.match(line) or re.match(r"(?m)^Vehicle\.[A-Za-z0-9_]*_gear_r:[ \t]*$", line):
            gear = True
        elif line[:1] and not line[0].isspace() and not line.lstrip().startswith("#"):
            gear = False
        if gear:
            m = GEAR_BASE_RE.match(line)
            if m:
                out.append(f"{m.group('indent')}$type: {GEAR_TYPE}\n")
                continue
        out.append(line)
    return "".join(out)


def apply_gearbox(text: str) -> str:
    """Rewrite every forward gear's window/multiplier from PHOENIX_GEARBOX."""
    out: list[str] = []
    gear: str | None = None
    for line in text.splitlines(keepends=True):
        m = GEAR_RECORD_RE.match(line)
        if m:
            gear = m.group("g")
        elif line[:1] and not line[0].isspace() and not line.lstrip().startswith("#"):
            gear = None                     # a new record at column 0 closes the block
        if gear:
            f = GEAR_FIELD_RE.match(line)
            if f and f.group("key") in GEAR_FIELDS:
                value = PHOENIX_GEARBOX[gear][GEAR_FIELDS.index(f.group("key"))]
                line = (f"{f.group('indent')}{f.group('key')}{f.group('sep')}"
                        f"{fmt_num(value)}{f.group('rest')}{f.group('eol')}")
        out.append(line)
    return "".join(out)


# The redscript virtual gearbox must agree with the ladder, or the HUD revs lie.
GEARSPEED_FN = re.compile(
    r"(?ms)^public static func (?P<name>\w*GearSpeed)\(g: Int32\) -> Float \{\n"
    r".*?^\}\n"
)


def apply_virtual_gearbox(text: str) -> str:
    """Regenerate PhoenixAMV_GearSpeed's switch from PHOENIX_GEARBOX' maxSpeed column."""
    def repl(m: re.Match) -> str:
        speeds = [PHOENIX_GEARBOX[str(g)][1] for g in range(1, 8)]
        cases = "".join(
            f"    case {g}:\n      return {fmt_num(s)};\n" for g, s in enumerate(speeds, 1)
        )
        body = ("  switch g {\n" + cases + "    default:\n"
                f"      return {fmt_num(speeds[-1])};\n  }}\n")
        head = ("// sanal vitesin 8100 devirdeki hizi (m/s) = tweak'teki vites maxSpeed degerleri\n"
                "// (port_to_phoenix.py PHOENIX_GEARBOX: 7 ileri, ~1.28x aralik)\n"
                f"public static func {m.group('name')}(g: Int32) -> Float {{\n")
        return head + body + "}\n"

    # NOTE: the port renames after this runs, so match the stock function name too.
    return GEARSPEED_FN.sub(repl, text, count=1)

# Steering return rate: not present in the stock file, so nothing could rewrite it and we
# inherited whatever the 911 base carries. Every car we have data for states it explicitly
# (170 / 140 / 135), and it is the rate at which the wheels come back to centre - the thing
# that decides whether a correction rings or settles (2026-11-24).
STEERING_RETURN = {"wheelTurnMaxSubPerSecond": "150"}
STEERING_ANCHOR_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]+)wheelTurnMaxAddPerSecond:[^\r\n]*\r?\n")


def ensure_steering_return(text: str) -> str:
    """Write the return-to-centre rate explicitly, right after the add rate."""
    missing = [(k, v) for k, v in STEERING_RETURN.items()
               if not re.search(rf"(?m)^\s*{k}:", text)]
    if not missing:
        return text
    m = STEERING_ANCHOR_RE.search(text)
    if not m:
        return text
    indent = m.group("indent")
    add = "".join(f"{indent}{k}: {v}\n" for k, v in missing)
    return text[:m.end()] + add + text[m.end():]


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
    text = "".join(out)
    if suffix in (".yaml", ".yml"):
        text = declare_gear_type(apply_drivetrain(apply_gearbox(text)))
        text = text.replace(STALE_GEAR_NOTE, FRESH_GEAR_NOTE, 1)
        return ensure_steering_return(ensure_engine_fields(text))
    if suffix == ".reds":
        return apply_virtual_gearbox(text)
    return text


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


# ---------------------------------------------------------------------------
# 3d. Named records instead of inline blocks
# ---------------------------------------------------------------------------
# Both working references attach physics by *reference*:
#     Quadra (vanilla retune): vehDriveModelData: Vehicle.turbor_afterburn_drive_model
#                              vehEngineData: Vehicle.turbor_afterburn_engine
#     Jesko:                   vehDriveModelData: Vehicle.jesko_attack_drive_model
#                              vehEngineData: Vehicle.jesko_attack_engine
# Ours (inherited from the stock mod) nests them inline, and the nested records base
# themselves on game-internal inlines (VehicleDriveModelData_911Turbo_inline0/1/2/7).
# Inline blocks are legal YAML, so this is not a syntax fix - it is removing the last
# place where our physics depends on the *position* of someone else's record. The values
# are identical either way; the shape is what a working mod ships.
HOISTED = (
    ("vehWheelDimensionsSetup", "Vehicle.phoenix_amv_wheel_dimensions"),
    ("vehDriveModelData", "Vehicle.phoenix_amv_drive_model"),
    ("vehEngineData", "Vehicle.phoenix_amv_engine"),
)
VEHICLE_RECORD = "Vehicle.phoenix_aston_valkyrie:"
SUB_RE = re.compile(r"^(?P<indent>[ \t]{2})(?P<key>vehWheelDimensionsSetup|vehDriveModelData|vehEngineData):[ \t]*\r?\n")


def hoist_subrecords(text: str) -> str:
    """Move the three inline physics blocks into named records, reference them instead."""
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == VEHICLE_RECORD)
    except StopIteration:
        return text

    named: list[str] = []
    out = lines[:start]
    i = start
    changed = False
    while i < len(lines):
        m = SUB_RE.match(lines[i])
        if m and lines[i].startswith("  ") and not lines[i].startswith("   "):
            key = m.group("key")
            new_id = dict(HOISTED).get(key)
            # collect the block: everything more indented than the key
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith(("    ", "\t"))):
                j += 1
            if new_id:
                body = lines[i + 1:j]
                dedented = [ln[2:] if ln.startswith("  ") else ln for ln in body]
                named.append(f"{new_id}:\n" + "".join(dedented))
                out.append(f"  {key}: {new_id}\n")
                changed = True
                i = j
                continue
        out.append(lines[i])
        i += 1
    if not changed:
        return text
    return "".join(out[:-len(lines) + start] if False else out).replace(
        VEHICLE_RECORD + "\n",
        "\n".join(n.rstrip("\n") + "\n" for n in named) + "\n" + VEHICLE_RECORD + "\n",
        1,
    )


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
    text = explicit_gears("".join(out))
    # the hoist needs the *renamed* record name, so it runs after the rename pass
    if physics and suffix in (".yaml", ".yml"):
        text = hoist_subrecords(text)
    return text


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
