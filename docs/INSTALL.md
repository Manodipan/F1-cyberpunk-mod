# Install + test — Phoenix_aston_cheats

Target: stock Valkyrie **and** Phoenix installed side by side, one car each,
2000 hp vs 680 hp in the scanner footer (PORT.md §5).

## 0. Before you start

* Requirements (unchanged from the stock mod): Cyber Engine Tweaks, redscript,
  TweakXL, ArchiveXL, AudioXL, plus the game version the stock mod targets.
* The two binary archives must be copied and renamed first —
  `Phoenix_aston_cheats/archive/pc/mod/README-COPY-ARCHIVE.md`.
* Work on the **Vortex staging / Downloads copy**, never inside the game folder
  (PORT.md §5.1). Also see `docs/STATUS.md` for the items that still need your
  Windows machine (script bodies, LocKeys) before this is a finished build.

## 1. What gets installed where

```
<game>/archive/pc/mod/phoenix_aston_valkyrie.archive       <- copied + renamed
<game>/archive/pc/mod/phoenix_aston_valkyrie.archive.xl    <- copied + renamed
<game>/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml       <- generated, 2000 hp
<game>/r6/scripts/phoenix_aston_valkyrie/phoenix_*.reds    <- generated, 4 files
```

`red4ext/` is intentionally absent — the Phoenix build shares the stock AudioXL
bank. Two copies of `xaires_amv.bnk` is a duplicate-load bug, not a feature.

## 2. Install

1. Vortex: two separate mods — the stock Valkyrie (Nexus) and
   `Phoenix_aston_cheats` — **both enabled**.
2. Deploy.
3. **Full game restart.** Not a reload: CET "Reload" only re-reads YAMLs already
   loaded at boot, so file adds/renames need a fresh process (PORT.md §5.2).

## 3. Summon

* In game: the vehicle list / dealer should show **two** Valkyries. The footer
  tells them apart by hp — `2000` (Phoenix) vs `680` (stock) — until §6 gives
  Phoenix its own name LocKey.
* Unlock fallback (CET console):

```lua
Game.GetVehicleSystem():EnablePlayerVehicle("Vehicle.phoenix_aston_valkyrie_purchasable", true, false)
```

* Stock reference: `Vehicle.xaires_aston_valkyrie_purchasable`.
* Everything working = spawn, scanner shows `2000` hp, V12 audio present, gear
  display tracking.

## 4. Test matrix (PORT.md §3: v2 handling test is still pending)

| # | Test | How | Pass looks like | Record |
|---|---|---|---|---|
| 1 | Top speed | Airport straight / long highway, hold full throttle | ~500 km/h indicated before drag wall; no tacho bounce | km/h |
| 2 | 100→200 km/h | rolling pull, note time | noticeably quicker than stock, no wheelspin | seconds |
| 3 | Launch | standstill, full throttle | forward bite; some spin is fine, no instant 180° | ok / spins |
| 4 | Hairpin flat-out | any tight corner at 60–90 km/h | front bites, rear stays planted; **no wobble** (that was v1) | ok / darts / steps |
| 5 | Braking | 200→0 | straight line, no yaw | metres |
| 6 | Shifting | 1→7 | shifts land inside the powerband, gear 7 pulls to the ceiling | ok / bog |
| 7 | Audio | windows down / cockpit | pitch climbs to ~138.89 ceiling, no cut-out at 330 km/h | ok / cuts |

Report the numbers plus one line per failure ("darts left on turn-in above
120 km/h", "rear steps out on 3rd→4th at full throttle"), which is what v3 tuning
needs. If the car does something odd but the scanner/mass/hp look right, suspect
the `Medium`/`Low` field mappings in `docs/YAML-FIELDS.md` first.

## 5. Uninstall / rollback

Disable the `Phoenix_aston_cheats` mod in Vortex and restart. Stock files were
never touched, so nothing else changes. The Phoenix saves are unaffected (the
vehicle record is only removed from the list).

## 6. Symptom → cause (PORT.md §7)

| Symptom | Most likely cause |
|---|---|
| Only one Valkyrie | duplicate IDs, or Phoenix YAML not loaded — check CET console for YAML errors |
| Name shows `TEST` | invalid LocKey (a plain string instead of a LocKey) |
| Duplicate-ID errors in log | leftovers from an older copy, `_f1` files still present, or Vortex staging overwrite |
| Car loads but invisible / no sound | broken `entityTemplatePath` (needs single backslashes) or missing AudioXL bank |
| redscript compile error about `PHX_*`/`VC_*` | `--keep-method-names` was used while the stock mod is also installed |
| Scanner shows `LOADING` forever | normal transient; hp comes from YAML, info text from localisation (§6) |
