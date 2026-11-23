# RENAME MAP — stock → Phoenix (PORT.md §4)

Applied mechanically by `tools/port_to_phoenix.py` against the real mod on `main`
(TweakXL YAML + 4 redscript files). The table exists so the tool can be audited.

## 1. Renamed — YAML (`reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml`)

| From | To |
|---|---|
| `Vehicle.xaires_aston_valkyrie` | `Vehicle.phoenix_aston_valkyrie` |
| `Vehicle.xaires_aston_valkyrie_data` | `Vehicle.phoenix_aston_valkyrie_data` |
| `Vehicle.xaires_aston_valkyrie_manufacturer` | `Vehicle.phoenix_aston_valkyrie_manufacturer` |
| `Vehicle.xaires_aston_valkyrie_purchasable` (+ `.dealerPrice`, `.dealerCred`, `.dealerAtlasPath`, `.dealerPartName`) | `Vehicle.phoenix_aston_valkyrie_purchasable` (…) |
| `UIIcon.xaires_aston_valkyrie_icon` / `_logo` | `UIIcon.phoenix_aston_valkyrie_icon` / `_logo` |
| `enumName: xaires_aston_valkyrie_logo` | `enumName: phoenix_aston_valkyrie_logo` |
| `Vehicle.xaires_amv_wheel_front` / `_back` (WheelRole) | `Vehicle.phoenix_amv_wheel_front` / `_back` |
| `Vehicle.xaires_amv_gear_r`, `_gear_1` … `_gear_7` | `Vehicle.phoenix_amv_gear_r`, `_gear_1` … `_gear_7` |
| `player_audio_resource: xaires_amv_engine` | `player_audio_resource: phoenix_amv_engine` |
| `Vehicle.vehicle_list.list` entries | append the Phoenix records instead |
| gear 7 `maxSpeed: 91.7` | `maxSpeed: 138.89` |
| `displayName: xaires_aston_valkyrie_name` | `displayName: phoenix_aston_valkyrie_name` |
| `info: LocKey#xaires_aston_valkyrie_info` | `info: LocKey#phoenix_aston_valkyrie_info` |

## 2. Renamed — redscript (`r6/scripts/xaires_aston_valkyrie/*.reds`)

| From | To | Why it matters |
|---|---|---|
| `XairesAMVEngineState` / `XairesAMVInput` / `XairesAMVEngineTick` / `XairesAMVAudioMetadata` / `XairesAMVWwise` | `Phoenix…` | duplicate class names are a compile error when both mods are installed |
| `n"XairesAMVEngineState"` service lookup | `n"PhoenixAMVEngineState"` | must match the class or the service is never found |
| `XairesAMV_IsTarget`, `_GearSpeed`, `_GearboxStep`, `_EngineStartTicker`, `_WwiseSend`, … | `PhoenixAMV_*` | global functions would otherwise collide with the stock mod |
| `t"Vehicle.xaires_aston_valkyrie"` / `…_purchasable"` | `t"Vehicle.phoenix_aston_valkyrie"` / `…_purchasable"` | otherwise the HUD/audio hooks silently keep driving the **stock** car |
| `n"xaires_amv_engine"` (metadata `Equals` check + copy target) | `n"phoenix_amv_engine"` | the record name the YAML points at |
| `XairesAMV_GearSpeed` `default: 91.7` | `default: 138.89` | audio rev ceiling must match gear 7 |
| file names `aston_valkyrie*.reds` | `phoenix_aston_valkyrie*.reds` | |

Everything else in those files (`@wrapMethod` hooks on `hudCarController`,
`speedometerLogicController`, `tachometerLogicController`, `VehicleComponent`) is
left alone — redscript chains wrappers, and each wrapper checks its own car by
TweakDBID.

## 3. Kept shared

| Thing | Value | Why |
|---|---|---|
| Appearance | `appearanceName: aston_valkyrie` | inside the shared `.ent` |
| Entity template | `xaires\aston_valkyrie\aston_valkyrie.ent` | shared asset |
| Textures / UI | `xaires\aston_valkyrie\ui\amv_icon.inkatlas`, `amv_dealer.inkatlas`, `aston_valkyrie_logo.inkatlas`, `atlasPartName` | inside the unchanged `.archive` |
| `dealerAtlasPath` / `dealerPartName` | `"xaires\\aston_valkyrie\\ui\\amv_dealer.inkatlas"` / `"amv_full"` | same archive UI |
| Wwise bank | `XairesAMV_Wwise` folder, `xaires_amv.bnk` | **one** AudioXL bank for both mods |
| Wwise events / params | `xamw_engine_on/off`, `xamw_rpm`, `xamw_gas`, `xcm_vol`, fact `xaires_cm_vol` | baked into the bank |
| Widget paths | `amvGear`, `amvGearImg`, `amvLed`, `amvRev`, `seg_*`, `g_*`, `s_*`, `led_*`, `amvSpd*` | inside the dashboard `.inkwidget` |
| **`VC_DeepCopyAudioMetadata`** | unchanged | it is a **VehicleCore** API (`import VehicleCore.*`), not the mod's own method. Renaming it breaks the audio metadata copy — an early draft of the tool did exactly that and it is now a regression test |

## 4. Tool

```bash
make port     # regenerate Phoenix_aston_cheats/r6 from reference/stock
make check    # identifiers + stock physics + script↔YAML reference consistency
make test     # 37 tests, incl. "committed tree == tool output"

# port your own staging copy in place (never the game folder — Vortex overwrites)
python3 tools/port_to_phoenix.py --from stock "C:/mods/aston_valkyrie" --in-place
```

`--check` fails on:

* any `xaires` / `_f1` identifier left **in code** (comments are exempt — the
  Turkish engineering notes and the credit to xaires are provenance);
* any stock physics value that should have moved (`engineMaxTorque: 1300`, …);
* a `t"Vehicle.phoenix_*"` literal with no matching record in the YAML;
* a `player_audio_resource` that no script creates, or a metadata record no YAML uses;
* a `xaires` path in the `.xl` (it registers the Phoenix onscreens file, not the stock one).
