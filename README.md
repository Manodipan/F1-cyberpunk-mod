# F1-cyberpunk-mod — `Phoenix_aston_cheats`

A second, independently-named build of the Aston Martin Valkyrie car mod for
Cyberpunk 2077: same model, livery, V12 bank and texture core, **new IDs and file
names in a `phoenix_*` namespace**, with F1-level physics (2000 hp, 500 km/h
gearing). It installs *alongside* the Nexus original, so the stock car stays
pristine and both can be summoned.

The port plan and the physics/tuning decisions live in [`PORT.md`](PORT.md).

## Quick start

```bash
# regenerate the installable mod from the reference files
python3 tools/port_to_phoenix.py --from f1 reference/aston_valkyrie_f1.yaml \
    --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
python3 tools/port_to_phoenix.py --from f1 reference/clone_f1 \
    --out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

# audit: fails on any leftover xaires/_f1 identifier or stock physics value
python3 tools/port_to_phoenix.py --check Phoenix_aston_cheats

# tests
python3 -m unittest discover -s tests -v
```

The two `.archive` files are copied and renamed once, by hand — see
[`Phoenix_aston_cheats/archive/pc/mod/README-COPY-ARCHIVE.md`](Phoenix_aston_cheats/archive/pc/mod/README-COPY-ARCHIVE.md).

## Layout

```
PORT.md                          port plan: stock reference, physics table, rename steps
Phoenix_aston_cheats/            the mod payload — merge into the game root
  archive/pc/mod/                phoenix_aston_valkyrie.archive(.xl)   [copy + rename]
  r6/tweaks/phoenix/             phoenix_aston_valkyrie.yaml           [generated]
  r6/scripts/phoenix_aston_valkyrie/  4 × phoenix_*.reds               [generated]
reference/                       inputs: stock physics, interim `_f1` tuning + scripts
tools/port_to_phoenix.py         §4 rename + §3 physics, one rule set, auditable
tests/test_port.py               15 tests over the rename/physics/check behaviour
docs/                            install + test, rename map, field confidence, localisation, status
```

## Physics at a glance (stock → Phoenix)

| | Stock | Phoenix |
|---|---|---|
| Scanner hp / torque | 680 / 1300 | **2000 / 3824** |
| Gear 7 ceiling | 91.7 (≈330 km/h) | **138.89 (≈500 km/h)** |
| Drag | 1.35 | **0.90** |
| Front grip | 1.29 / 1.15 | **1.60 / 1.50** |
| Rear grip | 1.33 / 1.20 | **2.00 / 1.85** |
| Rear helper / downforce | 0.95 / 0.60 | **1.45 / 1.40** |
| Sway F/R · braking F/R | 11/16 · 1410/1200 | **15/19 · 1850/1550** |
| Springs/damping | 23/22, 2000 | **30/28, 3000** |
| Steering | 94 / 26 / 0.33 | 94 / 26 / 0.33 (v1's 115/35/0.55 wobbled) |

Unchanged: RWD, gears 1–6, mass 1750, maxRPM 10100, inertia, centre of mass,
`turningRollFactor: 0`, tyre size, rotation limiter.

## Read before installing

[`docs/STATUS.md`](docs/STATUS.md) lists exactly what is finished and what still
needs your Windows machine: the copied archives, the script bodies
(`PORT-BODY` markers), the Phoenix name LocKeys, and the pending v2 handling test.
[`docs/INSTALL.md`](docs/INSTALL.md) has the install, summon and 7-test matrix.
