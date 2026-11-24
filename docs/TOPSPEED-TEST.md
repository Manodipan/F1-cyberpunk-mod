# Top-speed test — hands off the wheel

Goal: prove the v2 physics reach the **138.89 m/s (500 km/h)** ceiling in gear 7, with no
human input in the loop. Auto Drive drives the car with the game's own AI, so the throttle
is applied smoothly and consistently — better evidence than a keyboard hold.

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

## 3c. Borrowed reference: a 572 km/h car

There is a mod car known to reach **572 km/h** and stay driveable on straights (though not
hairpin-at-500 stable — nobody's is). That car is proof the engine will go past the vanilla
gear ceiling, and its numbers are a far better starting point than our guesses.

`tools/fastcar-dump.ps1` scans every vehicle YAML installed in the game, **ranks them by
top gear** and prints the deciding fields for anything above 400 km/h:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\fastcar-dump.ps1
powershell -ExecutionPolicy Bypass -File .\tools\fastcar-dump.ps1 -Tweaks "G:\...\r6\tweaks\that_mod"
```

What we borrow, in order of value:

| Field | Why it matters |
|---|---|
| top gear `maxSpeed` + `gears` count | how it gets past 91.7 m/s — more gears, or a longer last gear |
| `airResistanceFactor` | the actual drag wall at that speed |
| `wheelTurnMaxAddPerSecond` / `turnUpdateMaxSpeedTurnMul` | its steering authority at 500+ |
| `frictionMulLateral`, `swaybarStiffness`, `springDamping` | how it stays planted while doing it |
| downforce helper (`maxSpeedFactorGround`) | 1.40 for us, unknown for it |

Realistic target, given that reference: **500 km/h stable on a straight**, hands-off, in
7th. Hairpin stability at 500 is not a goal — it is a physical impossibility at that
speed and no mod car has it.

## 4. If it wobbles while autodriving

That is the useful result of removing human input: **any** yaw oscillation is now
attributable to the physics, not to your thumbs. The cause is almost certainly steering
authority that was tuned for 330 km/h:

```yaml
wheelTurnMaxAddPerSecond: 94      # how fast the wheels can turn
turnUpdateMaxSpeedThreshold: 26   # above 26 m/s (94 km/h) ...
turnUpdateMaxSpeedTurnMul: 0.33   # ... authority is cut to 33 %
```

At 500 km/h the same wheel angle generates roughly **2.3×** the lateral acceleration it
does at 330, so 33 % is still a lot. One command applies a high-speed profile to the
game's copy of the YAML (backup kept, repo untouched, reversible):

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
