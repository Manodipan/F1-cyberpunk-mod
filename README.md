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
make test            # 36 tests, incl. "committed tree == tool output"
make verify-package  # the folder is a clean game-root mirror (mod packaging norm)
make package         # -> dist/Phoenix_aston_cheats.zip for Nexus / Vortex
```

## Layout

```
Phoenix_aston_cheats/            the mod = a mirror of the game root (7 files, 12 MB)
  archive/pc/mod/                phoenix_aston_valkyrie.archive(.xl)  — renamed copy of stock
  r6/tweaks/phoenix/             phoenix_aston_valkyrie.yaml          — generated
  r6/scripts/phoenix_aston_valkyrie/  phoenix_aston_valkyrie{,_audio,_ekran,_led}.reds
reference/stock/                 verbatim copy of the real mod from main (source of truth)
tools/port_to_phoenix.py         §4 rename + §3 physics, one auditable rule set
tools/package.py                 payload-layout validator + Nexus zip builder
tests/                           36 tests (port + packaging) over the real files
docs/                            install + test matrix, packaging, rename map, field map,
                                 localisation, archive provenance, status
```

## Physics (stock → Phoenix)

| | Stock | Phoenix |
|---|---|---|
| Scanner hp / torque | 680 / 1300 | **2000 / 3824** |
| Gear 7 ceiling | 91.7 (≈330 km/h) | **138.89 (≈500 km/h)** |
| Drag | 1.35 | **0.90** |
| Front grip | 1.29 / 1.15 | **1.60 / 1.50** |
| Rear grip | 1.33 / 1.20 | **2.00 / 1.85** |
| Rear friction helper | 0.95 / 0.95 | **1.45 / 1.45** |
| Downforce (`maxSpeedFactorGround`) | 0.60 | **1.40** |
| Sway F/R · braking F/R | 11/16 · 1410/1200 | **15/19 · 1850/1550** |
| Springs / damping | 23/22, 2000 | **30/28, 3000** |
| Steering (add / threshold / mul) | 94 / 26 / 0.33 | 94 / 26 / 0.33 (v1's 115/35/0.55 wobbled) |

Unchanged: RWD, gears R and 1–6, mass 1750 + chassis 1750, maxRPM 10100, inertia,
centre of mass, `turningRollFactor 0`, tyre dimensions, wheel setup geometry.

## How it stays clean

The rename is not hand-edited text — `tools/port_to_phoenix.py` applies one ordered
rule set to the real files, and `make check` fails on any leftover `xaires`/`_f1`
identifier in code, any stock physics value, any `t"Vehicle.phoenix_*"` literal with
no record behind it, or a mismatch between `player_audio_resource` and the audio
metadata the scripts create. Comments (the Turkish engineering notes and the credit
to xaires) are left verbatim on purpose.

## Read before installing

* [`docs/INSTALL.md`](docs/INSTALL.md) — two-mod install, summon, 7-test matrix, logs.
* [`docs/PACKAGING.md`](docs/PACKAGING.md) — why the folder looks like this, and the
  `dist/*.zip` you upload.
* [`docs/STATUS.md`](docs/STATUS.md) — the one open blocker (distinct name LocKey),
   the pending handling test, and three launch risks worth knowing.
* [`docs/LOCALISATION.md`](docs/LOCALISATION.md) — exact JSON paths from the real `.xl`
   and the two-line YAML flip.
