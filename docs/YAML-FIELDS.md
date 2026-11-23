# YAML field map — PORT.md §3 → TweakDB

Every physics row from the port notes, the field the Phoenix YAML writes, and how
sure that mapping is. **Confidence is the point of this table:** `High` rows are
documented TweakDB fields; `Medium`/`Low` rows must be confirmed in WolvenKit's
Tweak Browser against the stock file before an in-game test means anything.

| PORT.md §3 | Stock | Phoenix | Record | Field | Confidence |
|---|---|---|---|---|---|
| Scanner hp | 680 | 2000 | `VehicleUIData` | `horsepower` | High |
| Engine torque | 1300 | 3824 | `gamedataVehicleEngineData_Record` | `engineMaxTorque` | High |
| Redline | 10100 | 10100 | `gamedataVehicleEngineData_Record` | `maxRPM` | High |
| Gear 7 ceiling | 91.7 | 138.89 | gear record (inline 6) | `maxSpeed` | Medium — engine gear records are 0-indexed (`_inline0` = reverse?) |
| Drag | 1.35 | 0.90 | `gamedataVehicleDriveModelData_Record` | `airResistanceFactor` | Medium |
| Front grip | 1.29 / 1.15 | 1.60 / 1.50 | wheel preset (front) | `frictionMulLateral` / `frictionMulLongitudinal` | High |
| Rear grip | 1.33 / 1.20 | 2.00 / 1.85 | wheel preset (back) | `frictionMulLateral` / `frictionMulLongitudinal` | High |
| Rear helper | 0.95 | 1.45 | `gamedataRearWheelsFrictionModifier_Record` | `multiplier` | Low — field name + helper inline index |
| Downforce | 0.60 | 1.40 | `gamedataDynamicDownforceHelper_Record` | `downforceFactor` | Low — field name |
| Sway F/R | 11 / 16 | 15 / 19 | wheel preset | `swaybarStiffness` | High |
| Braking F/R | 1410 / 1200 | 1850 / 1550 | wheel preset | `maxBrakingTorque` | High |
| Steering in / return | 94 / 26 | 94 / 26 | `gamedataVehicleDriveModelData_Record` | `wheelTurnMaxAddPerSecond` / `wheelTurnMaxSubPerSecond` | Medium |
| Steering `0.33` | 0.33 | 0.33 | — | not modelled | Low — unknown field; unchanged anyway, so the base record keeps it |
| Springs F/R | 23 / 22 | 30 / 28 | wheel preset | `springStiffness` | High |
| Damping | 2000 | 3000 | wheel preset | `springDamping` | Medium — could be `springReboundDamping` / `...LowRate` |
| Mass | 1750 | 1750 | `gamedataVehicleDriveModelData_Record` | `total_mass` | High |
| Roll factor | 0 | 0 | `gamedataVehicleDriveModelData_Record` | `turningRollFactor` | High |

Other assumptions baked into the YAML (all marked `VERIFY` inline):

* **Donor record** `Vehicle.v_sport1_rayfield_caliburn_player` /
  `..._purchasable` — the stock mod's `$base`. Any 4-wheel player car record works;
  it only supplies the fields the mod does not override.
* **Wheel setup** `Vehicle.VehicleWheelDrivingSetup_4_RWD` — RWD roles; confirm the
  record name in the Tweak Browser.
* **Wheel preset base** `Vehicle.VehicleWheelDrivingPreset_Default`.
* **Engine base** `Vehicle.VehicleEngineData_4_SuperSport` — supplies gears 1–6,
  `gearChangeTime`, `gears` array, `gearCurvesPath` unchanged, per §3.
* **Drive helpers** `Vehicle.VehicleDriveModelDataDefault_4w_inline1` (downforce) and
  `..._inline4` (rear friction); inline numbering follows the stock file's
  `driveHelpers` order and must be confirmed.
* **`player_audio_resource`** — taken verbatim from the port notes; if TweakXL
  rejects it, the stock mod's own vehicle record shows the field name it really uses.

## How to confirm in one pass

1. Open the game's Tweak Browser in WolvenKit.
2. Search `Vehicle.xaires_aston_valkyrie` (stock mod) and right-click → create a
   TweakXL override. That file is the ground truth for every `$base`, inline index
   and field name above.
3. Diff it against `reference/aston_valkyrie_stock.yaml`; fix this repo, then
   `python3 tools/port_to_phoenix.py --from stock … --out …` to regenerate.

Nothing in the pipeline depends on my guesses being right — the port tool is
value/key driven, so correcting a field name in the reference file propagates.

## Numeric style

Floats are written as plain numbers (`1985`, `1.60`, `138.89`) — TweakXL casts YAML
numbers to the record's flat type, so `2000` and `2000.0` are equivalent. If your
TweakXL build is strict about a specific field, add the `.0` in the reference file
and re-run the port; the tool never reformats numbers it does not change.
