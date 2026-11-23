# Status — where PORT.md stands

Updated 2026-11-23 · branch `arena/fd35b985-f1-cyberpunk-mod` · bases on `main` @ `3a6d0b1`
· target game **2.5** (Phantom Liberty)
(the real unpacked mod).

## Done — the Phoenix build is complete except one item

| Item | Where | Notes |
|---|---|---|
| §3 physics table | `tools/port_to_phoenix.py` (`STOCK_TO_F1`) | value-keyed against the **real** stock numbers |
| §4 rename (records, gears, wheels, icons, classes, functions, TweakDBID literals, file names) | `RENAME` / `FILE_RENAME` | covered by the test suite |
| §4 "keep shared" guards | `PROTECT` | assets, `.ent`, bank, `xamw_*`, facts, widget paths, dealer atlas |
| §4 gear ceiling 91.7 → 138.89 | YAML gear 7 **and** `GearSpeed` default | both move together, test-enforced |
| Tweak file | `Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml` | 2000 hp / 3824 Nm / 500 km/h |
| 4 redscript files | `Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie/` | **real logic**, not stubs: audio + virtual gearbox, HUD, rev LEDs, speed readout |
| Archive + `.xl` | `Phoenix_aston_cheats/archive/pc/mod/` | byte-identical copy, renamed (11.6 MB, tracked) |
| Audit gate | `make check` | identifiers, stock physics, script↔YAML references |
| Pretty name (optional) | `docs/WOLVENKIT.md`, `tools/localization/en-us.json`, `make check-strings` | pack `phoenix_strings.archive` once in WolvenKit; `tools/inspect_archive.py` proves the path landed |
| Target game | Cyberpunk 2077 **2.5** (Phantom Liberty) | payload is version-agnostic; the WolvenKit step needs WK **10.x** (9.1.1 has no 2.5 support) |
| Mod packaging | `tools/package.py`, `make verify-package`, `make package` | game-root mirror only: no docs/junk in the payload, archive + `.xl` paired, tweaks/scripts in their subfolders; builds `dist/Phoenix_aston_cheats.zip` |
| Tests | `tests/test_port.py`, `tests/test_package.py` | 41 tests, incl. "committed tree == tool output" and the packaging rules |

`red4ext/` is deliberately absent: the Phoenix scripts load the stock bank at
`red4ext/plugins/AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk`.

## Still open

| # | Item | Why | Unblocks it |
|---|---|---|---|
| 1 | Pretty name ("Phoenix AMV LMH") — **confirmed in game 2026-11-23** (card + scanner info) | the strings live in a CR2W `JsonResource` **inside** the archive — the stock archive has none at all, so the card falls back to the record name (`PHOENIX_ASTON_VALKYRIE`, already distinct) | `docs/LOCALISATION.md` — pack `tools/localization/en-us.json` into the archive (WolvenKit, one file) |
| 2 | Paint / livery in the two slots (Rosso Fiorano + bronze) | the manager paints the stock Aston but not the Phoenix; the dump showed v2 had a Lua syntax error (double comma) **and** a bare record id where `carOf` needs the full `Vehicle.` name | run `compat/xaires_car_manager/repatch.ps1` (v3), reload mods, spawn, pick the colours |
| 3 | **v2 handling test** (hairpin, top speed, launch) | needs the game | `docs/INSTALL.md` §4 matrix |
| 4 | Confirm both mods boot together cleanly | CT/LM: two archives, two `.xl`, two `ScriptableService`s, both loading the same bank | first launch — check `cyber_engine_tweaks.log` and `archivexl.log` |
| 5 | Decide dealer price for the cheat | currently inherits 900 000 / 0 cred from stock | one line in the YAML (edit the *reference*, re-run `make port`) |

## Risks worth knowing before the first launch

1. ~~Duplicate `.xl` localisation entry.~~ **Fixed:** `phoenix_aston_valkyrie.archive.xl`
   now registers its own `phoenix\aston_valkyrie\en-us.json`, so the two archives
   no longer declare the same (missing) onscreens file. Until that file is packed
   the lookup simply misses and the card keeps the record-name fallback.
2. **Same bank loaded twice** (`AudioXLNative.LoadBank` in both mods). The return
   codes are already handled (`1 || 69`); if the second load fails it just logs.
3. **Both wrappers chain**, by design: each `@wrapMethod` checks the mounted
   vehicle's TweakDBID via `PhoenixAMV_IsTarget` / `XairesAMV_IsTarget`, so the
   stock car keeps stock HUD/audio behaviour and the Phoenix car keeps its own.
4. **Shared `xaires_cm_vol` fact** — the "Xaires Car Manager" volume slider applies
   to both cars. Intentional (one bank, one mix).

## Corrections to PORT.md found while porting the real files

| PORT.md said | Reality |
|---|---|
| `XairesAMVF1` module → `PhoenixAMV` | no `module` declaration at all; names are free functions `XairesAMV_*` + classes `XairesAMV*`. Renamed to `PhoenixAMV_*` / `PhoenixAMV*` |
| `_f1` IDs everywhere | the previous chat's `_f1` artefacts never existed; the port is stock → Phoenix directly |
| `VC_DeepCopyAudioMetadata` is part of the mod | it is **VehicleCore's** API. Renaming it (an early draft did) breaks the audio copy — now a regression test |
| steering "94/26/0.33" | `wheelTurnMaxAddPerSecond` 94, `turnUpdateMaxSpeedThreshold` 26 **m/s**, `turnUpdateMaxSpeedTurnMul` 0.33 |
| `.archive` copies must be made by hand | now done and committed |
| script bodies must be restored | not true — the real scripts are ported verbatim |

## Next three actions

1. Launch with both mods and run `docs/INSTALL.md` §4 → report speeds/symptoms.
2. Watch the two logs for duplicate-registration warnings (item 3 above).
3. If the handling report says "wobble" or "bog at the 6→7 shift", tune in the
   reference YAML and `make port` — never hand-edit the generated tree.
