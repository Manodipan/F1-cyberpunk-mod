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
tests/                           123 tests (port + packaging + archive inspection)
docs/                            install + test matrix, packaging, rename map, field map,
                                 vehicle model reference, localisation, archive
                                 provenance, status
```

## Physics (stock → Phoenix)

**IMPORTANT — read [docs/SPEED-CAP.md](docs/SPEED-CAP.md) before planning any top speed above
360 km/h.** The game has a hard engine-level vehicle limit at exactly 100 m/s, and it is bypassable
only with a native plugin. **As of build 900033 the car is designed for 95 m/s, inside that wall**: the game is the stock Aston mod's physics plus one gear field, one ratio and torque:**
all four wheels drive, drag and torque are sized from measurement, and the top gear is stretched to
155 m/s. The base measured **80 m/s under ADE / 86 by hand** on this pipeline —
the reference car's own numbers. AWD is a handling override we keep on purpose; see below. Only two
things differ, and neither is a handling number: the scanner's `horsepower` field carries the build
stamp, and the speedometer is ours (true km/h for every car). Everything the car does — gearbox
91.7 m/s top gear, drag 1.35, mass 1750, torque 1300, steering 94, grip, springs, swaybars — is
the car that was measured at **~80 m/s under ADE and ~85 m/s by hand**, the best result on record.

| | Stock (the mod) | Phoenix (shipped, 900020) |
|---|---|---|
| Gearbox | 7 gears, top window 77→91.7 m/s (330 km/h) | **7th 77→98 m/s ceiling, car balances at ~95-97** (step 21) |
| Mass · Drag | 1750 · 1.35 | 1750 · **0.55** (step 16) |
| Torque · Redline | 1300 · 10 100 | **1650** · 10 100 (step 21, sized so DRAG sets the top, not the rev limiter) |
| Drivetrain | RWD (front `isDrive: false`) | **AWD** — all four wheels drive, handbrake still rear only |
| Grip F/R | 1.29/1.15 · 1.33/1.20 | **identical** |
| Yaw inertia | 3050 / 900 / 3530 | **3355 / 990 / 3883** (step 15, +10 %) |
| Downforce (`maxSpeedFactorGround`) | 0.60 | **identical** |
| Steering (add / threshold / mul) | 94 / 26 / 0.33 | **85** / 26 / **0.21** (step 15: −10 % rate, −36 % authority at speed) |
| Springs · damping · swaybar | 23/22 · 2000 · 11/16 | **identical** |
| Scanner hp | 680 | **900020** — build stamp, not a power claim |
| Speedometer | the game's 2.07× curve | **true km/h, all vehicles** |

The earlier "Phoenix" column — the Jesko Attack's physics copied verbatim, plus a five-field
stability overlay — is **reverted**. It measured **63 m/s ADE / 77 manual** against the stock car's
**80 / 85**; eight builds of tuning got it to 72 at best. `docs/STABILITY.md` keeps the full ladder
as a record of what was falsified. `RESTORE_STOCK_PHYSICS = True` in `tools/port_to_phoenix.py`
holds this state; the whole Jesko control path is still in the file, one flag away.

## Build stamp in the scanner

The car's scanner readout shows **900000 + build number** instead of a horsepower figure, e.g.
`900015` = build 15. It is the only number the game shows on demand, so it answers "did TweakXL
actually reload my file?" in one glance: if the number changed, the new YAML is live; if it did not,
the old one is cached. `BUILD` lives in `tools/port_to_phoenix.py` and is bumped with any change to
the generated YAML.

## Stability

The car weaves under ADE because ADE is a lagging controller and the reference damping rates leave
this chassis underdamped — see `docs/STABILITY.md`. A five-field overlay (`STABILITY_OVERLAY`)
raises the low-rate bound/rebound damping to the stock Aston's known-good rates, restores
anti-roll damping, slows the steering rate 20 % and removes roll-to-turn coupling. Power, drag,
gearing, mass and brakes are untouched, so the top-speed work is unaffected.

## The 500 km/h design

`docs/TOPSPEED-DESIGN.md` (generated by `tools/land_speed_design.py`) derives the target from the
four road cars that actually reached 447-533 km/h — Jesko Absolut, SSC Tuatara, Chiron Super Sport
300+, Agera RS — checks the standard `P = ½ρCdA·v³` model against their verified records (within
about 11 %), and only then sizes the Phoenix: **CdA 0.52 class, ~1,200 hp for a 500 km/h plateau**, and
what that means as a ratio to the car we measured at 278.

## Speedometer: true speed, every car

The game's HUD never shows a car's speed. It runs it through a `speed_to_multiplier` display
curve that inflates as speed rises. Measured on 2026-11-24 with timed 1 km runs, rolling start,
same stretch:

| car | 1 km | real speed | HUD read | inflate |
|---|---|---|---|---|
| Jesko | 13 s | 277 km/h | **572** | 2.07× |
| Phoenix (control build) | 13 s | 277 km/h | **278** | 1.00× |

The reference car never did 500. It does 277 and writes 572 on the dashboard, which is why
copying its data exactly landed us on the same real speed. An unrelated Zonda mod sits at
1.97× on a declared 180 km/h gearbox: it is one HUD function, not any car's data, and it touches
nothing physical.

`TRUE_SPEEDO_ALL_VEHICLES` in `tools/port_to_phoenix.py` (default on) extends the Phoenix's
bypass to **every vehicle**: `hudCarController.OnSpeedValueChanged` writes `SpeedValue × 3.6`
for whatever you are driving, so the number is the speed the car is actually doing. The game's
imperial setting is spent on something better — it shows the raw **m/s**, the engine's own unit,
since nobody here drives in miles. `MPH_MODE_SHOWS_MPS = False` restores mph. Set it to `False` for Phoenix-only. The custom dash, rev LEDs and audio stay
gated on our car either way.

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
* [`docs/HOW-CARS-WORK.md`](docs/HOW-CARS-WORK.md) — the long answer: how modders build a
  car, how the game interprets the numbers, and where that maps onto real physics.
* [`docs/TUNING-FROM-REAL-RACING.md`](docs/TUNING-FROM-REAL-RACING.md) — the real Valkyrie LMH's
  numbers, the 15 vanilla torque curves, and why 2 000 hp = 500 km/h is honest arithmetic.
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

## Removing it

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\uninstall.ps1
```

Deletes `r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml` and `r6\scripts\phoenix_aston_valkyrie\`
after backing both up to `%USERPROFILE%\phoenix-uninstall-<timestamp>\`. Nothing else is touched —
in particular **not** `r6\scripts\auto_drive_enhanced\`, which this repo only carries a read-only
copy of. The tweak YAML overrides fields rather than replacing the record, so removing it is a full
return to stock physics. Add `-Purge` to skip the backup.

