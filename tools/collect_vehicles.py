#!/usr/bin/env python3
"""
Collect every vehicle tweak installed in the game into one reference corpus + index.

Why: when a number looks wrong ("it stops at 330", "it wobbles at 400") the fastest way
to a sane value is another car that already does it. Every modded car's YAML is a free
worked example of gear spacing, drag, steering authority and damping.

    python tools/collect_vehicles.py                      # index only, from the game folder
    python tools/collect_vehicles.py --copy               # index + copies to reference/vehicles/
    python tools/collect_vehicles.py --tweaks <dir>       # a specific tweaks folder
    python tools/collect_vehicles.py --index-only <dir>   # rebuild INDEX.md from a local corpus

Output:
    reference/vehicles/<mod-folder>/<file>.yaml   (only with --copy)
    reference/vehicles/INDEX.md                   always

Nothing here is shipped inside Phoenix_aston_cheats/: it is reference material, so the
mod payload stays entirely ours.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME = Path(r"G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty")
DEST = ROOT / "reference" / "vehicles"

VEHICLE_MARKERS = ("airResistanceFactor", "vehDriveModelData", "vehEngineData", "gears:")

FIELDS = [
    "airResistanceFactor",
    "engineMaxTorque",
    "maxRPM",
    "total_mass",
    "wheelTurnMaxAddPerSecond",
    "turnUpdateMaxSpeedThreshold",
    "turnUpdateMaxSpeedTurnMul",
    "turningRollFactor",
    "maxSpeedFactorGround",
    "maxAngularSpeedRad",
    "driftLimit",
    "frictionMulLateral",
    "springDamping",
    "swaybarStiffness",
]

RE_MAXSPEED = re.compile(r"^\s*maxSpeed\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.MULTILINE)
RE_FIELD = {f: re.compile(r"^\s*" + f + r"\s*:\s*([^\s#]+)", re.MULTILINE) for f in FIELDS}
RE_RECORD = re.compile(r"^(Vehicle\.[A-Za-z0-9_]+)\s*:\s*$", re.MULTILINE)


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def profile(path: Path) -> dict | None:
    text = read_text(path)
    if not any(m in text for m in VEHICLE_MARKERS):
        return None
    speeds = [float(v) for v in RE_MAXSPEED.findall(text)]
    if not speeds:
        return None
    # prefer the maxSpeed of the gear records the engine actually lists: other records in
    # the same file (rotation limiters, friction helpers) also carry a maxSpeed field.
    gear_names = []
    m = re.search(r"^\s*gears\s*:\s*\[([^\]]+)\]", text, re.MULTILINE)
    if m:
        gear_names = [g.strip() for g in m.group(1).split(",") if g.strip()]
    else:
        gear_names = [g for g in re.findall(r"^\s*-\s*!append\s+(\S+)", text, re.MULTILINE)]
    gear_speeds = []
    if gear_names:
        blocks = {}
        for block in re.split(r"(?m)^(?=[A-Za-z][A-Za-z0-9_.]*:\s*$)", text):
            bm = re.match(r"^([A-Za-z][A-Za-z0-9_.]*)\s*:", block)
            if bm:
                blocks[bm.group(1)] = block
        for name in gear_names:
            block = blocks.get(name)
            if not block:
                continue
            hm = RE_MAXSPEED.search(block)
            if hm:
                gear_speeds.append(float(hm.group(1)))
    if gear_speeds:
        speeds = gear_speeds
    # only real vehicle records: the ones whose block carries vehDriveModelData
    recs = []
    for block in re.split(r"(?m)^(?=Vehicle\.[A-Za-z0-9_]+:\s*$)", text):
        m = re.match(r"^(Vehicle\.[A-Za-z0-9_]+)\s*:", block)
        if m and "vehDriveModelData" in block:
            recs.append(m.group(1))
    row = {
        "path": path,
        "top": max(speeds),
        "gears": len(speeds),
        "records": recs or [r for r in RE_RECORD.findall(text)
                             if not re.search(r"_(data|manufacturer|icon|purchasable)$", r)],
    }
    for f, rx in RE_FIELD.items():
        m = rx.search(text)
        row[f] = m.group(1) if m else ""
    return row


def collect(tweaks: Path, copy: bool, dest: Path) -> list[dict]:
    rows = []
    for path in sorted(tweaks.rglob("*.yaml")):
        row = profile(path)
        if not row:
            continue
        rel = path.relative_to(tweaks)
        row["rel"] = str(rel).replace("\\", "/")
        if copy:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        rows.append(row)
    rows.sort(key=lambda r: r["top"], reverse=True)
    return rows


def index_from_corpus(dest: Path) -> list[dict]:
    rows = []
    for path in sorted(dest.rglob("*.yaml")):
        row = profile(path)
        if not row:
            continue
        row["rel"] = str(path.relative_to(dest)).replace("\\", "/")
        rows.append(row)
    rows.sort(key=lambda r: r["top"], reverse=True)
    return rows


def fmt(row: dict) -> str:
    kmh = round(row["top"] * 3.6)
    recs = ", ".join(r.replace("Vehicle.", "") for r in row["records"][:2]) or "-"
    return (
        f"| {kmh} | {row['top']:g} | {row['gears']} | {row.get('airResistanceFactor') or '-'} "
        f"| {row.get('engineMaxTorque') or '-'} | {row.get('total_mass') or '-'} "
        f"| {row.get('wheelTurnMaxAddPerSecond') or '-'} | {row.get('turnUpdateMaxSpeedTurnMul') or '-'} "
        f"| {recs} | `{row['rel']}` |"
    )


def write_index(rows: list[dict], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "INDEX.md"
    lines = [
        "# Vehicle reference index",
        "",
        f"Generated {date.today().isoformat()} by `tools/collect_vehicles.py` — do not hand-edit.",
        f"{len(rows)} vehicle tweak(s), sorted by top gear.",
        "",
        "`km/h` and `m/s` come from the **last gear's `maxSpeed`**, which is what the game",
        "uses as the vehicle's ceiling. `drag` is `airResistanceFactor`, `steer` is",
        "`wheelTurnMaxAddPerSecond` / `turnUpdateMaxSpeedTurnMul` (authority above",
        "`turnUpdateMaxSpeedThreshold`).",
        "",
        "| km/h | m/s | gears | drag | torque | mass | steer | mul | records | file |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    lines += [fmt(r) for r in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--tweaks", type=Path, default=None, help="tweaks folder (default: <game>/r6/tweaks)")
    ap.add_argument("--dest", type=Path, default=DEST)
    ap.add_argument("--copy", action="store_true", help="also copy the YAMLs into --dest")
    ap.add_argument("--index-only", type=Path, default=None, metavar="DIR",
                    help="rebuild INDEX.md from an existing corpus instead of the game folder")
    args = ap.parse_args()

    if args.index_only:
        rows = index_from_corpus(args.index_only)
        out = write_index(rows, args.index_only)
        print(f"{len(rows)} vehicle file(s) indexed -> {out}")
        return 0

    tweaks = args.tweaks or (args.game / "r6" / "tweaks")
    if not tweaks.is_dir():
        print(f"tweaks folder not found: {tweaks}", file=sys.stderr)
        print("pass --tweaks <dir> or --game <game root>", file=sys.stderr)
        return 2

    rows = collect(tweaks, args.copy, args.dest)
    if not rows:
        print(f"no vehicle yaml found under {tweaks}", file=sys.stderr)
        return 1

    out = write_index(rows, args.dest)
    print(f"{len(rows)} vehicle file(s)")
    if args.copy:
        print(f"copied into {args.dest.relative_to(ROOT) if args.dest.is_relative_to(ROOT) else args.dest}")
    print(f"index -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print()
    for r in rows[:10]:
        print(f"  {round(r['top'] * 3.6):>5} km/h  {r['gears']:>2} gears  {r['rel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
