#!/usr/bin/env python3
"""
Side-by-side physics comparison of every vehicle tweak we have.

Why: when a number looks wrong ("it stops at 300", "it wobbles at 400") the fastest way
to a sane value is another car that already does it. With four cars in the repo we have a
control group - three that work, one that does not - so the outliers stop being opinions.

    python tools/compare_vehicles.py                    # writes docs/VEHICLE-COMPARISON.md
    python tools/compare_vehicles.py --out -            # print instead
    python tools/compare_vehicles.py --check            # exit 1 if the committed doc is stale

Output is generated: do not hand-edit it. Interpretation belongs in
docs/VEHICLE-MODEL.md, which links to it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_vehicles import profile, read_text  # noqa: E402  (same parser as the corpus)

OUT = ROOT / "docs" / "VEHICLE-COMPARISON.md"

CARS = [
    ("Phoenix AMV LMH", "Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml",
     "ours"),
    ("xaires Valkyrie (stock)", "reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml",
     "the car we forked; reaches its own 330 km/h"),
    ("Koenigsegg Jesko Attack", "reference/vehicles/jesko_attack.yaml",
     "the 572 km/h worked example"),
    ("Pagani Zonda Revo", "reference/vehicles/zonda_revo.yaml",
     "a low-torque mod that still runs its own top speed"),
    ("Quadra Turbo-R V-Tech", "reference/Quadra_TurboR_VTech_AFTERBURN_Vanilla_Override.yaml",
     "a **vanilla** car with a hand retune: the closest thing to the game's own defaults"),
]

# label, field, axis ("front/back" when the field appears once per axle)
SCALARS = [
    ("top gear `maxSpeed` (m/s)", "top", None),
    ("gears", "gears", None),
    ("`engineMaxTorque`", "engineMaxTorque", None),
    ("`maxRPM` / `minRPM`", "maxRPM", None),
    ("`total_mass`", "total_mass", None),
    ("`airResistanceFactor`", "airResistanceFactor", None),
    ("`maxSpeedFactorGround`", "maxSpeedFactorGround", None),
    ("`wheelTurnMaxAddPerSecond`", "wheelTurnMaxAddPerSecond", None),
    ("`wheelTurnMaxSubPerSecond`", "wheelTurnMaxSubPerSecond", None),
    ("`turnUpdateMaxSpeedThreshold`", "turnUpdateMaxSpeedThreshold", None),
    ("`turnUpdateMaxSpeedTurnMul`", "turnUpdateMaxSpeedTurnMul", None),
    ("`turningRollFactor`", "turningRollFactor", None),
    ("`driftLimit`", "driftLimit", None),
    ("`maxAngularSpeedRad`", "maxAngularSpeedRad", None),
    ("`frictionMulLateral` f/b", "frictionMulLateral", "fb"),
    ("`frictionMulLongitudinal` f/b", "frictionMulLongitudinal", "fb"),
    ("`swaybarStiffness` f/b", "swaybarStiffness", "fb"),
    ("`maxBrakingTorque` f/b", "maxBrakingTorque", "fb"),
    ("`springStiffness` f/b", "springStiffness", "fb"),
    ("`springDamping` f/b", "springDamping", "fb"),
    ("`springReboundDamping` f/b", "springReboundDamping", "fb"),
    ("`springReboundDampingLowRate` f/b", "springReboundDampingLowRate", "fb"),
    ("`flyWheelMomentOfInertia`", "flyWheelMomentOfInertia", None),
    ("`finalGearTorqueDecimationScalor`", "finalGearTorqueDecimationScalor", None),
    ("`gearChangeTime` / `gearChangeCooldown`", "gearChangeTime", None),
    ("`wheelsResistanceRatio`", "wheelsResistanceRatio", None),
    ("`resistanceTorque`", "resistanceTorque", None),
]

GEAR_FIELDS = ("minSpeed", "maxSpeed", "torqueMultiplier", "minEngineRPM", "maxEngineRPM")
RE_GEARS_INLINE = re.compile(r"^\s*gears\s*:\s*\[([^\]]+)\]", re.MULTILINE)
RE_GEARS_BLOCK = re.compile(r"(?ms)^\s*gears\s*:\s*\r?\n(?P<body>(?:\s+[^\r\n]*(?:\r?\n|$))+)")
RE_APPEND = re.compile(r"^\s*-\s*!append\s+(\S+)", re.MULTILINE)
RE_BLOCK = re.compile(r"(?m)^(?=[A-Za-z][A-Za-z0-9_.]*:\s*$)")

# reverse is named every way you can think of, and it always sits first in the list
RE_REVERSE = re.compile(r"(?:_|gear)(?:r|0|reverse|rev)$", re.IGNORECASE)


def blocks(text: str) -> dict[str, str]:
    out = {}
    for block in RE_BLOCK.split(text):
        m = re.match(r"^([A-Za-z][A-Za-z0-9_.]*)\s*:", block)
        if m:
            out[m.group(1)] = block
    return out


def gear_names(text: str) -> list[str]:
    """The gears an engine actually lists, in order, in any of the three YAML shapes."""
    m = RE_GEARS_INLINE.search(text)
    if m:
        return [g.strip() for g in m.group(1).split(",") if g.strip()]
    m = RE_GEARS_BLOCK.search(text)
    if m:
        names = re.findall(r"Vehicle\.[A-Za-z0-9_]+", m.group("body"))
        if names:
            return names
    # the stock mod's surgery form: !remove the inherited gears, !append ours
    return re.findall(r"!append\s+(Vehicle\.[A-Za-z0-9_]+)", text)


def gear_ladder(text: str) -> tuple[dict | None, list[dict]]:
    """(reverse, forward ladder) for the gears the engine lists."""
    known = blocks(text)
    ladder = []
    for name in gear_names(text):
        block = known.get(name)
        if not block:
            continue
        row = {"name": name}
        for f in GEAR_FIELDS:
            g = re.search(rf"(?m)^\s*{f}\s*:\s*([0-9]+(?:\.[0-9]+)?)", block)
            row[f] = float(g.group(1)) if g else None
        ladder.append(row)
    if ladder and RE_REVERSE.search(ladder[0]["name"]):
        return ladder[0], ladder[1:]
    return None, ladder


def load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    text = read_text(path)
    row = profile(path)
    if row is None:
        return None
    # profile() keeps one value per field; pull the axle pairs separately.
    for field in ("frictionMulLateral", "frictionMulLongitudinal", "swaybarStiffness",
                  "maxBrakingTorque", "springStiffness", "springDamping",
                  "springReboundDamping", "springReboundDampingLowRate"):
        vals = re.findall(rf"(?m)^\s*{field}\s*:\s*([0-9.]+)", text)
        if len(vals) >= 2:
            row[field] = f"{vals[0]} / {vals[1]}"
    for extra in ("flyWheelMomentOfInertia", "finalGearTorqueDecimationScalor",
                  "gearChangeTime", "gearChangeCooldown", "wheelsResistanceRatio",
                  "resistanceTorque", "minRPM", "wheelTurnMaxSubPerSecond"):
        m = re.search(rf"(?m)^\s*{extra}\s*:\s*([^\s#]+)", text)
        row[extra] = m.group(1) if m else ""
    if row.get("gearChangeTime") and row.get("gearChangeCooldown"):
        row["gearChangeTime"] = f"{row['gearChangeTime']} / {row['gearChangeCooldown']}"
    row["reverse"], row["ladder"] = gear_ladder(text)
    return row


def cell(row: dict, field: str) -> str:
    if row is None:
        return "—"
    value = row.get(field, "")
    return str(value) if value not in ("", None) else "**inherited**"


def render(cars: list[tuple[str, dict | None, str]]) -> str:
    names = [c[0] for c in cars]
    out = [
        "# Vehicle comparison — every car we have a YAML for",
        "",
        "Generated by `tools/compare_vehicles.py` — do not hand-edit.",
        "`**inherited**` = the field is not written in that YAML, so the record's `$base`"
        " (or the vanilla record) supplies it.",
        "",
        "| | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
        "| where it comes from | " + " | ".join(c[2] for c in cars) + " |",
    ]
    for label, field, _axis in SCALARS:
        if field == "gearChangeTime":
            pass
        out.append(f"| {label} | " + " | ".join(cell(c[1], field) for c in cars) + " |")

    out += ["", "## Gear ladders", "",
            "Reverse is listed separately: it is the first entry of the gear array but it"
            " is not part of the forward ladder.", ""]
    out += ["| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    rev = []
    for _name, car, _note in cars:
        r = car.get("reverse") if car else None
        rev.append(f"0 → {r['maxSpeed']:g} m/s" if r and r.get("maxSpeed") else "—")
    out.append("| reverse | " + " | ".join(rev) + " |")
    depth = max((len(c[1]["ladder"]) for c in cars if c[1]), default=0)
    for i in range(depth):
        tops = []
        for _name, car, _note in cars:
            lad = car["ladder"] if car else []
            g = lad[i] if i < len(lad) else None
            if not g or g["maxSpeed"] is None:
                tops.append("—")
                continue
            top = g["maxSpeed"]
            lo = g["minSpeed"] or 0.0
            span = f", window {top / lo:.2f}×" if lo else ""
            mul = f" · ×{g['torqueMultiplier']}" if g["torqueMultiplier"] is not None else ""
            tops.append(f"{lo:g} → {top:g} m/s ({top * 3.6:.0f} km/h){span}{mul}")
        out.append(f"| gear {i + 1} | " + " | ".join(tops) + " |")

    out += ["", "## Ratio steps between gears", ""]
    out += ["| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for i in range(1, depth):
        cells = []
        for _name, car, _note in cars:
            lad = car["ladder"] if car else []
            if i < len(lad) and lad[i]["maxSpeed"] and lad[i - 1]["maxSpeed"]:
                cells.append(f"{lad[i]['maxSpeed'] / lad[i - 1]['maxSpeed']:.2f}×")
            else:
                cells.append("—")
        out.append(f"| {i} → {i + 1} | " + " | ".join(cells) + " |")

    out += ["", "## Top-gear window (the ratio that decides whether it can be pulled)", ""]
    out += ["| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    cells = []
    for _name, car, _note in cars:
        lad = car["ladder"] if car else []
        if lad and lad[-1]["maxSpeed"]:
            g = lad[-1]
            lo = g["minSpeed"] or 0.0
            span = f"{g['maxSpeed'] / lo:.2f}×" if lo else "—"
            cells.append(f"{lo:g} → {g['maxSpeed']:g} m/s, span {span}, "
                         f"×{g['torqueMultiplier']}")
        else:
            cells.append("—")
    out.append("| last gear | " + " | ".join(cells) + " |")

    out += ["", "## Speed/rpm consistency per gear — a smell, not a law", "",
            "Within a gear, speed and rpm should scale together: `maxSpeed / minSpeed` "
            "ought to equal `maxEngineRPM / minEngineRPM`. Stretch a gear's speed window and "
            "leave the rpm band alone, and the record describes a gear whose ratio changes as "
            "you accelerate. It is **not** a hard rule — the Zonda Revo breaks it by 47 % and "
            "still ships — but it is the cheapest way to spot a gear that was edited by hand.",
            "",
            "| | " + " | ".join(names) + " |",
            "|---|" + "---|" * len(names)]
    worst_cells = []
    for _name, car, _note in cars:
        worst = None
        for g in (car["ladder"] if car else []):
            lo, hi = g["minSpeed"], g["maxSpeed"]
            rlo, rhi = g["minEngineRPM"], g["maxEngineRPM"]
            if not all((lo, hi, rlo, rhi)):
                continue
            dev = abs((hi / lo) / (rhi / rlo) - 1) * 100
            worst = dev if worst is None else max(worst, dev)
        worst_cells.append(f"{worst:.1f} %" if worst is not None else "—")
    out.append("| worst deviation | " + " | ".join(worst_cells) + " |")
    out.append("")
    return "\n".join(out)


def build() -> str:
    cars = []
    for name, rel, note in CARS:
        path = ROOT / rel
        row = load(path)
        if row is None:
            print(f"warning: {rel} missing or not a vehicle tweak — column left empty",
                  file=sys.stderr)
        cars.append((name, row, note))
    return render(cars)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--out", type=Path, default=OUT, help="output file ('-' for stdout)")
    ap.add_argument("--check", action="store_true",
                    help="verify the committed file matches the generated one")
    args = ap.parse_args(argv)

    text = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != text:
            print(f"{OUT.relative_to(ROOT)} is stale — re-run tools/compare_vehicles.py",
                  file=sys.stderr)
            return 1
        print(f"{OUT.relative_to(ROOT)}: up to date")
        return 0
    if str(args.out) == "-":
        sys.stdout.write(text)
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
