# PORT.md — Phoenix_aston_cheats: New Valkyrie Mod (Cyberpunk 2077)

**Date:** 2026-11-24
**Objective:** Build a **brand-new mod** (`Phoenix_aston_cheats`) from the Nexus original — same assets (model, livery, V12 sound, texture core) reused under **new folder/file/ID naming** (`phoenix_*`, `PhoenixAMV*`) so there is **zero chance of duplicates or game-engine confusion** with stock. Forget `xaires` in the new mod. Stock stays pristine on `main`; all Phoenix work on a separate branch/folder.

This replaces the interim `_f1` naming (workspace `aston_valkyrie_f1.yaml` + `clone_f1/*.reds`). Next chat: rename `_f1` → `phoenix` per §4, then install/test.

---

## 1. Repo structure

```
main (Nexus original, unpacked, UNTOUCHED):
  archive/pc/mod/aston_valkyrie.archive + .archive.xl
  r6/scripts/xaires_aston_valkyrie/*.reds (4 files)
  r6/tweaks/xaires/aston_valkyrie.yaml
  red4ext/plugins/AudioXL/sounds/XairesAMV_Wwise/{sounds.json,xaires_amv.bnk}

phoenix branch / Phoenix_aston_cheats folder (NEW MOD):
  archive/pc/mod/phoenix_aston_valkyrie.archive + .archive.xl   (copies, renamed files)
  r6/scripts/phoenix_aston_valkyrie/*.reds                      (cloned scripts, PhoenixAMV*)
  r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml                (F1-cheat physics, phoenix_* IDs)
  red4ext/plugins/AudioXL/...                                   (SHARED stock bank — do not duplicate yet)
```

Workspace deliverables to push: `aston_valkyrie_stock.yaml` (stock reference), `aston_valkyrie_f1.yaml` (interim F1 YAML — rename to phoenix per §4), `clone_f1/*.reds` (interim scripts — rename per §4), this file. `uploads/` = original sources (reference only).

---

## 2. Original mod reference (stock, do not edit on main)

Stock physics: 680 hp, `engineMaxTorque: 1300`, gear7 `91.7` (330 km/h), drag 1.35, front 1.29/1.15, rear 1.33/1.20, helper 0.95, downforce 0.6, sway 11/16, braking 1410/1200, steering 94/26/0.33, springs 23/22 + 2000. RWD, 7-speed, `maxRPM: 10100`. User tested ~310 km/h real.

Shared asset refs (keep pointing at same files in Phoenix — same livery/sound):
`appearanceName: aston_valkyrie`, `entityTemplatePath: xaires\aston_valkyrie\aston_valkyrie.ent` (single backslashes), `player_audio_resource` (→ `phoenix_amv_engine` after rename, same Wwise events), Wwise bank `xaires_amv.bnk`, texture core in `.archive` (`amv_icon/dealer/ui` `.xbm`).

---

## 3. Phoenix F1-cheat physics (v2 stable — current target)

| Parameter | Stock | Phoenix F1 |
|---|---|---|
| Scanner hp / torque | 680 / 1300 | **2000 / 3824** |
| Gear7 ceiling | 91.7 (330) | **138.89 (500)** |
| Drag | 1.35 | **0.90** |
| Front grip | 1.29/1.15 | **1.60/1.50** |
| Rear grip | 1.33/1.20 | **2.00/1.85** |
| Rear helper | 0.95 | **1.45** |
| Downforce | 0.60 | **1.40** |
| Sway F/R | 11/16 | **15/19** |
| Braking F/R | 1410/1200 | **1850/1550** |
| Steering | 94/26/0.33 | **94/26/0.33** (reverted — v1 115/35/0.55 wobbled) |
| Springs/damping | 23/22, 2000 | **30/28, 3000** |

Unchanged: RWD, gears 1–6 values, RPM, mass 1750, inertia, CoM, `turningRollFactor: 0`, tyre size, rotation limiter. Top speed 500 advised (not 600 — RPM stretch + v³ drag). **v2 handling test still pending** (hairpin/top-speed/launch).

---

## 4. Phoenix rename — baby steps (next chat)

**Step 1 — Copy folder:** Copy Nexus mod folder → `Phoenix_aston_cheats`. Leave `main`/original untouched.

**Step 2 — Rename files/folders in copy:**
- `archive\pc\mod\aston_valkyrie.archive` → `phoenix_aston_valkyrie.archive` (+ `.xl` same rename; contents unchanged for same livery)
- `r6\scripts\xaires_aston_valkyrie\` → `phoenix_aston_valkyrie\`
- `r6\tweaks\xaires\aston_valkyrie.yaml` → `r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml`
- Delete `red4ext\plugins\AudioXL\` from copy (share stock bank)

**Step 3 — Rename IDs in text files** (YAML + 4 `.reds`). From current interim `_f1` files:
- `Vehicle.xaires_aston_valkyrie_f1` → `Vehicle.phoenix_aston_valkyrie` (incl. `_purchasable`, `_data`, `_manufacturer`)
- `Vehicle.xaires_amv_f1_gear/wheel` → `Vehicle.phoenix_amv_gear/wheel`
- `UIIcon.xaires_aston_valkyrie_f1_*` → `UIIcon.phoenix_aston_valkyrie_*` (+ `enumName: phoenix_aston_valkyrie_logo`)
- `XairesAMVF1` → `PhoenixAMV` (all classes/functions/service strings)
- `xaires_amv_engine` → `phoenix_amv_engine` (YAML `player_audio_resource` + audio `.reds` `VC_DeepCopyAudioMetadata` + `Equals` checks; Wwise events `xamw_*` stay shared)
- Keep shared: `appearanceName`, `.ent` path, widget paths (`amvGear/Led/Rev`, `seg_*`, `g_*`, `s_*`, `led_*`), `xamw_*`/`xcm_vol`, bank path, `xaires_cm_vol` fact
- Audio-only: `PhoenixAMV_GearSpeed` default `91.7` → `138.89` (match Phoenix gear7)

**Step 4 — Textures:** Reuse original `.archive` texture core as-is. New F1 livery later: AI-generate PNG → Wolvenkit import to `.xbm` → repack `.archive`. No imitation needed — original designs.

**Step 5 — Names:** `displayName`/`info` → `phoenix_aston_valkyrie_name/info` once language entries added (§6). Until then reuse stock LocKey (`xaires_aston_valkyrie_name`).

---

## 5. Install + test

1. Install **both** mods (stock + Phoenix) — merge `archive/`, `r6/`, `red4ext/` into game root. Via Vortex: two separate mods, both enabled. **Never hand-edit game-folder files** (Vortex overwrites). Edit staging/Downloads copies.
2. **Full game restart** after any file add/remove/rename. CET Reload only re-reads already-loaded YAMLs.
3. Call Vehicle: two Valkyries. Footer distinguishes (`..._F1` 2000 hp interim; after rename `phoenix_...` 2000 hp vs stock 680 hp).
4. CET unlock (backup): `Game.GetVehicleSystem():EnablePlayerVehicle("Vehicle.phoenix_aston_valkyrie_purchasable", true, false)` (interim: `..._f1_purchasable`). Stock: `Vehicle.xaires_aston_valkyrie_purchasable`.
5. Test: hairpin flat-out, top speed, 100–200 accel, launch wheelspin. Report speeds/symptoms for v3 tuning.

---

## 6. Localisation — distinct Phoenix name (pending)

Plain-string `displayName` **fails** (summon shows TEST fallback — proven). Names must be valid LocKeys in language files inside `.archive`.

Still needed from user:
1. `aston_valkyrie.archive.xl` contents (small text file, paste as `.txt`).
2. Wolvenkit file list for `.archive` + language file contents (likely `base\languages\en-us.json` with `xaires_aston_valkyrie_name`). Wolvenkit = Windows tool to extract/repackage `.archive` (model/UI/language). Cannot run in sandbox.
3. Then: add `phoenix_aston_valkyrie_name` = "Aston Martin Valkyrie F1 CHEAT" + `_info`, repackage (modify original OR new small lang `.archive` — ArchiveXL merges all), update Phoenix YAML to new LocKeys (match prefix style: displayName no `LocKey#`, info with `LocKey#`).

`.archive` strings search found only `.xbm` UI paths (compressed) — extraction required. Never edit `.archive` binary as text.

---

## 7. Troubleshooting

- One car only / TEST name / duplicate errors: duplicate IDs, duplicate displayName, broken `.ent` path (single backslashes!), old file still in game folder, or Vortex staging overwrite. Full restart + check CET console.
- Scanner LOADING: normal state. hp from YAML, info text from localisation (680 PS mismatch expected until §6).
- Wobble (v1): over-steering + front grip + soft suspension — fixed in v2 (§3). If v2 still wobbles, report speed + front-dart vs rear-step to tune next.

---

## 8. Session log — 2026-11-23 (`arena/fd35b985-f1-cyberpunk-mod`)

The real unpacked mod landed on `main` (3a6d0b1). §4 is now **done against the real
files** and the Phoenix build is complete apart from §6.

Built: `tools/port_to_phoenix.py` (one ordered rule set + `--check` gate + 21 tests),
`Phoenix_aston_cheats/` with the renamed archive + `.xl` (byte-identical copy), the
Phoenix tweak YAML (2000 hp / 3824 Nm / 138.89 m/s) and the four real redscript
files ported verbatim, plus `reference/stock/` as the source of truth.

Reality vs this document (§4):

| §4 said | What the files actually contain |
|---|---|
| `XairesAMVF1` module | no `module` line; free functions `XairesAMV_*` + classes `XairesAMV*` |
| interim `_f1` files | never existed — port is stock → Phoenix directly |
| `VC_DeepCopyAudioMetadata` is the mod's | it is **VehicleCore's** API; renaming it breaks audio (regression test added) |
| steering 94/26/0.33 | `wheelTurnMaxAddPerSecond` 94, `turnUpdateMaxSpeedThreshold` 26 m/s, `turnUpdateMaxSpeedTurnMul` 0.33 |
| rear helper 0.95 | `minLatFrictionCoef` **and** `minLongFrictionCoef` on `RearWheelsFrictionModifier_Exotic` |
| downforce 0.60 | `maxSpeedFactorGround` on `DynamicDownforceHelper_Exotic` (air stays 0) |
| gear 7 = one field | two places: `Vehicle.xaires_amv_gear_7.maxSpeed` **and** the `GearSpeed` default in the audio script |

Still open: §6 (onscreens JSON is inside the archive at
`xaires\aston_valkyrie\aston_valkyrie.json` / `_tr.json` per the real `.xl`), and the
pending v2 handling test. See `docs/STATUS.md`.
