# Vehicle reference corpus

Every vehicle tweak installed in the game, indexed — so that when a number looks wrong
("it stops at 330", "it wobbles at 400") there is a real worked example to compare against
instead of a guess.

```powershell
# from the clone root, with the game installed
python tools/collect_vehicles.py --copy     # writes the YAMLs here + INDEX.md
python tools/collect_vehicles.py            # index only (nothing written except INDEX.md)
python tools/collect_vehicles.py --tweaks "G:\...\r6\tweaks\some_mod"
```

## What is tracked, and what is not

| File | In git? | Why |
|---|---|---|
| `INDEX.md` | **yes** | facts: top gear, drag, torque, mass, steering authority, damping, per car. This is the part we actually compare against. |
| `*/**.yaml` | **yes** | other authors' tweak files, kept **for comparison only**. Never copied into `Phoenix_aston_cheats/`, never in the Nexus zip — `make verify-package` fails if that ever happens. Be aware this is a public repo: most Nexus vehicle mods ask that their files not be re-uploaded, and this is a copy, not an upload of the mod. |
| `README.md` | yes | this file |

If you want a specific car's full record in git (to read, not to ship), copy **only that
file** and say so in the commit — one file for study is a different thing from republishing
a library.

**Currently tracked by exception:** `jesko_attack.yaml` — the 572 km/h reference car
(`docs/TOPSPEED-TEST.md` §3c explains what it proved). Note that its last gear says
283 km/h while the car does 572: a gear table's `maxSpeed` is a shift point, not a cap.

## Keeping the index honest

`INDEX.md` is generated from whatever is in this folder. If it disagrees with the files
next to it (a car added by hand, or a collector run that only saw part of the game):

```powershell
python tools/collect_vehicles.py --index-only reference/vehicles
```

## Reading `INDEX.md`

* `km/h` / `m/s` — the **last gear's `maxSpeed`**, which is the game's ceiling for that car
* `drag` — `airResistanceFactor`; the wall at speed
* `steer` — `wheelTurnMaxAddPerSecond` + `turnUpdateMaxSpeedTurnMul` (authority above
  `turnUpdateMaxSpeedThreshold`)
* `mass` — `total_mass`; torque is `engineMaxTorque`

For the Phoenix: **500 km/h / 138.89 m/s, 8 gears, drag 0.90, 3824 Nm, 1750 kg,
steering 94 / 0.33.**

Nothing in this folder is part of the mod payload. `Phoenix_aston_cheats/` stays entirely
ours; `make verify-package` enforces that.
