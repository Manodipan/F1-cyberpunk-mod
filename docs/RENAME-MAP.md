# RENAME MAP — `_f1` → `phoenix` (PORT.md §4)

Everything here is applied mechanically by `tools/port_to_phoenix.py`; the table
exists so you can audit the tool and hand-check a diff.

## 1. Renamed

| Kind | From (interim) | To (Phoenix) |
|---|---|---|
| Vehicle record | `Vehicle.xaires_aston_valkyrie_f1` | `Vehicle.phoenix_aston_valkyrie` |
| … purchasable | `Vehicle.xaires_aston_valkyrie_f1_purchasable` | `Vehicle.phoenix_aston_valkyrie_purchasable` |
| … UI data | `Vehicle.xaires_aston_valkyrie_f1_data` | `Vehicle.phoenix_aston_valkyrie_data` |
| … manufacturer | `Vehicle.xaires_aston_valkyrie_f1_manufacturer` | `Vehicle.phoenix_aston_valkyrie_manufacturer` |
| Engine / gears | `Vehicle.xaires_amv_f1_gear` (+ `_inlineN`) | `Vehicle.phoenix_amv_gear` (+ `_inlineN`) |
| Wheels | `Vehicle.xaires_amv_f1_wheel`, `_front`, `_back` | `Vehicle.phoenix_amv_wheel`, `_front`, `_back` |
| Drive model | `Vehicle.xaires_amv_f1_drive` | `Vehicle.phoenix_amv_drive` |
| Drive helpers | `Vehicle.xaires_amv_f1_downforce`, `_rearHelper` | `Vehicle.phoenix_amv_downforce`, `_rearHelper` |
| Icons | `UIIcon.xaires_aston_valkyrie_f1_*` | `UIIcon.phoenix_aston_valkyrie_*` |
| Manufacturer enum | `enumName: xaires_aston_valkyrie_f1_logo` | `enumName: phoenix_aston_valkyrie_logo` |
| Module / classes | `XairesAMVF1_*`, module `XairesAMVF1` | `PhoenixAMV_*`, module `PhoenixAMV` |
| Audio resource | `xaires_amv_engine` | `phoenix_amv_engine` |
| Methods | `VC_DeepCopyAudioMetadata`, `VC_UpdateAMVDash` | `PHX_DeepCopyAudioMetadata`, `PHX_UpdateAMVDash` |
| Gear 7 ceiling | `91.7` (330 km/h) | `138.89` (500 km/h) |
| Folders / files | `r6\scripts\xaires_aston_valkyrie\` `xaires_aston_valkyrie_f1_*.reds` | `r6\scripts\phoenix_aston_valkyrie\` `phoenix_aston_valkyrie_*.reds` |
| Tweak file | `r6\tweaks\xaires\aston_valkyrie.yaml` | `r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml` |
| Archives | `aston_valkyrie.archive` + `.xl` | `phoenix_aston_valkyrie.archive` + `.xl` |

### Why `VC_*` → `PHX_*` when PORT.md §4 doesn't say so

PORT.md §5 installs **both** mods at once ("two separate mods, both enabled").
redscript compiles every mod together and rejects two `@addMethod`/`@wrapMethod`
definitions with the same class + name + signature. Keeping `VC_DeepCopyAudioMetadata`
in both mods is a guaranteed compile error on the next launch — so the Phoenix
build uses a `PHX_` prefix (game-internal, never referenced by the YAML).

If you ever need the old names: `--keep-method-names` (only safe if the stock mod
is uninstalled).

## 2. Kept shared (do **not** rename — same assets, same bank)

| Thing | Value | Why |
|---|---|---|
| Appearance | `appearanceName: aston_valkyrie` | lives in the shared `.ent` |
| Entity template | `xaires\aston_valkyrie\aston_valkyrie.ent` | single backslashes, shared asset |
| Texture core | `xaires\aston_valkyrie\ui\*.inkatlas`, `atlasPartName: *` | inside the unchanged `.archive` |
| Wwise bank | `XairesAMV_Wwise`, `xaires_amv.bnk` | one AudioXL bank for both mods |
| Wwise events / facts | `xamw_*`, `xcm_vol`, `xaires_cm_vol` | baked into the bank |
| Dashboard widgets | `amvGear`, `amvLed`, `amvRev`, `seg_*`, `g_*`, `s_*`, `led_*` | inside the dashboard `.inkwidget` |
| Display LocKeys | `xaires_aston_valkyrie_name`, `xaires_aston_valkyrie_info` | reused until §6 adds `phoenix_*` entries |

## 3. Tool

```bash
# port one file
python3 tools/port_to_phoenix.py --from f1 reference/aston_valkyrie_f1.yaml \
    --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml

# port a folder (file names renamed too)
python3 tools/port_to_phoenix.py --from f1 reference/clone_f1 \
    --out Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie

# port physics as well (fresh start from the stock file)
python3 tools/port_to_phoenix.py --from stock reference/aston_valkyrie_stock.yaml --out /tmp/x.yaml

# audit a tree — exit 1 on any leftover xaires/_f1 identifier or stock physics value
python3 tools/port_to_phoenix.py --check Phoenix_aston_cheats

# port your own stock copy in place (Vortex staging folder, not the game folder)
python3 tools/port_to_phoenix.py --from stock "C:/mods/aston_valkyrie" --in-place
```

`--check` is the gate that replaces eyeballing: it fails on stale `Vehicle.xaires_*`,
`UIIcon.xaires*`, `XairesAMV*`, `xaires_amv_engine`, `VC_*` methods and any stock
physics value that should have moved (e.g. `engineMaxTorque: 1300`).
