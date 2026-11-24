# How a vehicle actually works in Cyberpunk 2077

Written 2026-11-24, after a night of chasing a 330 km/h plateau. This is the model behind
the numbers in `docs/YAML-FIELDS.md`: which record owns what, what the units really are,
what limits top speed (and what only looks like it does), and the field to change when the
car wobbles at 400 instead of tracking straight.

Sources are listed at the end; where the community disagrees with itself, this page says so
instead of picking a winner.

---

## 1. The record tree — one car is a dozen records

A vehicle is a `gamedataVehicle_Record` named `Vehicle.<something>`, and almost every field
points at *another record*:

```yaml
Vehicle.phoenix_aston_valkyrie:
  $base: Vehicle.v_sport2_porsche_911turbo      # inherit a whole vanilla car, then override
  entityTemplatePath: …\aston_valkyrie.ent      # the .ent: meshes, components, appearances
  appearanceName: aston_valkyrie                # which appearance inside that .ent
  vehDriveModelData: { … }                      # mass, grip, steering, suspension, drag
  vehEngineData:    { … }                       # torque, RPM, gears
  vehWheelDimensionsSetup: { … }                # tyre radius/width — also the visual wheels
  vehDataPackage, vehDefaultState, vehAirControl, vehSeatSet, vehImpactTraffic, …
  vehicleUIData: Vehicle.<x>_data               # card: year, hp, mass, info text
  manufacturer, icon, displayName, dealerPrice  # presentation + shop
```

Key consequence: **`$base` + a partial override is a layering trick, not a reset.** If you
override `vehEngineData` but leave `gears:` as `!append`, everything the base record had is
still there underneath. This is exactly how our car ended up driving the gearbox it
inherited (see §5).

TweakXL operators, all of which appear in real car mods:

| Operator | Meaning |
|---|---|
| `$base: X` | derive from record X, keep every field not redefined |
| `- !append Y` | add Y to the end of an array (gears, driveHelpers, vehicle_list) |
| `- !remove Y` | delete Y from an array — **fails silently if Y does not exist** |
| `NewRecord: { … }` | define a new named record you can reference |

## 2. The drive model — `gamedataVehicleDriveModelData_Record`

The physics block. What the fields we actually use do:

| Field | Effect |
|---|---|
| `total_mass`, `chassis_mass` | mass (kg on this mod's cars) — scales everything inertial |
| `momentOfInertia`, `momentOfInertiaScale` | resistance to yaw/roll/pitch; too low = nervous, too high = barge |
| `center_of_mass_offset` | weight distribution; z is the important one for kerbs/ramps |
| `airResistanceFactor` | **the drag wall**. Top speed is wherever engine force meets this |
| `turningRollFactor` | artificial body roll while steering; `0` = none |
| `maxWheelTurnDeg` | maximum steering angle at the wheel |
| `wheelSetup.LF/RF/LB/RB` | `VehicleWheelRole` records: which wheel drives / brakes / handbrakes |
| `wheelSetup.frontPreset` / `backPreset` | per-axle grip, brakes, springs, dampers, anti-roll |
| `driveHelpers[]` | a bag of modifiers, each its own record (§2b) |
| `useAlternativeTurnUpdate` | switches on the three-band steering model (§3) |

### 2a. Per-axle preset (`gamedataVehicleWheelDrivingPreset_Record`)

| Field | Effect |
|---|---|
| `frictionMulLateral` / `frictionMulLongitudinal` | tyre grip across / along the car. Front vs rear difference is what decides understeer vs oversteer |
| `maxBrakingTorque` | braking force at that axle |
| `springStiffness`, `springDamping`, `springReboundDamping` | suspension; damping too low = the car floats and oscillates after a bump |
| `swaybarStiffness`, `swaybarLengthScalar`, `swaybarDisplacementLimit` | anti-roll bar: how much load moves across the axle |
| `tireRollingResistanceCoef`, `tireFrictionCoef` | rolling drag and base grip |
| `wheelsVerticalOffset`, `visualSuspension*` | how the car sits and looks |
| `slipAngleCurveScale`, `slipRatioCurveScale`, `slipAngleMinSpeedThreshold` | how abruptly grip lets go at the limit |

### 2b. The drive helpers worth knowing

| Helper | Field | Effect |
|---|---|---|
| `DynamicDownforceHelper` | `maxSpeedFactorGround` | how hard the car is pushed into the road at speed — free cornering grip. `0.6` stock, `1.40` on our car, `0.7` on the 572 km/h reference |
| `RotationLimiter` | `maxAngularSpeedRad`, `driftLimit` | hard cap on yaw rate; also the drift thresholds |
| `RearWheelsFrictionModifier` | `minLatFrictionCoef` / `minLongFrictionCoef` | how much the rear tyres are *allowed* to slide — the difference between planted and snappy |
| `InAirGravityModifier` | `baseAddedGravity`, `driveSpeedAddedGravity` | how eagerly the car comes back down |
| `HandbrakeFrictionModifier` | `rearWheelsLatFrictionCoef`, `postHandbrakeTractionBoost` | handbrake behaviour |
| `DriveWheelsAccelerateNoise` | `accelerationBoost` | fake extra shove at low speed |
| `UphillDriveHelper` | `slopeCompensationFactor` | torque added on gradients |

## 3. Steering is a three-band, speed-dependent model

This is the part that decides whether a 500 km/h car is driveable, and it is *not* one
number. `wheelTurnMaxAddPerSecond` is only the rate at which the wheels can turn; what you
get at speed is filtered through bands:

| Field | Meaning |
|---|---|
| `wheelTurnMaxAddPerSecond` | how fast the wheels can turn **away** from centre |
| `wheelTurnMaxSubPerSecond` | how fast they return to centre |
| `turnUpdateBaseSpeedThreshold` | below this (m/s), full authority |
| `turnUpdateMidSpeedThreshold` + `turnUpdateMidSpeedTurnMul` | middle band: authority multiplier |
| `turnUpdateMaxSpeedThreshold` + `turnUpdateMaxSpeedTurnMul` | top band: authority multiplier |
| `turnUpdateMaxSpeedTurnChangeMul` | how strongly a *change* of input is scaled in the top band |
| `turnUpdateInputDiffForFastChange` / `…ForSlowChange` | the input-difference thresholds that separate "small nudge" from "full lock" |
| `turnUpdateInputFastChangeSpeed` / `…SlowChangeSpeed` | how fast each kind of input is applied |

That last pair is the wobble knob: at speed, a *small* steering input is amplified by
`turnUpdateInputSlowChangeSpeed` while a large one takes the fast path. Cars that feel
twitchy under fingertip corrections at 400+ have the slow path too aggressive — which is
what "slight nudges make it wobble" describes.

Our values versus the 572 km/h reference car:

| | Phoenix | Jesko reference |
|---|---|---|
| `wheelTurnMaxAddPerSecond` | 94 | 137 |
| `turnUpdateMaxSpeedThreshold` (m/s) | 26 | **45** |
| `turnUpdateMaxSpeedTurnMul` | 0.33 | **0.21** |
| `turningRollFactor` | 0 | 1 |
| `driftLimit` | 1.6 | 2.3 |

The reference lets the car steer almost fully up to 162 km/h and then cuts hard to 21 %.
Ours cuts earlier (94 km/h) but less (33 %) — so at 400+ we are still handing the tyres a
third of full authority.

## 4. The engine and the gearbox

`gamedataVehicleEngineData_Record`:

| Field | Meaning |
|---|---|
| `engineMaxTorque` | peak torque — the single biggest lever on acceleration |
| `maxRPM` / `minRPM` | rev range the transmission works inside |
| `gearCurvesPath` | the **torque curve** (a `.curveset`): torque as a function of RPM. Inherited from the base engine unless you change it |
| `gears[]` | the gear list — see below |
| `gearChangeTime`, `gearChangeCooldown` | shift duration and lockout |
| `flyWheelMomentOfInertia` | how lazily revs build/fall |
| `finalGearTorqueDecimationScalor` | how much torque the *last* gear gives up |
| `wheelsResistanceRatio`, `resistanceTorque` | drivetrain losses |

`gamedataVehicleGearRecord` (per gear):

| Field | Meaning |
|---|---|
| `minSpeed` / `maxSpeed` | the speed window that *belongs* to that gear (m/s) |
| `minEngineRPM` / `maxEngineRPM` | RPM window used in that gear |
| `torqueMultiplier` | how hard the engine pulls **through** that window |

Two things the community keeps relearning:

1. **`maxSpeed` is a shift point, not a speed cap.** A car whose last gear says 78.5 m/s
   can still do 572 km/h (`reference/vehicles/jesko_attack`). The gear defines where the
   transmission thinks the gear ends; the actual top speed is an equilibrium between engine
   force and drag.
2. **The gear list is what the gearbox is.** If you build the list wrong — inherited gears
   still in front of yours because an `!remove` missed — the car drives the gearbox it
   inherited, and every other number in your file is wasted.

## 5. Speed: units, the HUD, and the limiter

Three claims circulate; all three matter:

**(a) Internal units are metres per second.** Gear and drive-model speed values are m/s,
`1 m/s = 3.6 km/h`. This is what current vehicle-tuning work states outright and it is what
the numbers look like (`maxSpeed: 138.89` for a 500 km/h target).

**(b) The HUD is not a calibrated instrument.** The speedometer shows an inflated number —
the older wiki measured displayed mph as roughly double the real mph, and puts the engine's
"speed unit" at ≈2.4 mph (≈3.87 km/h). Whether the inflation is exactly ×2, applied only in
mph mode, or varies by vehicle, nobody has pinned down.

**(c) There is a separate hard speed limiter in the engine.** Independent of any TweakDB
value, the game clamps vehicle speed; a RED4ext mod exists purely to remove it
(*Vehicle Speed Unlimiter*, mid-2025, "allowing speeds above ~400"). If you tune a car past
that ceiling and nothing happens, this is why — not your YAML.

Practical rule for us: **trust relative changes, not absolute numbers.** If the plateau
moves when we change a value, that value is the limit. If it does not move, it isn't —
including the case where the limiter in (c) is the thing holding it.

## 6. What actually happened to our car (2026-11-24)

| Observation | What it rules in / out |
|---|---|
| Stock Valkyrie: gear 7 `maxSpeed 91.7`, car reads ~330 | the numbers line up at ×3.6, i.e. m/s → km/h |
| Phoenix with gear 7 `138.89`: still ~330 | our gear values were not in play, *or* a non-gear limit |
| Same plateau with 2.9× the torque of stock | not a power limit |
| Reference car reaching 572 with a 78.5 m/s top gear | `maxSpeed` is not a cap, so "330 = the gear ceiling" was the wrong conclusion |
| The reference builds its gearbox as one explicit list; ours inherited SuperSport gears and did `8 × !remove` + `8 × !append` | the fragile half of our file |

Fixes applied, in order: the explicit gear list (shipped — `tools/port_to_phoenix.py`
`explicit_gears()` builds the array, `tests/test_port.py` keeps it that way), then the drag
(`tools/stability-tweak.ps1 -Drag`), and the limiter question if it still will not move.
`docs/TOPSPEED-TEST.md` keeps the test protocol.

## 7. Tuning playbook

**Top speed is set by:** last gear `maxSpeed` (window) → `torqueMultiplier` and
`engineMaxTorque` (force) → `airResistanceFactor` (drag) → the engine limiter (§5c).
Change one per restart, or you learn nothing.

**Wobble at speed is set by:** the §3 bands, in this order of usefulness —
`turnUpdateMaxSpeedTurnMul` (how much authority survives), `turnUpdateMaxSpeedThreshold`
(where it starts being cut), `wheelTurnMaxAddPerSecond` (how fast it gets there), and the
`turnUpdateInput*` pair (how a small correction is interpreted).

**Do not touch** mass, inertia or `center_of_mass_offset` while chasing speed — they change
how the car *feels* under braking and in air, and the effect is not local.

**Never trust an `!append`-based gear list.** One missed `!remove` and the car is a
different car. Write the list explicitly.

## 8. Sources

* **Cheat Sheet: Vehicle Properties** (CDPR-Modding-Documentation, GitHub) — per-field tables
  for the drive model, engine, gear, downforce, rotation limiter, wheel presets; also the
  speed-unit and speed-limiter notes:
  <https://github.com/CDPR-Modding-Documentation/Cyberpunk-Modding-Docs/blob/main/for-mod-creators-theory/references-lists-and-overviews/vehicles/vehicle-drive-model-data-record.md>
* **Cheat Sheet: Vehicle Root Record** — the full `Vehicle_Record` field list:
  <https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/vehicles/vehicle-record>
* **Changing Handling & Speed For Modded Vehicles** (redmodding wiki) — the `$base` /
  `!remove` / `!append` gear pattern, and the `minSpeed` / `maxSpeed` / `torqueMultiplier`
  explanation. Its author explicitly says the explanations are trial-and-error:
  <https://wiki.redmodding.org/cyberpunk-2077-modding/modding-guides/vehicles/changing-handling-and-speed-for-modded-vehicles>
* **Ultimate Vehicle Tuning** (Nexus 34367) — states internal speed values are m/s, warns
  gear behaviour is "highly interconnected and is not a simple hard speed cap", and exposes
  exactly these fields in a UI:
  <https://www.nexusmods.com/cyberpunk2077/mods/34367>
* **Vehicle Speed Unlimiter** (Jack Humbert, June 2025) — the engine-level speed limit,
  reported by RPS as "the automatic limits the game puts on car movement speed … the ones
  you'd bang your head against even if you modded or file tweaked a car to go beyond its
  base top speed value":
  <https://www.rockpapershotgun.com/cyberpunk-2077s-flying-car-modder-has-removed-the-games-max-speed-limit-and-i-may-soon-be-involved-in-a-1222mph-mid-air-fender-bender>
