# YAML field map — PORT.md §3 → the real TweakDB fields

Now that the stock file is in the repo (`reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml`),
every row below is confirmed against the actual record tree instead of guessed.
For what each of these fields *does* — the drive model, the steering bands, how the
gearbox and speed units work — see [`VEHICLE-MODEL.md`](VEHICLE-MODEL.md).

| PORT.md §3 | Stock | Phoenix | Where in the stock YAML | Confidence |
|---|---|---|---|---|
| Scanner hp | 680 | 2000 | `VehicleUIData.horsepower` (`_data` record) | Confirmed |
| Engine torque | 1300 | 3824 | `vehEngineData.engineMaxTorque` (`$base: VehicleEngineData_4_SuperSport`) | Confirmed |
| Redline | 10100 | 10100 | `vehEngineData.maxRPM` (unchanged) | Confirmed |
| Gearbox ladder | 7 gears, top 91.7 | 7 gears, **even 1.28× steps**, top 138.89 | per-gear `minSpeed`/`maxSpeed`/`torqueMultiplier`/`min|maxEngineRPM` in `Vehicle.xaires_amv_gear_1…7` **and** `XairesAMV_GearSpeed` in `aston_valkyrie_audio.reds` | Confirmed — the window is the ratio, and both places must move together (see `VEHICLE-MODEL.md` §4.3) |
| Drag | 1.35 | 0.60 | `vehDriveModelData.airResistanceFactor` (911 base record was 1.93) | Confirmed |
| Front grip | 1.29 / 1.15 | 1.60 / 1.50 | `wheelSetup.frontPreset.frictionMulLateral` / `.frictionMulLongitudinal` | Confirmed |
| Rear grip | 1.33 / 1.20 | 1.70 / 1.68 | `wheelSetup.backPreset.…` | Confirmed |
| Rear helper | 0.95 | 1.45 | `driveHelpers` → `RearWheelsFrictionModifier_Exotic.minLatFrictionCoef` **and** `.minLongFrictionCoef` (both 0.95) | Confirmed |
| Downforce | 0.60 | 0.70 | `driveHelpers` → `DynamicDownforceHelper_Exotic.maxSpeedFactorGround` (`maxSpeedFactorAir: 0` stays) | Confirmed |
| Sway F/R | 11 / 16 | 15 / 19 | `frontPreset` / `backPreset` `swaybarStiffness` | Confirmed |
| Braking F/R | 1410 / 1200 | 1850 / 1550 | `frontPreset` / `backPreset` `maxBrakingTorque` | Confirmed |
| Steering | 94 / 26 / 0.33 | 94 / **150** / **45** / **0.21** | `wheelTurnMaxAddPerSecond` / `wheelTurnMaxSubPerSecond` (added) / `turnUpdateMaxSpeedThreshold` / `turnUpdateMaxSpeedTurnMul` (source note: "86 derece/s, 24 m/s üstü %29") | Confirmed — "45" is a speed threshold in m/s, **not** the steering return rate; the pair now matches the 572 km/h reference car |
| Springs F/R | 23 / 22 | 30 / 28 | `springStiffness` | Confirmed |
| Damping | 2000 | 3000 | `springDamping`, plus `springReboundDamping` 3750/3900 and `…LowRate` 3600/3600 — the stock rebound pair was 5000 front vs 2900 rear against the same 2900 bound | Confirmed |
| Mass | 1750 | 1750 | `total_mass`, `chassis_mass` | Confirmed |
| Roll factor | 0 | 0 | `turningRollFactor` | Confirmed |
| Tyres | model | model | `vehWheelDimensionsSetup` (0.392 m radius, 0.341 / 0.374 width) | Untouched |

## What the stock file corrected in the plan

* **Gears are separate records.** `Vehicle.xaires_amv_gear_r`, `_1` … `_7`, each
  `$base`d on a Quadra engine inline record with its own `torqueMultiplier`,
  `minSpeed`, `maxSpeed`, `minEngineRPM`, `maxEngineRPM`. They are attached with
  `!remove` of the SuperSport inlines + `!append` of ours. Only gear 7 moves.
* **Wheel roles vs presets.** `Vehicle.xaires_amv_wheel_front/_back` are
  `VehicleWheelRole` records (`isDrive` / `isHandBrake` / `isMainBrake`), not wheel
  presets; the presets are inline under `wheelSetup` with a 911 base.
* **`player_audio_resource`** is real (AudioXL + VehicleCore), and the reds side
  creates that metadata record.
* **Steering triplet** is `wheelTurnMaxAddPerSecond` + `turnUpdateMaxSpeedThreshold`
  + `turnUpdateMaxSpeedTurnMul`, not `wheelTurnMaxSubPerSecond`.
* **Nothing is guessed any more.** `docs/YAML-FIELDS.md` used to carry Medium/Low
  confidence rows; the remaining unknown is gameplay behaviour, not field mapping.

## The gear ladder is rebuilt, not just gear 7 (2026-11-24)

Gears 1–6 used to stay as the stock file had them, which put 277 → 500 km/h inside a
single 1.80× overdrive while 6th still ended at 290 km/h. Now every forward gear comes
from `PHOENIX_GEARBOX` in `tools/port_to_phoenix.py`: 1.28× steps, 115 / 147 / 188 / 240 /
306 / 391 / 500 km/h, top window 101 → 138.89 m/s. If the car bogs at a shift, move that
gear's `minSpeed`, not the physics table.

Also note the virtual audio gearbox (`XairesAMV_GearboxStep`) ups at
`4800 + 4900·gas^1.6` rpm using `v · 9900 / GearSpeed(gear)`; at 138.89 m/s in 7th
that is ~7 130 "virtual rpm", i.e. the note climbs more slowly near the top — that
is expected, not a bug.
