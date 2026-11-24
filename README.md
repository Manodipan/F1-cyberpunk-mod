# F1-cyberpunk-mod — `Phoenix_aston_cheats`

A second, independently-named build of the Aston Martin Valkyrie LMH car mod for
Cyberpunk 2077: same model, livery, V12 bank and texture core, **new IDs and file
names in a `phoenix_*` namespace**, with F1-level physics (2000 hp, 500 km/h
gearing). It installs *alongside* the Nexus original, so the stock car stays
pristine and both can be summoned.

The port plan is [`PORT.md`](PORT.md); what is done vs open is
[`docs/STATUS.md`](docs/STATUS.md).

## Quick start

```bash
make port            # rebuild Phoenix_aston_cheats/r6 from reference/stock (the real mod)
make check           # identifiers, stock physics, script<->YAML references
make test            # 41 tests, incl. "committed tree == tool output"
make verify-package  # the folder is a clean game-root mirror (mod packaging norm)
make package         # -> dist/Phoenix_aston_cheats.zip for Nexus / Vortex
```

## Layout

```
Phoenix_aston_cheats/            the mod = a mirror of the game root (7 files, 12 MB)
  archive/pc/mod/                phoenix_aston_valkyrie.archive(.xl)  — copy of stock + own .xl
  r6/tweaks/phoenix/             phoenix_aston_valkyrie.yaml          — generated
  r6/scripts/phoenix_aston_valkyrie/  phoenix_aston_valkyrie{,_audio,_ekran,_led}.reds
reference/stock/                 verbatim copy of the real mod from main (source of truth)
tools/port_to_phoenix.py         §4 rename + §3 physics, one auditable rule set
tools/package.py                 payload-layout validator + Nexus zip builder
tools/inspect_archive.py         list/lookup paths inside a .archive (no WolvenKit needed)
tools/dump-car-manager.ps1       one-file evidence dump for the paint/compat work
tools/stability-tweak.ps1        optional high-speed steering profile (game copy only)
tools/gearbox-check.ps1          why does it stop at 330 km/h? installed YAML + TweakXL logs
tools/fastcar-dump.ps1           ranks every installed car by top gear, dumps the tuning fields
tools/collect_vehicles.py        corpus + index of every installed vehicle tweak
tools/localization/en-us.json    CR2W onscreens source -> "Phoenix AMV LMH"
tests/                           41 tests (port + packaging + archive inspection)
docs/                            install + test matrix, packaging, rename map, field map,
                                 vehicle model reference, localisation, archive
                                 provenance, status
```

## Physics (stock → Phoenix)

| | Stock | Phoenix |
|---|---|---|
| Scanner hp / torque | 680 / 1300 | **2000 / 3824** |
| Redline | 10100 (a number no curve reaches) | **7900, geared to finish there** |
| Gearbox | 7 gears, top window 77→91.7 m/s (1.19×) | **7 gears, even 1.28× steps, top window 101→138.89 m/s (500 km/h)** |
| Drag | 1.35 | **0.60** |
| Front grip | 1.29 / 1.15 | **1.60 / 1.50** |
| Rear grip | 1.33 / 1.20 | **1.70 / 1.68** (axles within 6 %, as every reference car) |
| Drivetrain | RWD | **AWD** (`DRIVETRAIN` flag; the real LMH is RWD) |
| Rear friction helper | 0.95 / 0.95 | **1.45 / 1.45** |
| Downforce (`maxSpeedFactorGround`) | 0.60 | **0.70** (was 1.40 — twice every reference car) |
| Sway F/R · braking F/R | 11/16 · 1410/1200 | **15/19 · 1850/1550** |
| Springs / damping | 23/22, 2000 | **30/28, 3000** |
| Steering (add / return / threshold / mul) | 94 / inherited / 26 / 0.33 | **94 / 150 / 45 / 0.21** (the 572 km/h car's band, explicit return rate) |

Unchanged: reverse gear, mass 1750 + chassis 1750, inertia,
centre of mass, `turningRollFactor 0`, tyre dimensions, wheel setup geometry.

## How it stays clean

The rename is not hand-edited text — `tools/port_to_phoenix.py` applies one ordered
rule set to the real files, and `make check` fails on any leftover `xaires`/`_f1`
identifier in code, any stock physics value, any `t"Vehicle.phoenix_*"` literal with
no record behind it, or a mismatch between `player_audio_resource` and the audio
metadata the scripts create. Comments (the Turkish engineering notes and the credit
to xaires) are left verbatim on purpose.

## Read before installing

* **Updating:** [`docs/UPDATE.md`](docs/UPDATE.md) — one command (pull + install +
  verify): `powershell -ExecutionPolicy Bypass -File .\tools\update.ps1`
* [`docs/INSTALL.md`](docs/INSTALL.md) — two-mod install, summon, 7-test matrix, logs.
* [`compat/xaires_car_manager/`](compat/xaires_car_manager/README.md) — one-line patch so the
  Car Manager paints the Phoenix (all 149 colours, no art).
* [`docs/VEHICLE-COMPARISON.md`](docs/VEHICLE-COMPARISON.md) — the same fields, side by
  side, for every car we have a YAML for (generated; `make compare`).
* [`docs/VEHICLE-MODEL.md`](docs/VEHICLE-MODEL.md) — how a vehicle actually works in
  CP2077: the record tree, drive model, the three-band steering model, gearboxes,
  speed units, and the engine-level speed limiter.
* [`docs/PAINT.md`](docs/PAINT.md) — how the two-tone paint can actually be changed
  (runtime Car Manager vs baked materials vs CrystalCoat).
* [`docs/WOLVENKIT.md`](docs/WOLVENKIT.md) — the one-time, click-by-click pack that turns
  the label into "Phoenix AMV LMH".
* [`docs/PACKAGING.md`](docs/PACKAGING.md) — why the folder looks like this, and the
  `dist/*.zip` you upload.
* [`docs/STATUS.md`](docs/STATUS.md) — the one open blocker (distinct name LocKey),
   the pending handling test, and three launch risks worth knowing.
* [`docs/LOCALISATION.md`](docs/LOCALISATION.md) — why the card shows the TweakDBID, and the one-file pack that turns it into "Phoenix AMV LMH"
   and the two-line YAML flip.
