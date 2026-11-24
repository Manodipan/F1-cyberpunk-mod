# Top-speed test — hands off the wheel

Goal: prove the v2 physics reach the **138.89 m/s (500 km/h)** ceiling in gear 7, with no
human input in the loop. Auto Drive drives the car with the game's own AI, so the throttle
is applied smoothly and consistently — better evidence than a keyboard hold.
Background on what sets the ceiling (gears, drag, and the engine-level speed limiter):
[`VEHICLE-MODEL.md`](VEHICLE-MODEL.md) §4–§5.

Test mod: **Auto Drive Enhanced** (Nexus 23157, by nobo). Requires ArchiveXL, redscript,
Input Loader, TweakXL; Mod Settings is optional but is where the knobs live.

## 1. Configure the mod (once)

Settings → **Mod Settings** → **Auto Drive** (main menu or pause menu, the tab the mod adds):

| Setting | Set to | Why |
|---|---|---|
| **Max speed** | the vehicle's maximum / **100 %** | vanilla autodrive obeys a road-speed limiter; this is the setting that lifts it. If yours is a plain number, use `500` (km/h) |
| **Driving AI** | **Modded AI** | drives with the car's own physics instead of the vanilla planner, which is what we want measured |
| Restrictions (v0.0.0.15+) | remove **"valid lane"** and **"not in combat"** | the AI otherwise aborts the run on a lane it does not like |
| Cheat settings (v0.0.0.19+) | optional: **no damage** | a 500 km/h kiss with a barrier otherwise ends the run before the number is read |

Version note: **0.0.0.20+** is the first that stops an internal minimum speed from
overriding your max-speed setting, and **0.0.0.21+** is the one that works on 2.5. If
the car refuses to pass ~150 km/h, that is the version, not the car.

## 2. Run it

1. Spawn the Phoenix, sit in it.
2. Set a destination down a **long straight** — the Badlands highway is the usual one.
   Corners are the enemy of this test: the AI brakes for them, and we are measuring the
   drag wall, not cornering.
3. Engage autodrive and **do not touch the controls**.
4. Watch the car's own HUD read-out (the Phoenix dash is scripted, so it reports km/h
   directly) and the gear indicator.

## 3. What to record

| Reading | Pass | Notes |
|---|---|---|
| Top speed reached | **~500 km/h** (138.89 m/s), then flat | the drag wall is `airResistanceFactor 0.90`; if it stops at e.g. 420, that number is what we tune |
| Gear at top speed | **7th**, no hunting between 6 and 7 | gear 7 is a long overdrive by design |
| Time to 300 km/h | record it, no target yet | acceleration is torque 3824 Nm over 1750 kg |
| Steering behaviour | tracks straight hands-off | any **wobble here is the car**, because no human is steering |
| Audio / LEDs | revs climb, LEDs sweep, no cut-out | audio ceiling = 138.89 |

## 3b. Known: it plateaus at ~330 km/h (reported 2026-11-24)

**330 km/h = 91.7 m/s = the *stock* Valkyrie's gear-7 `maxSpeed`.** Our record sets that
same field to **138.89**, so a hard plateau on 91.7 is a **ceiling being enforced**, not
the car running out of power: with `engineMaxTorque 3824` and `airResistanceFactor 0.90`
the terminal velocity is north of 450, nowhere near 330.

Three candidates, cheap to separate:

| Candidate | Check |
|---|---|
| the installed YAML is stale (old gear set) | `tools/gearbox-check.ps1` prints the **installed** file's gear 7 and counts `138.89` |
| the `gears:` `!remove` / `!append` block did not take (TweakXL error) | same file shows the TweakXL log lines; an `Ambiguous`/`not found` on the gear records is the answer |
| drag wall after all | negative result of both, *and* the engine sits **mid-rev** at the plateau |

In-game tell, no tools: at the plateau, are the rev lights pinned (engine maxed → the game
thinks that is top gear) or mid-scale (engine has headroom → drag)?

```powershell
cd $HOME\f1-cyberpunk-mod
powershell -ExecutionPolicy Bypass -File .\tools\gearbox-check.ps1
```

If the file is clean and the logs are silent, the A/B test settles it: set gear 7
`maxSpeed` to `100` (360 km/h) and rerun — plateau moves to 360 means it is the gear
ceiling and the append is being ignored; still 330 means it is drag, and
`airResistanceFactor` comes down from 0.90.

## 3c. The 572 km/h reference (Koenigsegg Jesko Attack) — what it proved

`reference/vehicles/jesko_attack/jesko_attack.yaml` is that car's actual tweak file (kept
from the corpus the collector built on 2026-11-24). Its numbers:

| | Jesko Attack (572 km/h) | Phoenix (stops at 330) |
|---|---|---|
| last gear `maxSpeed` | **78.5 m/s = 283 km/h** | 138.89 m/s = 500 km/h |
| gears | 8, one explicit `gears: [ … ]` list | 8, via `8 × !remove` + `8 × !append` |
| `airResistanceFactor` | **0.66** | 0.90 |
| `engineMaxTorque` | 1000 | 3824 |
| `total_mass` | 1800 | 1750 |
| steering | 137 / threshold **45** / mul **0.21** | 94 / 26 / 0.33 |
| `maxSpeedFactorGround` (downforce) | 0.7 | 1.40 |
| `turningRollFactor` | 1 | 0 |
| `driftLimit` / `maxAngularSpeedRad` | 2.3 / 2.6 | 1.6 / 2.6 |
| `frictionMulLateral` | 1.3 | 1.60 front / 2.00 rear |

Two conclusions, and one of them kills our earlier theory:

1. **A car's top speed is not its gear table.** The Jesko does 572 km/h on a gear set
   whose last entry says 283 km/h — exactly 2× over. So `maxSpeed` per gear is the
   *shift point*, not a hard cap, and "330 = the stock 91.7 gear value" was a coincidence
   of arithmetic, not a proof of where the wall is.
2. **Our engine block is the suspicious part, not our gear numbers.** It inherits
   `Vehicle.VehicleEngineData_4_SuperSport` and then removes that record's 8 inline gears
   and appends ours. If those 8 `!remove` lines miss their targets, the inherited gear set
   stays **in front of** ours and the transmission drives the car it inherited from. The
   Jesko avoids this entirely: one explicit list, no inherited gears at all.

**Fixed in the deliverable, 2026-11-24.** The port tool now emits that form itself
(`explicit_gears()` in `tools/port_to_phoenix.py`), so the shipped YAML carries

```yaml
gears: [ Vehicle.phoenix_amv_gear_r, …, Vehicle.phoenix_amv_gear_7 ]
```

with no `!remove` and no `!append`, and two tests enforce it
(`test_gearbox_is_one_explicit_list`, plus the existing "committed tree == tool output").
Nothing to install by hand: `git pull`, copy the deliverable YAML over the game's copy,
restart.

**Result in game, 2026-11-24: still ~300 km/h, still wobbly.** So the explicit list was
necessary (a fragile block is gone for good) but it was *not* the wall. §3d is what the
second failure revealed.

```powershell
$d = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\r6\tweaks\phoenix"
Copy-Item "$d\phoenix_aston_valkyrie.yaml" "$d\phoenix_aston_valkyrie.yaml.stock" -Force   # once, as insurance
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" $d -Force
```


## 3d. The wall was the gear *ratio* — the overdrive (2026-11-24, second failure)

Conclusion 1 in §3c was half right in a way that mattered. `maxSpeed` per gear is not a
cap, but it is not decorative either: **a gear's window sets its ratio**, and the Phoenix
was given one heroic overdrive:

| | window | ratio span | torque multiplier |
|---|---|---|---|
| stock 7th | 77 → 91.7 m/s | **1.19×** | 0.306 |
| Phoenix 7th (failed) | 77 → 138.89 m/s | **1.80×** | 0.306 |
| Phoenix 6th | 66 → 80.6 m/s | 1.22× | 0.348 |

One gear was asked to cover **277 → 500 km/h** while carrying the weakest multiplier in
the box — and 6th still ended at 290 km/h. So the car ran out of pull exactly where its
last *usable* gear ended: ~300 km/h, twice reported. The stock car never showed this
because its 7th only spans 15 m/s, which is why "stock tops out at exactly 91.7" looked
like a cap and was really a short, pullable top gear.

The fix is a real 7-speed ladder — equal steps, short top window, tapering multiplier
(`PHOENIX_GEARBOX` in `tools/port_to_phoenix.py`, mirrored into the redscript virtual
gearbox so the HUD revs stay honest):

| gear | window (m/s) | tops | torque multiplier |
|---|---|---|---|
| 1 | 0 → 32 | 115 km/h | 0.78 |
| 2 | 29.8 → 40.9 | 147 | 0.72 |
| 3 | 38 → 52.2 | 188 | 0.665 |
| 4 | 48.5 → 66.6 | 240 | 0.61 |
| 5 | 61.9 → 85 | 306 | 0.56 |
| 6 | 79.1 → 108.6 | 391 | 0.53 |
| 7 | 101 → **138.89** | **500** | 0.50 |

Steps are 1.276–1.279× — the spread a seven-speed actually needs to reach 500 from a
sane first gear. No single gear has to double its speed any more.

Two more changes ride along, because they answer the other complaint and a different
question respectively:

| Change | From | To | Why |
|---|---|---|---|
| `turnUpdateMaxSpeedThreshold` / `…TurnMul` | 26 m/s / 0.33 | **45 m/s / 0.21** | the 572 km/h car's band: keep authority to 162 km/h, then cut to 21 %. Ours still handed over a third of full lock at 400+ |
| `airResistanceFactor` | 0.90 | **0.60** | second lever on the same wall; 0.66 is what the 572 km/h car uses |

Install after `git pull` (YAML **and** scripts — the redscript gear table changed too):

```powershell
$root = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" `
          "$root\r6\tweaks\phoenix\" -Force
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie\*" `
          "$root\r6\scripts\phoenix_aston_valkyrie\" -Force
```

Restart the game (TweakXL reads YAML at boot; CET reload alone does not take).

| Outcome | What it means | Next |
|---|---|---|
| **~500 or beyond** | the ladder was the wall | if it overshoots, raise `airResistanceFactor` in steps (0.60 → 0.70 → 0.80) until it sits at 500 |
| stalls **~390** (= new 6th) | the *next* ratio is still too tall for the available force | drop 7th's `minSpeed` (101 → 95) and raise its multiplier (0.50 → 0.56) |
| stalls **~300 again** | ratio theory is dead: it is the engine-level speed limiter or the engine record itself | see `docs/VEHICLE-MODEL.md` §5c — that needs the RED4ext unlimiter, not YAML |
| still wobbly at 400+ | steering bands are not the only cause; next suspects are rear/front lateral friction (2.00 vs 1.60 — every known-good car runs them near equal) | report the speed it starts at |

## 4. If it wobbles while autodriving

That is the useful result of removing human input: **any** yaw oscillation is now
attributable to the physics, not to your thumbs. The cause is almost certainly steering
authority that was tuned for 330 km/h:

At 500 km/h the same wheel angle generates roughly **2.3×** the lateral acceleration it
does at 330, so a third of full authority is a lot. **The high-speed band is now in the
deliverable** (§3d: threshold 45 m/s, multiplier 0.21), so the script below is no longer
the first move — it is the fallback if the shipped band is still not enough. It works on
the game's copy of the YAML (backup kept, repo untouched, reversible):

```powershell
cd $HOME\f1-cyberpunk-mod
powershell -ExecutionPolicy Bypass -File .\tools\stability-tweak.ps1
```

It changes 94 → **64**, threshold 26 → **30**, mul 0.33 → **0.12**, prints the three lines
back, and needs a game restart (TweakXL reads YAML at boot). Undo with `-Revert`.

If the car then tracks straight but feels numb at low speed, the honest fix is a
speed-dependent curve rather than one number, and the values above are the starting point
for that second pass.

## 5. Report

One line per row of §3, plus one sentence per surprise ("held 7th at 470, never reached
the wall"; "yaw oscillation started at ~350 km/h and grew"). That is what turns v2 into a
final tune instead of a guess.
