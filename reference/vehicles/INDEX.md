# Vehicle reference index

Generated 2026-11-25 by `tools/collect_vehicles.py` — do not hand-edit.
2 vehicle tweak(s), sorted by top gear.

`km/h` and `m/s` come from the **last gear's `maxSpeed`**, which is what the game
uses as the vehicle's ceiling. `drag` is `airResistanceFactor`, `steer` is
`wheelTurnMaxAddPerSecond` / `turnUpdateMaxSpeedTurnMul` (authority above
`turnUpdateMaxSpeedThreshold`).

| km/h | m/s | gears | drag | torque | mass | steer | mul | records | file |
|---|---|---|---|---|---|---|---|---|---|
| 283 | 78.5 | 8 | 0.66 | 1000 | 1800 | 137 | 0.21 | v_sport1_koenigsegg_jesko_attack_player | `jesko_attack.yaml` |
| 180 | 50 | 7 | - | 520 | 1280 | 100 | - | zonda_revo | `zonda_revo.yaml` |
