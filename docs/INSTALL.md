# Install + test — Phoenix_aston_cheats


> **Updating an existing install?** Don't work through this page again —
> run [`UPDATE.md`](UPDATE.md)'s one command, which pulls, copies and verifies.

Target: stock Valkyrie **and** Phoenix installed side by side, one car each,
2000 hp vs 680 hp in the scanner footer (PORT.md §5).

## 0. Requires

Cyber Engine Tweaks, redscript, TweakXL, ArchiveXL, AudioXL, VehicleCore — the
same set the stock mod needs. The Phoenix scripts `@if(ModuleExists(...))` on
AudioXL/VehicleCore exactly like stock, so a missing one degrades the same way
(no engine audio) instead of failing to compile.

## 1. Contents

```
Phoenix_aston_cheats/archive/pc/mod/phoenix_aston_valkyrie.archive(.xl)
Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie/phoenix_aston_valkyrie{,_audio,_ekran,_led}.reds
```

That folder is a **mirror of the game root** — 7 files, nothing else — so the zip
from `make package` installs by extraction/overlay. `red4ext/` is absent on purpose:
the Phoenix scripts load the stock bank
(`AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk`), so the stock mod must stay
installed. Layout rules and the validator: `docs/PACKAGING.md`.

## 2. Install

1. Vortex: two separate mods — the Nexus Valkyrie (stock) and `Phoenix_aston_cheats`
   — **both enabled**, deploy.
2. **Full game restart**, not a CET reload: file adds/renames are read at boot.
3. Never hand-edit files in the game folder; Vortex overwrites them.

## 3. Summon

Two Valkyries in the dealer/list. Until §6 adds the Phoenix LocKey both are named
"Aston Martin Valkyrie LMH" — the footer's hp separates them (**2000** = Phoenix,
680 = stock), and so does the dealer price if you change it.

CET fallback:

```lua
Game.GetVehicleSystem():EnablePlayerVehicle("Vehicle.phoenix_aston_valkyrie_purchasable", true, false)
```

Stock for comparison: `Vehicle.xaires_aston_valkyrie_purchasable`.

## 4. Test matrix (PORT.md §3 — v2 handling test still pending)

| # | Test | How | Pass | Note |
|---|---|---|---|---|
| 1 | Top speed | long straight, full throttle in 7th — or hands-off via **Auto Drive Enhanced** ([`TOPSPEED-TEST.md`](TOPSPEED-TEST.md)) | ~500 km/h before the drag wall | 138.89 m/s ceiling |
| 2 | 100→200 km/h | rolling pull | clearly quicker than stock, no spin | |
| 3 | Launch | standstill, full throttle | forward bite, no instant spin-out | rear helper 1.45 |
| 4 | Hairpin flat-out | tight corner 60–90 km/h | front bites, rear planted, **no wobble** (that was v1) | front 1.60/1.50, rear 2.00/1.85, sway 15/19 |
| 5 | Braking 200→0 | straight line | no yaw, short | 1850/1550 |
| 6 | 6→7 shift | hold full throttle | does not bog; pulls to the ceiling | gear 7 is a long overdrive by design |
| 7 | Audio / dash | cockpit | rev note climbs to the new ceiling, LEDs/dash follow, no cut-out | audio ceiling = 138.89 |

Report numbers + one line per failure ("darts left on turn-in above 120 km/h",
"rear steps out on 3→4 at full throttle") — that is what v3 tuning needs.

## 5. Logs to check on the first launch

| Log | Look for |
|---|---|
| `cyber_engine_tweaks.log` | TweakXL: duplicate IDs / `Ambiguous definition`; redscript compile errors |
| `archivexl.log` | duplicate onscreens registration for `xaires\aston_valkyrie\aston_valkyrie.json` |
| CET console | `PhoenixAMV` after mounting the car (the service tag in the scripts) |

## 6. Symptom → cause

| Symptom | Likely cause |
|---|---|
| Only one Valkyrie | YAML not loaded (wrong folder depth) or duplicate IDs — check the CET console |
| Name shows `TEST` | a plain-string `displayName`; must be a LocKey (§6) |
| Phoenix car sounds like stock / LEDs dead | scripts not compiled (check redscript log) or `PhoenixAMV_IsTarget` never true (record ID mismatch) |
| No engine audio on **both** cars | shared bank failed to load; check `archivexl.log` |
| redscript error mentioning `VC_DeepCopyAudioMetadata` | VehicleCore missing or out of date |
| Car invisible / no collisions | archive not deployed or `.xl` missing |

## 7. Rollback

Disable `Phoenix_aston_cheats` in Vortex, restart. Stock is untouched, so nothing
else changes.
