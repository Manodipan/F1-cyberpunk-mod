# How vehicle mods work: building them, what the game does with them, and where reality fits

Three questions, answered with what we have actually measured in this repo rather than
what the wikis assert. Everything here is labelled **measured** (we drove it or computed it
from our own files), **documented** (a source says so), or **inferred** (my reading of the
numbers, could be wrong).

Field-by-field reference: [`VEHICLE-MODEL.md`](VEHICLE-MODEL.md). Five cars side by side:
[`VEHICLE-COMPARISON.md`](VEHICLE-COMPARISON.md).

---

# 1. How modders make a car

## 1.1 The two halves

A car mod is two completely different products glued together:

| Half | What it is | Tools |
|---|---|---|
| **Assets** | the mesh, materials, wheels, doors, glass, destruction, icons | Blender → WolvenKit → `.archive` (+ `.archive.xl` for ArchiveXL) |
| **Data** | the records that say how it drives, sounds, and what the scanner shows | plain text: `r6\tweaks\**\*.yaml` (TweakXL) + `r6\scripts\**\*.reds` (redscript) |

The asset half is a *path* in the data half (`entityTemplatePath: xaires\aston_valkyrie\aston_valkyrie.ent`).
That is why a car mod that "looks right but drives wrong" is a data problem, not a model
problem — and why the work in this repo never touches the archive.

## 1.2 The record chain

A vehicle is not one record, it is a small graph:

```
Vehicle.<name>                     gamedataVehicle_Record   <- the car itself
├── entityTemplatePath + appearanceName   -> the .ent in the archive
├── vehEngineData           -> record    torque, redline/rpm, gears, shift timing
├── vehDriveModelData       -> record    mass, grip, steering, suspension, drag, downforce
├── vehWheelDimensionsSetup -> record    tyre radius/width, rim, offset
├── vehDataPackage          -> record    seats, doors, driver combat type
├── destruction             -> record    how it breaks
├── vehicleUIData           -> record    scanner card: year, horsepower, mass, info LocKey
├── manufacturer, icon      -> records   logos and thumbnails (inkatlas)
└── displayName             -> LocKey    the name, via an onscreens localisation archive
```

Three ways to fill that graph, and the choice matters more than any single number:

| Strategy | Who | Cost |
|---|---|---|
| **clone** an existing player car (`$base:`) and override a handful of fields | most mods, including this one | every field you *don't* write is inherited — and silently governs behaviour |
| **write records out fully** (`$type:` on everything) | the Jesko | you must know every field, but nothing surprises you |
| **clone the base *and* write the physics fully** | the Quadra retune | the safest of the lot: known-good relationships, explicit physics |

Both failures in this repo came from the first row. The gearbox inherited a set of gears we
thought we had replaced; the engine inherited a **torque curve** that silently capped revs
about 2 000 rpm below what the record claimed. (Both measured, both fixed 2026-11-24.)

## 1.3 Gears are where mods die

A gearbox is an array of records. Two ways to build it:

```yaml
# pattern A: surgery on the inherited set  (what the stock mod did)
gears:
  - !remove Vehicle.VehicleEngineData_4_SuperSport_inline0     # x8
  - !append Vehicle.xaires_amv_gear_r                          # x8

# pattern B: one explicit list  (what the Jesko and, now, this mod do)
gears: [ Vehicle.phoenix_amv_gear_r, ... Vehicle.phoenix_amv_gear_7 ]
```

Pattern A fails *silently*: if a single `!remove` misses its target, the inherited gears stay
in front of yours. Pattern B cannot miss, but it only works if every record in the list
exists — so each gear must be defined, not merely renamed.

And the pitfall underneath both: **never base a record on a game-internal `inlineN` record**
(`Vehicle.v_sport1_quadra_turbo_r_inline14`). TweakXL's docs are blunt: inline indices "can
change **without ANY warning** on every single game update". Our gears based themselves on
`_inline10…14`, and gears 4, 5, 6 and 7 all based on the *same* `_inline14`.

## 1.4 The rest of the furniture

* **Audio**: a Wwise bank + an AudioXL entry + a redscript that answers "which sound for
  this car". Usually the engine sound is a copy of an existing vehicle's metadata.
* **Virtual gearbox** (optional): a redscript that computes revs from speed and a gear table
  so the note climbs and the LEDs sweep. This is *cosmetic* — it cannot change physics.
* **Paint**: either baked into materials (needs art), or via a third-party runtime tool
  (Car Manager / CrystalCoat) which needs a one-line compatibility patch, not textures.
* **Localisation**: an onscreens/CR2W `.json` packed into its own archive, referenced by
  `displayName` and `info` LocKeys.

---

# 2. How the game interprets the numbers

## 2.1 The shape of the model

The vehicle sim reads the drive model and the engine and produces, at each tick:

```
wheel force  ≈ torque_curve(rpm) × gearTorqueMultiplier × (something akin to a gear ratio)
acceleration ≈ (wheel force − resistance) / mass
resistance   ≈ airResistanceFactor · v²  +  rolling resistance (grows with downforce)
target rpm   ≈ where v falls inside that gear's [minSpeed, maxSpeed] ↔ [minEngineRPM, maxEngineRPM] map
```

Nothing in that chain is "the top speed". Top speed is where force meets resistance — or
where the engine runs out of curve, whichever comes first. (**inferred**, consistent with
everything we measured.)

## 2.2 Units, and the three lies

| Quantity | Unit | Evidence |
|---|---|---|
| gear `minSpeed` / `maxSpeed` | **m/s** | Quadra's last gear is 58.5 → the game says 211 km/h (**documented**: stock values, **measured**: 58.5 × 3.6 = 211) |
| engine `maxRPM`, gear rpm bands | rpm | — |
| `total_mass` | the drive model's own scale; the scanner card uses lbs | 1750 kg → card reads 3858 lb (**measured** on our car) |
| `airResistanceFactor` | dimensionless scale, **0.35 – 2.45** across five cars | `VEHICLE-COMPARISON.md` |
| `springStiffness` | **not** N/mm | the Quadra author's annotated rant in `reference/Quadra_…yaml` (**documented**) |

Three things people get wrong:

1. **The speedo is not a measurement.** The game displays speed through a
   `speed_to_multiplier` curve that **inflates the number as speed rises** (the comment in
   this mod's own redscript says so). This car's dash bypasses that curve with
   `SpeedValue × 3.6`, so **its numbers are true km/h while every vanilla car's are
   inflated** — which means "the Jesko showed 500" and "the Phoenix showed 350" are not
   comparable quantities. Treat display as *relative*, never absolute, and never compare a
   modded dash with a vanilla one.
2. **`maxSpeed` per gear is not a top speed.** Measured this week: the Zonda does **355 km/h
   on a gear table whose last gear says 180** (1.97×), the Jesko **500+ on 283** (1.77×).
3. **The upshift is at 90 % of a gear's range, and the ladder must contain it.** Every shift
   of ours landed *below* the next gear's floor, so the box grabbed a gear the car was too
   slow for and the engine braked it — the 308 and 352 km/h plateaus. The curve is not a
   ceiling: it is a normalised shape (`x` = rpm 0→1) stretched over `[minRPM, maxRPM]`, so it
   cannot cap rpm at all. (**measured** twice, then **documented** by the file format.)

## 2.3 `torqueMultiplier` is a gear ratio wearing a disguise

It has no physical unit; it scales the engine's torque in that gear. Which is why a gearbox
that looks sane on paper can be undriveable: the *shape* of the ladder (how much each shift
drops rpm, how much speed one gear must cover) matters more than any single number. Ours was
1.80× of speed in one gear on the weakest multiplier — a stack of numbers that cannot pull —
and the car stopped exactly where the last pullable gear ended. (**measured**)

## 2.4 Steering is a three-band filter, not a wheel angle

`maxWheelTurnDeg` is the physical lock; what you *get* at speed is filtered:

```
below turnUpdateBaseSpeedThreshold      full authority
below turnUpdateMidSpeedThreshold       × turnUpdateMidSpeedTurnMul
above turnUpdateMaxSpeedThreshold       × turnUpdateMaxSpeedTurnMul
small inputs vs large inputs            turnUpdateInputDiff… / …FastChangeSpeed / …SlowChangeSpeed
```

Five cars, one pattern: the fast ones cut authority hard above ~45 m/s (to 16–21 %) and hold
it there. Ours cut early and mildly (26 m/s, 33 %) — a third of full lock still being handed
over at 400 km/h. (**documented** fields, **measured** comparison.)

## 2.5 What we learned by measurement, not by reading

| Claim in the wild | What our cars actually did |
|---|---|
| "gear `maxSpeed` is the vehicle's ceiling" (redmodding wiki, corpus index) | false — Zonda 1.97×, Jesko 1.77× past it |
| "there is a native cap around 400" (speed-unlimiter mod) | not in this install — 500+ was reached without it |
| "internal speed unit ≈ 3.87 km/h" (cheat sheet) | inconsistent with 58.5 m/s ↔ 211 km/h; m/s → km/h matched everything |
| **our own** theory: "it stops at ~7 850 / ~8 020 rpm, so the curve ends there" | wrong — a curve is normalised; the 308 and 352 km/h plateaus were shift holes |
| "the wobble is steering authority" | partly: it also needed grip symmetry (all five cars within 6 % front-to-rear; ours was 25 % apart) and rebound damping that isn't 1.72× its bound |

---

# 3. Relation to real physics

## 3.1 What maps honestly

| Game | Real | Notes |
|---|---|---|
| `engineMaxTorque` | peak torque, Nm | but the *scale* is fiction: ours is 3 824, a real LMH is ~700 |
| `total_mass` | mass, kg | our 1750 is a real LMH number |
| `airResistanceFactor` | ½ρC_dA | monotone, not calibrated |
| `maxSpeedFactorGround` | downforce coefficient C_l A | 0.35–0.7 for the fast cars, ours was 1.40 |
| `frictionMulLateral/Longitudinal` | tyre μ, front vs rear | the *split* is what makes a car stable or nervous |
| `springStiffness` / `springDamping` | spring rate / damper rate | uncalibrated; only ratios are meaningful |
| gear `torqueMultiplier` | gear ratio | the only place ratios live, and they are explicit numbers, not a final drive |
| `maxBrakingTorque` | brake torque | proportional-ish |

## 3.2 What does not map, and why that matters

* **There is no final drive and no wheel-force equation you can audit.** You cannot compute
  top speed from power and drag the way you can in reality, because the game never tells you
  the ratio it derived. It only tells you where the gear's rpm map sits.
* **A shift into an out-of-range gear behaves like braking.** Nothing in the data says "these
  two gears overlap"; if the box grabs a gear whose window starts above your speed, the engine
  math lands under its floor, the engine stops making torque, and drag does the rest. It reads
  exactly like a brake fault, which cost us a build.
* **Power is not conserved.** Two cars with the same power can differ by 200 km/h if one has
  a taller top gear or a shorter curve. Our car had 3.8× the torque of the Jesko and went
  60 % as fast. In reality that is impossible; in TweakDB it is just a badly shaped record.
* **The shape of the torque curve lives in a binary asset** (`gearCurvesPath`, a `.curveset`)
  and is chosen by name from 15 vanilla shapes — but it is *normalised*, so it scales to
  whatever `maxRPM` says rather than imposing a ceiling of its own. The un-real part is
  narrower than we first thought: you can say "peaky" or "balanced", you cannot say
  "peak torque at 7 000 rpm" without authoring a curve yourself.

## 3.3 The real-physics reality check for 500 km/h

For a 2 000 hp (1 491 kW) car with an open-wheel-ish C_dA of ~0.95 m² in air at 1.225 kg/m³:

```
drag at 138.89 m/s (500 km/h) = ½ · 1.225 · 0.95 · 138.89²  ≈ 11 200 N
power to hold it             = F · v                       ≈ 1 559 kW  =  2 091 hp
```

So **500 km/h at 2 000 hp is not fantasy — it is right on the edge**, and it needs a C_dA of
about 0.91 m² to work. That is a real LMH-class number, and it is exactly why the car is
"2 000 hp": below ~2 100 hp, 500 km/h stops being a power question and becomes an aero one.
Running the same arithmetic backwards gives the class ceiling: 2 000 hp with C_dA 0.95 tops
out near **493 km/h**.

Where the game matches reality: the *relationships*. Wider gears hurt; more drag hurts;
grip split front-to-rear decides whether the car weaves; dampers that rebound faster than
they compress make a car oscillate. Every one of those behaved the way a real car would.

Where it does not: **absolute values, and causality.** In reality, if you have the power and
the ratios, you get the speed. In this game, if the curve ends at 7 800 rpm, you get what
the curve gives you — no matter what your gearbox, torque figure or drag says.

## 3.4 The practical checklist that falls out of all of it

1. Clone a car whose **class** matches what you want, and write the physics out explicitly.
2. Define gears as **one explicit list**; never base them on `inlineN` records.
3. Build the ladder as **even ratio steps**; every gear's speed window ≈ its rpm band ratio.
   Then check the **overlap**: the next gear must contain the speed at which this one shifts,
   i.e. `minEngineRPM ≤ 0.90 × maxEngineRPM / step`. A gear the car enters too slowly is not
   a slow gear, it is a brake.
4. Finish the top gear at an rpm the **curve** actually reaches — that number, not `maxRPM`,
   is your redline.
5. Keep the axles' lateral grip **within a few percent** of each other.
6. Set rebound damping ≈ **1.25×** bound; large asymmetry is an oscillator.
7. Steering authority above ~45 m/s should be **~20 %**, not 33 %.
8. Change **one subsystem per test**, and test with the AI driving so the input is constant.
