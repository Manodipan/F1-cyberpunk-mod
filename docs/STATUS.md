# Status
**Resuming a session? Read [NEXT-SESSION.md](NEXT-SESSION.md) first** — build to install, the
pending measurements, and the mistakes not to repeat.


**ADE is now a read interface, not a mystery.** Its source is in the repo. It does not drive: it
hands `maxSpeed = max(gear.maxSpeed) × ratio` to the native AI. With our 98 ceiling, **Max Speed
Ratio 0.97 = 95.06 m/s exactly**, and the car has 1.84 m/s of headroom so the AI can hold it. Its
stopping radius is linear in speed where braking is quadratic, so it will brake too late at 95 —
[ADE-INTERFACE.md](ADE-INTERFACE.md).

**Build 900033 — 95 m/s reached on a slope, not a rev limiter.** The gear ceiling is 98 (never
reached), torque 1650, so drag stops the car at ~96.9 m/s and 95 sits on a gentle part of the curve
(+0.19 m/s² in hand). That is the plant Auto Drive Enhanced needs; a ceiling exactly on the target
is a step nonlinearity no controller can damp. §2p of TOPSPEED-TEST.md.

**Build 900032 — the car is designed INSIDE the wall: 95 m/s = 342 km/h.** A 2025 "Vehicle Speed
Unlimiter" plugin does not let the game load on 2.5, so the bypass is off the table. The target is
now 95 m/s: 5 m/s clear of the engine limit, faster than anything the game ships (~55 m/s), and
built from the stock Aston mod with **one gear field, one ratio and the torque** changed.
See [TOPSPEED-TEST.md](TOPSPEED-TEST.md) §2o.

**The 100 m/s wall is the game, not the car.** Engine-level vehicle speed limit at exactly 100 m/s
(360 km/h); the native `vehicle::RigidBody::Recalculate` returns a non-finite result at the limit and
the frame's velocity is discarded. It is not tunable from TweakXL or redscript. Bypass with a RED4ext
plugin — `Vehicle Speed Unlimiter` (try it; it resolves by reloc hash, not address) or the current
`Let There Be Flight`, which ships the same hooks unconditionally. Full evidence in
[SPEED-CAP.md](SPEED-CAP.md). Everything below 100 m/s — ladder, ratio invariant, rpm floors,
window overlap, the weave work — is unaffected and still needed. — where PORT.md stands

Updated 2026-11-24 · branch `arena/fd35b985-f1-cyberpunk-mod` · bases on `main` @ `3a6d0b1`
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
| **Paint / livery in both slots** | `compat/xaires_car_manager/repatch.ps1` (v3) | **confirmed in game 2026-11-24** — the Phoenix paints from the *Aston Martin Valkyrie LMH* pane, all 149 colours, no art, no dependency mod. Colour choice is shared with the stock Aston (same `amv` entry) |
| Both mods boot together | — | **confirmed**: `redscript_rCURRENT.log` compiled both `xaires_*` and `phoenix_*`; game session clean with both archives + both `.xl` |
| Tests | `tests/test_port.py`, `tests/test_package.py`, `tests/test_compat.py` | 57 tests, incl. "committed tree == tool output", the packaging rules, and the compat-patch regressions (double comma, bare record id) |

`red4ext/` is deliberately absent: the Phoenix scripts load the stock bank at
`red4ext/plugins/AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk`.

## Still open

| # | Item | Why | Unblocks it |
|---|---|---|---|
| 1 | **v11 CONTROL — MEASURED: no cap, the game's speedometer inflates 2.07x** | timed 1 km runs: Jesko **13 s = 277 km/h real**, dash said **572**; Phoenix, on the Jesko's verbatim physics, **13 s = 277 km/h**, dash says **278**. The reference car never did 500 - it does 277 and displays 572, and it stopped at exactly its declared top gear (283). Our physical car already equals it; the difference was display only. `docs/TOPSPEED-TEST.md` §3n | decision pending: display parity (one file) or chase a genuine 500 km/h real (~2.9x force, v9's 350 wall to crack first) | **v12 SHIPPED: TRUE speedometer for every vehicle** — `TRUE_SPEEDO_ALL_VEHICLES` routes `hudCarController` around the game's `speed_to_multiplier` curve for all cars; set False for Phoenix-only |
| 2 | Decide dealer price for the cheat | currently inherits 900 000 / 0 cred from stock | one line in the YAML (edit the *reference*, re-run `make port`) |
| 3 | Reference corpus | every racing car mod's YAML is a worked example of drag/steering at speed, and comparing beats guessing | `make vehicles` (local corpus) + `reference/vehicles/INDEX.md` (committed facts) — see `reference/vehicles/README.md` |
| 4 | **Wobble / ADE stability** | **v14: BACK ON THE STOCK MOD** — every Jesko-derived build was worse (best 72 ADE against the stock car's 80), so the shipped car is the stock Aston mod's own physics again, unchanged (`RESTORE_STOCK_PHYSICS = True`). Baseline confirmed at **80 ADE / 86 hand** (build 900020). 900022 (AWD only) measured: **onset unchanged at 80 on the 11.3 km straight, but no more spin-outs** - so onset (loop gain) and divergence (plant authority) are separate axes. 900024 (whole gain axis) measured: **onset did not move**, recovery slowed, manual top speed up. Four levers have failed on the onset, 900025 moved the 6->7 shift to 100 m/s and **the weave moved to 100 m/s** - third confirmation that the car weaves when it shifts into its top gear. **partly retracted**: 900025 still weaves at 80 (no gear boundary there) and stalls its engine at 100 because 6th ended exactly where 7th began - zero overlap, a bug. 900026 restores overlaps, puts the terminal at 535 km/h inside a 6th that ends at 180, and leaves the 80 m/s weave as the open problem | `docs/STABILITY.md` step 12; the reverted ladder is the record of what does not work |
| 5 | **Scanner build stamp** | the scanner's `horsepower` shows **900000 + BUILD** (currently `900033`) instead of a horsepower claim: it is the one number the game shows on demand, so it proves in one glance whether TweakXL/CET reloaded the installed YAML | bump `BUILD` in `tools/port_to_phoenix.py` with every generated-YAML change |
| 6 | Optional housekeeping | `phoenix_strings.archive` (8 KB, built on the PC) is not committed; F1 livery artwork is deferred and now unnecessary | commit the archive, or leave the local name in place |

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
