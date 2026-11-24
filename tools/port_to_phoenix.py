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
import pathlib
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
    # 2026-11-24 Jesko map: 1500 is 1.5x the torque the Jesko reaches 500+ km/h with, on the
    # same curve and the same (scaled) ladder. 3824 was 3.8x and never helped top speed.
    ("engineMaxTorque", "1300"): "1500",           # torque
    ("maxRPM", "10100"): "7900",                   # the Jesko map: redline 7900, top gear 7800
    ("minRPM", "1000"): "900",
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
# ---------------------------------------------------------------------------
# THE JESKO MAP (2026-11-24)
# ---------------------------------------------------------------------------
# The Jesko reaches 500+ km/h in this install on a gear table whose top gear says 283. Its file
# is a blessing: it writes *every* record explicitly, so it is a complete specification of a car
# that works, and we can copy it instead of deriving from a car that does not.
#
# What the copy revealed, and it is the best evidence we have about how the game shifts: every
# one of its six gear floors is EXACTLY 0.90 x the previous gear's top speed, to 0.01 m/s.
#
#     gear 2 floor 21.60 = 0.90 x 24.00      gear 5 floor 46.12 = 0.90 x 51.25
#     gear 3 floor 29.78 = 0.90 x 33.08      gear 6 floor 54.30 = 0.90 x 60.33
#     gear 4 floor 37.95 = 0.90 x 42.17      gear 7 floor 62.47 = 0.90 x 69.42
#
# So the upshift fraction is 0.90, confirmed by construction rather than inferred from one stall.
# We use 0.89 - one percent of margin, so a shift that lands a hair early still lands inside.
#
# Its steps NARROW toward the top (1.378, 1.275, 1.215, 1.177, 1.151, 1.131) where ours were a
# flat 1.20, and its torque multipliers are a true ratio ladder (1.0 -> 0.265). Everything below
# is the Jesko's ladder scaled so the top gear lands on 138.89 m/s = 500 km/h:
# ---------------------------------------------------------------------------
# THE CONTROL BUILD (2026-11-24): the Jesko's physics, copied verbatim.
# ---------------------------------------------------------------------------
# No scaling, no adaptation, no "improvement". The reference mod reaches 500+ km/h on this
# exact gear table, engine and chassis, so if the Phoenix behaves differently it is the car and
# not our numbers. Only the mesh, entity, textures, name, icons and audio stay ours.
PHOENIX_GEARBOX = {
    #  gear: (minSpeed, maxSpeed, torqueMultiplier, minEngineRPM, maxEngineRPM)
    "1": (0.0,   24.0,  1.000,  900, 7600),
    "2": (21.6,  33.08, 0.670, 4960, 7600),
    "3": (29.78, 42.17, 0.494, 5370, 7600),
    "4": (37.95, 51.25, 0.387, 5630, 7600),
    "5": (46.12, 60.33, 0.316, 5810, 7600),
    "6": (54.30, 69.42, 0.265, 5940, 7600),
    "7": (62.47, 78.50, 0.227, 6050, 7800),
}

# The Jesko's own curve; copied with everything else.
TORQUE_CURVE = "base\\gameplay\\vehicles\\curves\\engine_torque\\large_balanced_turbo.curveset"

# Drive-model fields the Jesko writes out and we were inheriting from the 911 Turbo - the
# `$base` chain hides ~40 numbers, and several of them (turningRollFactor 0 vs 1,
# antiSwaybarDampingScalor, slipAngle/slipRatio curve scales, tireRollingResistanceCoef on the
# wheels) plausibly govern both the wobble and the top end. Mass stays ours; inertia scaled by
# 1750/1800 for the same handling balance at our weight.
JESKO_DRIVE = {
    "airResistanceFactor": "0.66",
    "antiSwaybarDampingScalor": "0.75",
    "bankBodyFBTanMultiplier": "0.1",
    "bankBodyLRTanMultiplier": "0.1",
    "bodyFriction": "0.6",
    "brakingEstimationMagicFactor": "0.5",
    "brakingFrictionFactor": "1.4",
    "center_of_mass_offset": "{ x: 0.0, y: -0.16, z: 0.06 }",
    "differentialOvershootFactor": "0",
    "forwardWeightTransferFactor": "0.3",
    "handbrakeBrakingTorque": "1600",
    "lowVelStoppingDeceleration": "0.8",
    "maxWheelTurnDeg": "38",
    "momentOfInertia": "{ x: 2528, y: 758, z: 2917 }",
    "perfectSteeringFactor": "1",
    "sideWeightTransferFactor": "0.2",
    "slipAngleCurveScale": "2",
    "slipAngleMinSpeedThreshold": "3",
    "slipRatioCurveScale": "2",
    "slipRatioMinSpeedThreshold": "5",
    "slopeTractionReductionBegin": "12",
    "slopeTractionReductionFactor": "1.5",
    "slopeTractionReductionMax": "30",
    "smoothWheelContactDecreaseTime": "0",
    "smoothWheelContactIncreseTime": "0",
    "turningRollFactor": "1",
    "turningRollFactorWeakContactMul": "1",
    "turningRollFactorWeakContactThresholdMax": "0.6",
    "turningRollFactorWeakContactThresholdMin": "0.9",
    "turnUpdateBaseSpeedThreshold": "5",
    "turnUpdateInputDiffForFastChange": "1",
    "turnUpdateInputDiffForSlowChange": "0",
    "turnUpdateInputDiffProgressionPow": "0.7",
    "turnUpdateInputFastChangeSpeed": "1.7",
    "turnUpdateInputSlowChangeSpeed": "0.15",
    "turnUpdateMaxSpeedThreshold": "45",
    "turnUpdateMaxSpeedTurnChangeMul": "2.15",
    "turnUpdateMaxSpeedTurnMul": "0.21",
    "turnUpdateMidSpeedThreshold": "22",
    "turnUpdateMidSpeedTurnChangeMul": "1.58",
    "turnUpdateMidSpeedTurnMul": "0.62",
    "useAlternativeTurnUpdate": "true",
    "wheelTurnMaxAddPerSecond": "137",
    "wheelTurnMaxSubPerSecond": "170",
    "wheelsFrictionMap": "CarDrivingFrictionMap.Default",
}

# Wheel presets: the Jesko's full field set, with grip 12 % above its numbers - that is the one
# place we deliberately aim higher than the reference car.
JESKO_FRONT = {
    "extremeCompressionEventScalor": "0.46",
    "frictionMulLateral": "1.46",       # Jesko 1.30
    "frictionMulLongitudinal": "1.06",  # Jesko 0.95
    "logicalSuspensionCompressionLength": "0.5",
    "mass": "23",
    "maxBrakingTorque": "1165",
    "springBoundDampingLowRate": "2200",
    "springDamping": "3000",
    "springDampingHighRateCompression": "0.3",
    "springDampingLowRateCompression": "0.2",
    "springReboundDamping": "3300",
    "springReboundDampingLowRate": "2300",
    "springStiffness": "27",
    "swaybarDisplacementLimit": "0.14",
    "swaybarLengthScalar": "2.3",
    "swaybarStiffness": "18",
    "tenderSpringLength": "0",
    "tireFrictionCoef": "1",
    "tireLateralSlipEffectsMul": "1.46",
    "tireLongitudinalSlipEffectsMul": "1.3",
    "tireRollingResistanceCoef": "0.002",
    "visualSuspensionCompressionLength": "0.03",
    "visualSuspensionDroop": "0.12",
    "wheelsVerticalOffset": "-0.017",
}
JESKO_BACK = {
    "extremeCompressionEventScalor": "0.38",
    "frictionMulLateral": "1.44",       # Jesko 1.28
    "frictionMulLongitudinal": "1.10",  # Jesko 0.98
    "logicalSuspensionCompressionLength": "0.5",
    "mass": "25",
    "maxBrakingTorque": "785",
    "springBoundDampingLowRate": "2500",
    "springDamping": "3200",
    "springDampingHighRateCompression": "0.3",
    "springDampingLowRateCompression": "0.2",
    "springReboundDamping": "3500",
    "springReboundDampingLowRate": "2500",
    "springStiffness": "26",
    "swaybarDisplacementLimit": "0.13",
    "swaybarLengthScalar": "1.3",
    "swaybarStiffness": "15",
    "tenderSpringLength": "0",
    "tireFrictionCoef": "1",
    "tireLateralSlipEffectsMul": "1.3",
    "tireLongitudinalSlipEffectsMul": "1.1",
    "tireRollingResistanceCoef": "0.002",
    "visualSuspensionCompressionLength": "0.03",
    "visualSuspensionDroop": "0.12",
    "wheelsVerticalOffset": "-0.004",
}


# ---------------------------------------------------------------------------
# Verbatim copy of the Jesko's physics records
# ---------------------------------------------------------------------------
# Raw text blocks, lifted from the reference mod and renamed into our namespace, so "copy it
# exactly" is literally true rather than true-by-my-typing. The only edits are record IDs.
JESKO_REF = pathlib.Path(__file__).resolve().parents[1] / "reference" / "vehicles" / "jesko_attack.yaml"

JESKO_RECORD_MAP = [
    ("Vehicle.jesko_attack_wheel_role_lf", "Vehicle.phoenix_amv_role_lf"),
    ("Vehicle.jesko_attack_wheel_role_rf", "Vehicle.phoenix_amv_role_rf"),
    ("Vehicle.jesko_attack_wheel_role_lb", "Vehicle.phoenix_amv_role_lb"),
    ("Vehicle.jesko_attack_wheel_role_rb", "Vehicle.phoenix_amv_role_rb"),
    ("Vehicle.jesko_attack_gear_r", "Vehicle.phoenix_amv_gear_r"),
    ("Vehicle.jesko_attack_gear_1", "Vehicle.phoenix_amv_gear_1"),
    ("Vehicle.jesko_attack_gear_2", "Vehicle.phoenix_amv_gear_2"),
    ("Vehicle.jesko_attack_gear_3", "Vehicle.phoenix_amv_gear_3"),
    ("Vehicle.jesko_attack_gear_4", "Vehicle.phoenix_amv_gear_4"),
    ("Vehicle.jesko_attack_gear_5", "Vehicle.phoenix_amv_gear_5"),
    ("Vehicle.jesko_attack_gear_6", "Vehicle.phoenix_amv_gear_6"),
    ("Vehicle.jesko_attack_gear_7", "Vehicle.phoenix_amv_gear_7"),
    ("Vehicle.jesko_attack_wheel_dims_front", "Vehicle.phoenix_amv_wheel_dims_front"),
    ("Vehicle.jesko_attack_wheel_dims_back", "Vehicle.phoenix_amv_wheel_dims_back"),
    ("Vehicle.jesko_attack_wheel_dims", "Vehicle.phoenix_amv_wheel_dimensions"),
    ("Vehicle.jesko_attack_wheel_front", "Vehicle.phoenix_amv_wheel_preset_front"),
    ("Vehicle.jesko_attack_wheel_back", "Vehicle.phoenix_amv_wheel_preset_back"),
    ("Vehicle.jesko_attack_wheel_setup", "Vehicle.phoenix_amv_wheel_setup"),
    ("Vehicle.jesko_attack_helper_rotation", "Vehicle.phoenix_amv_helper_rotation"),
    ("Vehicle.jesko_attack_helper_rear_friction", "Vehicle.phoenix_amv_helper_rear_friction"),
    ("Vehicle.jesko_attack_helper_accel_noise", "Vehicle.phoenix_amv_helper_accel_noise"),
    ("Vehicle.jesko_attack_helper_handbrake", "Vehicle.phoenix_amv_helper_handbrake"),
    ("Vehicle.jesko_attack_helper_uphill", "Vehicle.phoenix_amv_helper_uphill"),
    ("Vehicle.jesko_attack_helper_downforce", "Vehicle.phoenix_amv_helper_downforce"),
    ("Vehicle.jesko_attack_helper_air_gravity", "Vehicle.phoenix_amv_helper_air_gravity"),
    ("Vehicle.jesko_attack_burnout", "Vehicle.phoenix_amv_burnout"),
    ("Vehicle.jesko_attack_drive_model", "Vehicle.phoenix_amv_drive_model"),
    ("Vehicle.jesko_attack_engine", "Vehicle.phoenix_amv_engine"),
    ("Vehicle.jesko_attack_model", "Vehicle.phoenix_aston_valkyrie_model"),
    ("Vehicle.jesko_attack_power_level", "Vehicle.phoenix_aston_valkyrie_power_level"),
]


def jesko_records() -> dict:
    """Every top-level record of the reference mod, as raw text blocks."""
    raw = JESKO_REF.read_text(encoding="utf-8").replace("\r\n", "\n")
    recs, cur, buf = {}, None, []
    for line in raw.splitlines(keepends=True):
        if line and not line[0].isspace() and not line.startswith("#") and line.rstrip().endswith(":"):
            if cur:
                recs[cur] = "".join(buf)
            cur, buf = line.rstrip()[:-1].strip(), [line]
        elif cur:
            buf.append(line)
    if cur:
        recs[cur] = "".join(buf)
    return recs


def jesko_control_block() -> str:
    """The Jesko's physics records, renamed into our namespace, in dependency order."""
    recs = jesko_records()
    out = ["# ---- PHYSICS COPIED VERBATIM FROM reference/vehicles/jesko_attack.yaml ----\n",
           "# Record IDs renamed only. Values are byte-identical to the car that reaches 500+ km/h\n",
           "# here; nothing in this section is ours (docs/TOPSPEED-TEST.md 3m).\n\n"]
    for src, dst in JESKO_RECORD_MAP:
        block = recs[src]
        for a, b in JESKO_RECORD_MAP:          # rename every reference, not just the header
            block = block.replace(a, b)
        out.append(block.strip("\n") + "\n\n")
    return "".join(out)


# Fields of the reference's vehicle record that are ours and must not be copied: identity,
# mesh, camera rigs and anything that names a record belonging to the other mod.
JESKO_VEHICLE_KEEP_OURS = {
    "appearanceName", "entityTemplatePath", "displayName", "icon", "manufacturer",
    "$type", "player_audio_resource", "traffic_audio_resource", "vehicleUIData", "vehDataPackage",
    "destruction", "model", "statModifiers", "tppCameraPresets", "queryOnlyExceptions",
    "vehDriver_FPPCameraParams", "vehDriverCombat_FPPCameraParams", "destroyedAppearance",
    "persistentName", "weaponSafeModeBounds", "audioResourceName",
}

OUR_VEHICLE_BLOCK = """  appearanceName: aston_valkyrie
  entityTemplatePath: xaires\\aston_valkyrie\\aston_valkyrie.ent
  destruction:
    $base: Vehicle.v_sport2_porsche_911turbo_inline8
  displayName: phoenix_aston_valkyrie_name
  manufacturer: Vehicle.phoenix_aston_valkyrie_manufacturer
  model: Vehicle.phoenix_aston_valkyrie_model
  player_audio_resource: phoenix_amv_engine
  statModifiers: [ Vehicle.phoenix_aston_valkyrie_power_level ]
  vehDataPackage:
    $base: Vehicle.VehicleDataPackageSport2
    useAuxiliary: true
    hasSpoiler: false
    driverCombat: DriverCombatTypes.Doors
    vehSeatSet: Vehicle.Vehicle2SeatSetDefault
    additionalAnimFeatures:
      - porscheCorrectivePose
  vehicleUIData: Vehicle.phoenix_aston_valkyrie_data
"""


def jesko_vehicle_record() -> str:
    """The reference's vehicle record, minus its identity, as an explicit $type record.

    This is the last `$base` in the file: ours inherited `Vehicle.v_sport2_porsche_911turbo`,
    and a vehicle record carries curvesPath, driving params, impact and crowd settings that no
    drive-model field can override. The Jesko writes all 110 of them out, so ours does too.
    """
    block = jesko_records()["Vehicle.v_sport1_koenigsegg_jesko_attack_player"]
    lines = []
    for line in block.splitlines(keepends=True)[1:]:   # drop the header line
        if line.strip() and not line[0].isspace():     # the record ends at the next top-level key
            break
        lines.append(line)
    for a, b in JESKO_RECORD_MAP:
        lines = [l.replace(a, b) for l in lines]
    kept = []
    for line in lines:
        key = line[2:].split(":", 1)[0] if line.startswith("  ") and ":" in line else None
        if key in JESKO_VEHICLE_KEEP_OURS:
            continue
        kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    return ("Vehicle.phoenix_aston_valkyrie:\n"
            "  $type: gamedataVehicle_Record\n"
            + "".join(kept)
            + "\n" + OUR_VEHICLE_BLOCK)


def apply_explicit_vehicle_record(text: str) -> str:
    begin = "Vehicle.phoenix_aston_valkyrie:\n"
    if begin not in text:
        return text
    start = text.index(begin)
    rest = text[start + len(begin):]
    for marker in ("\nUIIcon.phoenix_aston_valkyrie_icon:", "\n# Arac cagirma"):
        if marker in rest:
            end = rest.index(marker)
            break
    else:
        return text
    return text[:start] + jesko_vehicle_record() + rest[end:]

def apply_jesko_control(text: str) -> str:
    """Replace our wheel roles, gears, wheels, drive model and engine with the Jesko's."""
    begin = "Vehicle.phoenix_amv_wheel_front:"
    end = "Vehicle.phoenix_aston_valkyrie:"
    if begin not in text or end not in text:
        return text
    head = text[: text.index(begin)]
    tail = text[text.index(end):]
    return head + jesko_control_block() + tail

def _set_fields(lines, lo, hi, indent, fields):
    """Set key: value pairs inside lines[lo:hi] at the given indent, appending what is missing."""
    pad = " " * indent
    for key, value in fields.items():
        pattern = re.compile(r"^" + pad + re.escape(key) + r":")
        for i in range(lo, hi):
            if pattern.match(lines[i]):
                lines[i] = f"{pad}{key}: {value}\n"
                break
        else:
            lines.insert(hi, f"{pad}{key}: {value}\n")
            hi += 1
    return hi


def _block(lines, header, start=0):
    """Span of a top-level record: from its header line to the next line at indent 0."""
    for i in range(start, len(lines)):
        if lines[i].rstrip("\r\n") == header:
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j][0].isspace() and not lines[j].startswith("#"):
                    return i + 1, j
            return i + 1, len(lines)
    raise KeyError(header)


def apply_jesko_chassis(text: str) -> str:
    """Write the Jesko's drive-model and wheel-preset numbers out in full."""
    lines = text.splitlines(keepends=True)

    try:
        lo, hi = _block(lines, "Vehicle.phoenix_amv_drive_model:")
    except KeyError:
        return text          # not the hoisted vehicle YAML; nothing to map
    _set_fields(lines, lo, hi, 2, JESKO_DRIVE)

    lo, hi = _block(lines, "Vehicle.phoenix_amv_drive_model:")
    for sub, fields in (("frontPreset:", JESKO_FRONT), ("backPreset:", JESKO_BACK)):
        for i in range(lo, hi):
            if lines[i].strip() == sub:
                end = i + 1
                while end < hi and lines[end].strip() and (lines[end].startswith("      ")
                                    or lines[end].startswith("    #")):
                    end += 1
                _set_fields(lines, i + 1, end, 6, fields)
                break

    text = "".join(lines)
    # helper values the Jesko runs and we inherited from the 911
    text = text.replace("      driftLimit: 1.6\n", "      driftLimit: 2.3\n")
    text = text.replace("      minLatFrictionCoef: 1.45\n      minLongFrictionCoef: 1.45",
                        "      minLatFrictionCoef: 0.62\n      minLongFrictionCoef: 0.8")
    text = text.replace("      baseAddedGravity: 1.0\n      driveSpeedAddedGravity: 0.4",
                        "      baseAddedGravity: 0.4\n      driveSpeedAddedGravity: 0.2")
    return text

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
    # The Jesko's own numbers: redline 7900 with the top gear ceiling at 7800. The shift happens
    # at 0.90 of a gear's range (7020 here), so the limiter is never reached in normal running.
    "maxRPM": "7900",
    "minRPM": "900",
    "gearCurvesPath": TORQUE_CURVE,
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
# Scanner build stamp
# ---------------------------------------------------------------------------
# The scanner reads VehicleUIData.horsepower, and it is the only number the game puts in front of
# the player on demand - so it carries the BUILD NUMBER instead of a fictional horsepower. When a
# new YAML is installed and TweakXL/CET actually reloads it, the scanner number changes; when the
# old file is still cached, it does not. 900000 + BUILD, so 900015 reads as "build 15".
#
# Bump BUILD in the same commit as any change to the generated YAML. The number is deliberately
# out of range for any real car: nobody mistakes 900015 for horsepower.
BUILD_STAMP_BASE = 900000
BUILD = 20

HORSEPOWER_LINE = re.compile(r"(?m)^(?P<i>[ \t]*horsepower:[ \t]*)\d+(?P<t>[ \t]*\r?)$")


def apply_build_stamp(text: str) -> str:
    """Put the build number where the scanner reads horsepower."""
    return HORSEPOWER_LINE.sub(
        lambda m: m.group("i") + str(BUILD_STAMP_BASE + BUILD) + m.group("t"), text, count=1)


# ---------------------------------------------------------------------------
# Stability overlay (2026-11-24)
# ---------------------------------------------------------------------------
# The verbatim-Jesko car wobbles under ADE, and it is the car's fault, not the driver's: an AI
# controller is a lagging controller, and it can only be stable if the plant it steers is damped.
# A human hides an underdamped car by predicting the next correction; ADE applies the correction
# it just learned, sees the overshoot, and corrects again - which is exactly a sustained weave.
#
# So this overlay buys damping, and nothing else. It does not touch power, drag, grip, gearing,
# mass or brakes, so the top-speed work and its measurements stay valid.
#
#   spring{Bound,Rebound}DampingLowRate  the Jesko runs 2200/2300 front and 2500/2500 rear.
#       The stock Aston ran 2900/5000, i.e. noticeably more rebound control at low shaft speed -
#       the regime small steering inputs live in. Restored to the stock car's rates.
#   antiSwaybarDampingScalor 0.75 -> 1    the reference damps its anti-roll bars to 75 %; that
#       is a track-car choice, and on a car whose roll inertia is not the Jesko's it lets the
#       body keep rocking after the car has already stopped turning.
#   wheelTurnMaxAddPerSecond 137 -> 110   steering rate, 20 % slower. The AI turns in, overshoots
#       and has to turn back; asking for the wheel more slowly removes most of the excitation.
#   turningRollFactor 1 -> 0              the reference couples roll into turning (1); every
#       other car we have data for, including the stock Aston, does not (0).
STABILITY_OVERLAY_ENABLED = True

STABILITY_OVERLAY = (
    ("springBoundDampingLowRate", "2200", "2900"),      # front
    ("springBoundDampingLowRate", "2500", "2900"),      # rear
    ("springReboundDampingLowRate", "2300", "6500"),    # front, zeta 0.93
    ("springReboundDampingLowRate", "2500", "6500"),    # rear
    # Step 6 (2026-11-24): the load axis. The test road is 4.6 km of gentle crests, and a crest of
    # radius R at speed v unloads the car by v^2/R: at 72 m/s any R below 528 m puts it weightless,
    # at 78 m/s below 620 m. So the car is going light - and landing - repeatedly, and an impulse at
    # 70+ m/s is a yaw excitation. Nothing can stop the unload, but the landing does not have to
    # become an oscillation:
    #   extremeCompressionEventScalor   the fraction of suspension force KEPT in an extreme
    #       compression event - i.e. what survives a landing. Reference 0.46 front / 0.38 rear,
    #       stock Aston 0.74 / 0.67: the reference throws away 54-62 % of its spring force exactly
    #       when it needs it, the stock car only 26-33 %.
    #   springDampingHighRateCompression 0.3 -> 0.36   the Pagani's, for the high-velocity shaft
    #       speeds a landing generates (the low-rate rates from step 1 do not apply here).
    #   smoothWheelContact{Decrease,Increse}Time 0 -> 0.1   reference-only fields, both zero: grip
    #       is dropped and restored instantaneously over a crest. A tenth of a second of smoothing
    #       turns a step into a ramp, which is the difference between an impulse and a force.
    # REVERTED 2026-11-24: the three fields above (extremeCompressionEventScalor 0.74/0.67,
    # springDampingHighRateCompression 0.36, smoothWheelContact* 0.1) took the ADE wobble DOWN from
    # 72 to 67 m/s. Kept here as a record, with the reasoning in docs/STABILITY.md step 6: retaining
    # more force in an extreme compression event makes the landing harsher, and 0.1 s of contact
    # smoothing is 0.1 s of LAG in the tyre force - and lag is exactly what costs a lagging
    # controller its phase margin.
    # Step 7 (2026-11-24): downforce, which is the ONE grip lever that damps instead of amplifying.
    # Raising a friction coefficient raises the plant's gain and spends phase margin (that is why
    # the grip map was left alone). Downforce is different: it raises NORMAL LOAD, and tyre
    # cornering stiffness rises with load, so it raises the yaw damping term itself. It also keeps
    # the tyres loaded over crests, where step 6 could only soften the landing.
    #   maxSpeedFactorGround 0.7 -> 1.4   the value this car carried before the control experiment
    #       (docs called it "twice every reference car": Jesko 0.7, stock Aston 0.6, Pagani 0.35).
    #       Deliberately above every reference - this is our number, not a copied one.
    #   helper maxSpeed 80 -> 139   the helper ramps from 20 to its maxSpeed and then stops. At 80
    #       it saturated at 281 km/h, so beyond that downforce was CONSTANT while drag kept growing
    #       as v^2 - i.e. the car got relatively lighter the faster it went. Extending the ramp to
    #       the new top-speed target makes downforce track v^2 up to 500 km/h, which is what the
    #       real thing does.
    # Step 8 REVERTED (2026-11-24, measured): raising maxSpeedFactorGround 1.4 -> 3.0 moved the ADE
    # wobble from 72 to 55-58 m/s and moved the MANUAL top speed only 77 -> 78. A straight loss on
    # the stability goal, and it inverts the earlier reasoning: the ceiling is the GEARBOX (78.5 m/s),
    # so load cannot buy speed here, while load DOES raise cornering stiffness and with it the yaw
    # frequency - which is the quantity that decides where ADE starts weaving. Less load, later
    # wobble. Aero is restored to the last known-good state (0.7 with the ramp ending at 80 m/s).
    # Keep the downforce ramp fix in mind for the ladder build: once the top gear is stretched past
    # 80 m/s the ramp must be extended again or downforce flat-lines while drag keeps growing.
    # Step 9 (cont.): the slip curve scales are the last Jesko-only fields and they are the direct
    # plant-gain lever - they scale the tyre's slip response, i.e. cornering stiffness. Step 8's
    # measured trade (wobble 72 -> 57, ceiling 72 -> 78) is the frequency effect of extra load, so
    # scaling these from 2 to 1 takes the stiffness back down without giving up the load.
    # Step 11 REVERTED (2026-11-24, measured): constant 2.0 load (ramp finished at 45 m/s, so no
    # moving aero at all) still wobbled - at 65 m/s, against 72 for 0.7 @ 80. So the SWEEP was not
    # the problem; the absolute LEVEL is. Downforce is not an ADE-stability lever in this car and the
    # aero is back to the known-good 0.7 @ 80 for good; only the ladder build will touch it again,
    # and only for grip above 80 m/s where the car is currently gear-limited anyway.
    #
    # Measured, all cold-boot:
    #   aero 0.7 @ 80,  no step 9   -> ADE 72, hand 77   (step 5)
    #   aero 3.0 @ 139, no step 9   -> ADE 55-58, hand 78 (step 8)
    #   aero 2.0 @ 45,  with step 9 -> ADE 65, hand 77    (step 11)
    #   aero 0.7 @ 80,  with step 9 -> to measure        (step 12 - this build)
    ("slipAngleCurveScale", "2", "1"),
    ("slipRatioCurveScale", "2", "1"),
    ("antiSwaybarDampingScalor", "0.75", "1.15"),   # Pagani's
    ("turningRollFactor", "1", "0"),
    # Step 2 (2026-11-24, from measurement): the reference's alternative turn-update is an
    # input-derivative-sensitive steering model and it is the ONLY car in the corpus that has it.
    # Measured limits - stock Aston 80 m/s under ADE / 85 held by hand, Jesko 63 / 77, ours 63 / 77
    # (ours = the reference, so the limit was the chassis, not our work). Turning it off and taking
    # the stock car's cruising steering authority is the one change that separates the two cars.
    ("useAlternativeTurnUpdate", "true", "false"),
    ("turnUpdateMaxSpeedThreshold", "45", "26"),      # stock Aston's
    # Step 3 (2026-11-24): the remaining things ONLY the wobbling car has. Measured limits again -
    # stock Aston 80/85, Jesko 63/77, ours 63/77. The Pagani (Zonda Revo) is a weak control: it
    # tops at 48 m/s against a 50 m/s gear, so it never reaches the speeds where this matters. But
    # it does agree with the stock Aston on one thing: neither of them has any of the fields below.
    #   steering rate      137 (Jesko) vs 94 (stock Aston) / 100 (Pagani) -> the two cars that do
    #                      not wobble steer at 80-73 % of the reference's rate
    #   minLatFrictionCoef 0.62 (Jesko) vs 0.95 (stock) -> the floor of lateral grip once sliding,
    #                      i.e. how hard the car bites when it is already at the limit
    #   rearWheelsLatFrictionCoef 0.9 (Jesko only) -> the reference deliberately takes 10 % of
    #                      lateral grip off the rear wheels, which is a rotation bias, and rotation
    #                      bias at 80 m/s is a spin waiting for a reason
    ("wheelTurnMaxAddPerSecond", "137", "85"),        # step 9: 10 % slower than stock Aston's 94
    ("minLatFrictionCoef", "0.62", "0.95"),           # stock Aston's
    ("minLongFrictionCoef", "0.8", "0.95"),           # stock Aston's
    ("rearWheelsLatFrictionCoef", "0.9", "1"),        # no rear-grip reduction
    # Step 4 (2026-11-24, after measurement): 63 -> 72 m/s under ADE with steps 2+3, manual hold
    # unchanged at 77 (which is the gear ceiling, so the hand is not the limit any more). The rest
    # of the gap is yaw oscillation, so this step slows the car's willingness to rotate - all
    # three fields are on that one axis:
    #   driftLimit   the rotation limiter helper's threshold. Reference 2.3 vs stock Aston 1.6:
    #                the reference lets the car reach 44 % more angular rate before the game's own
    #                anti-spin net engages, i.e. it spins before the net catches it.
    #   handbrakeLimit           2.49 -> 1.6, same threshold, same reference-only field.
    #   momentOfInertia          the reference is lighter in all three axes (2600/780/3000) than
    #                the stock Aston (3050/900/3530). Yaw mode frequency goes as 1/sqrt(I): a
    #                lighter car answers the wheel faster, and "faster than the controller" is how
    #                a weave starts. Stock's vector, scaled to our 1800 kg from its 1750 (x1.0286).
    ("driftLimit", "2.3", "1.6"),
    ("handbrakeLimit", "2.49", "1.6"),
        # Step 9 (2026-11-24, measured): step 8 raised the ADE ceiling to 78 m/s - the gear ceiling
    # itself - but the wobble onset moved DOWN, exactly the frequency half of the prediction: more
    # load means later saturation (ceiling up) AND higher cornering stiffness, so the yaw mode moved
    # nearer the controller's bandwidth (wobble sooner). Both effects are real; this step keeps the
    # load and pushes the frequency back down, without touching anything that produces speed.
    #   momentOfInertia x1.10   2600/780/3000 -> 3450/1020/3995 (stock Aston's vector, scaled to our
    #       mass, then +10 %). Yaw frequency goes as 1/sqrt(I_z): 926 -> 1020 is 4.7 % lower.
    #   wheelTurnMaxAddPerSecond 94 -> 85   a slower command is a first-order lag on the input, and
    #       the input is what ADE taps. Same lever that produced the first real gain (137 -> 94).
    ("momentOfInertia", "{ x: 2600, y: 780, z: 3000 }", "{ x: 3450, y: 1020, z: 3995 }"),
    # Step 5 (2026-11-24). The wobble happens on STRAIGHTS, which rules out cornering and tyre
    # saturation: with near-zero steering angle it is a limit cycle between ADE's lane-keeping
    # corrections and the yaw mode. On a straight there are only two levers - yaw damping and
    # loop gain - and damping has already been spent (step 1 -> no change, steps 2-4 -> 63 to 72).
    # So this step spends loop gain, then adds margin on the damping axis as backup:
    #   turnUpdateMaxSpeedTurnMul back to the reference's 0.21 (step 2 briefly used the stock
    #       Aston's 0.33): this is the steering authority above 26 m/s, i.e. the gain
    #       ADE's error signal is multiplied by. 36 % less response per correction, for a loop
    #       whose phase margin was the problem. Below 26 m/s nothing changes, so the car keeps its
    #       low-speed agility. (Step 2 adopted 0.33 from the stock Aston; with the alternative turn
    #       update now OFF the field sits in the other steering model, where the low value is the
    #       one that damps response rather than sharpening it.)
    #   antiSwaybarDampingScalor 1 -> 1.15       the Pagani's value - the highest of the three cars,
    #       and the Pagani is the one that never wobbles
    #   springReboundDampingLowRate 5000 -> 6500 body-mode zeta 0.72 -> 0.93 on the 1.23 Hz mode
        )


STABILITY_TARGETS = {(k, new) for k, _old, new in STABILITY_OVERLAY}


def apply_stability(text: str) -> str:
    """Buy damping without touching power, drag, grip, gearing, mass or brakes."""
    if not STABILITY_OVERLAY_ENABLED:
        return text
    for key, old, new in STABILITY_OVERLAY:
        text = re.sub(
            rf"(?m)^(?P<i>[ \t]*{key}:[ \t]*){re.escape(old)}(?P<t>[ \t]*\r?)$",
            lambda m, new=new: m.group("i") + new + m.group("t"),
            text,
        )
    return text


# ---------------------------------------------------------------------------
# True speedometer
# ---------------------------------------------------------------------------
# The game's HUD never shows speed. It shows speed run through the `speed_to_multiplier`
# display curve, which inflates the reading as speed rises. Measured 2026-11-24 by timing
# 1 km over a known stretch, rolling start:
#
#     Jesko    13 s/km = 277 km/h real -> HUD read 572   (2.07x)
#     Phoenix  13 s/km = 277 km/h real -> HUD read 278   (1.00x)
#
# and an unrelated Zonda mod lands at 355 km/h on a declared 180 km/h gearbox (1.97x). Two
# independent mods, same kind of factor: it is the HUD function, not any car's data, and it
# touches nothing physical - it is text formatting.
#
# The stock mod already bypasses it, but only for its own car ("diger araclara dokunmaz").
# With TRUE_SPEEDO_ALL_VEHICLES the bypass becomes every vehicle, so any car in the game
# reports the speed it is actually doing. Only the HUD number changes: the custom Phoenix
# dash, rev LEDs and audio stay gated on PhoenixAMV_IsTarget.
TRUE_SPEEDO_ALL_VEHICLES = True

HUD_SPEED_ONLY_NOTE = (
    "// Sadece bu araçta Vehicle.SpeedValue (m/s) x 3.6 yazılır, "
    "oyunun km/mph ayarına (m_kmOn) uyar. Diğer araçlara dokunmaz."
)
HUD_SPEED_ALL_NOTE = (
    "// Her araçta gerçek hız yazılır: km/h modunda m/s x 3.6, mph modunda ham m/s (m_kmOn):\n"
    "// oyunun speed_to_multiplier eğrisi (277 km/h gerçek hızı 572 gösteriyordu) devre dışı."
)
# The rename step runs after this one, so the source still carries the stock prefix.
HUD_GUARD_OURS = (
    "  if XairesAMV_IsTarget(this.m_activeVehicle) {",
    "  if PhoenixAMV_IsTarget(this.m_activeVehicle) {",
)
HUD_GUARD_ALL = "  if PhoenixAMV_TrueSpeedo(this.m_activeVehicle) {"

TRUE_SPEEDO_FN = """
// Gerçek hız göstergesi: HUD hızı speed_to_multiplier eğrisinden geçirdiği için yüksek hızda
// şişiyor (277 km/h gerçek hız 572 okunuyordu). Bu kapı bütün araçlara açık; Phoenix'in kendi
// ekranı, led ve sesi IsTarget'ta kalmaya devam ediyor, değişen tek şey HUD'daki sayı.
public static func PhoenixAMV_TrueSpeedo(vehicle: wref<VehicleObject>) -> Bool {
  return IsDefined(vehicle);
}
"""


# The owner never uses the game's imperial setting, so there is no reason to spend it on miles.
# In mph mode the dial shows the raw m/s instead - the engine's own unit, the one every number
# in this repo is quoted in ("278 km/h" is 77.2 m/s, "78.5" is a gear's maxSpeed). km/h mode is
# untouched. The HUD's "MPH" label is cosmetic and stays as it is.
MPH_MODE_SHOWS_MPS = True

HUD_SPEED_BODY = """    let kmh: Float = AbsF(speedValue) * 3.6;
    inkTextRef.SetText(this.m_SpeedValue, IntToString(RoundMath(this.m_kmOn ? kmh : kmh / 1.609344)));"""

HUD_SPEED_BODY_MPS = """    let mps: Float = AbsF(speedValue);
    // mph modu kullanilmiyor: orada ham m/s yazilir (motorun kendi birimi), km/h modu gercek km/h
    let shown: Float = this.m_kmOn ? mps * 3.6 : mps;
    inkTextRef.SetText(this.m_SpeedValue, IntToString(RoundMath(shown)));"""


def apply_mph_as_mps(text: str) -> str:
    """In the game's imperial setting, show m/s instead of miles per hour."""
    if not MPH_MODE_SHOWS_MPS or HUD_SPEED_BODY not in text:
        return text
    return text.replace(HUD_SPEED_BODY, HUD_SPEED_BODY_MPS, 1)


def apply_true_speedometer(text: str) -> str:
    """Route every vehicle's HUD speed around the game's inflating display curve."""
    if not TRUE_SPEEDO_ALL_VEHICLES or "hudCarController" not in text:
        return text                       # not the speedometer file
    guard = next((g for g in HUD_GUARD_OURS if g in text), None)
    if guard is None:
        return text                       # already converted, or not the shape we expect
    eol = "\r\n" if "\r\n" in text else "\n"
    text = text.replace(guard, HUD_GUARD_ALL, 1)
    text = text.replace(HUD_SPEED_ONLY_NOTE, HUD_SPEED_ALL_NOTE.replace("\n", eol), 1)
    if not text.endswith(eol):
        text += eol
    return text + TRUE_SPEEDO_FN.replace("\n", eol)


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
    """Rewrite stock physics values to the v2 Phoenix table (PORT.md §3).

    With RESTORE_STOCK_PHYSICS nothing physical is rewritten at all: the YAML keeps the stock
    mod's own numbers (they are the best measured car) and so does the redscript's virtual
    gearbox, whose gear-7 ceiling must agree with the ladder or the HUD revs lie. The redscript
    still gets the true speedometer - that is a display fix, not a physics one.
    """
    if RESTORE_STOCK_PHYSICS:
        if suffix in (".yaml", ".yml"):
            return text
        if suffix == ".reds":
            return apply_mph_as_mps(apply_true_speedometer(text))
        return text
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
        if RESTORE_STOCK_PHYSICS:
            return apply_mph_as_mps(apply_true_speedometer(text))
        return apply_mph_as_mps(apply_true_speedometer(apply_virtual_gearbox(text)))
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


# ---------------------------------------------------------------------------
# Physics source
# ---------------------------------------------------------------------------
# 2026-11-24: THE REFERENCE CAR WAS A LIE, AND ITS CHASSIS WAS WORSE.
#
# The Jesko's 500+ km/h turned out to be the game's speedometer inflating 2.07x - timed, it did
# 277 km/h, the same as our copy of it. So "copy the fastest car" was copying an engine that was not
# faster, attached to a drive model that was worse: measured on the same road, the STOCK mod's own
# Aston does 80 m/s under ADE and 85 by hand, against the Jesko's 63 and 77. Eight builds of damping,
# steering-rate, inertia and grip-floor work climbed from 63 to at best 72 - still short of the
# number the stock car shipped with.
#
# So the stock mod's own physics is the base again: it is the best car we have measured, and it was
# authored for this exact entity. Everything we learned stays in the tool as overlays, ready to be
# re-applied on a chassis that starts from a better place (docs/STABILITY.md).
RESTORE_STOCK_PHYSICS = True


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
    elif not RESTORE_STOCK_PHYSICS:
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
        if not RESTORE_STOCK_PHYSICS:
            # CONTROL BUILD: the whole physics section is replaced with the Jesko's own records,
            # so the chassis tune must not run - it would edit records that no longer exist.
            text = apply_stability(apply_explicit_vehicle_record(
                apply_jesko_control(hoist_subrecords(text))))
        text = apply_build_stamp(text)
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
            if (not RESTORE_STOCK_PHYSICS and (key, value) in STOCK_TO_F1
                    and (key, value) not in STABILITY_TARGETS):
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
