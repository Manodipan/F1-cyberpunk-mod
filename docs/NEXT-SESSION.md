# Next session — start here

**Written 2026-11-24, at the owner's bedtime after a ~12 h session.** Nothing is half-applied:
the repo is committed, pushed and clean.

- **Shipped HEAD:** **build 900032** — the car is designed inside the 100 m/s wall at
  **95 m/s = 342 km/h**.
- **Installed in the owner's game:** **900028**. 900029–900031 were never installed; 900032 is the
  one to try.
- **The bypass is closed for now.** The 2025 *Vehicle Speed Unlimiter* prevents the game from
  loading on 2.5. Do not spend another session on it unless a maintained plugin appears.
- **Tests:** 138, green. `make all` clean.

## The decision (settled 2026-11-24)

**Design inside the wall: 95 m/s = 342 km/h, "no more no less."** One gear field, one ratio and the
torque, on the stock Aston base. Details in [TOPSPEED-TEST.md](TOPSPEED-TEST.md) §2o.

## The wall, for context

> **There is an engine-level vehicle speed limit at exactly 100 m/s = 360 km/h = 223 mph.**
> It is not a record, not a TweakXL value, not redscript-reachable. See
> [SPEED-CAP.md](SPEED-CAP.md) for the evidence, the mechanism and the source.

The game discards the frame's velocity when native `vehicle::RigidBody::Recalculate` returns
`FP_INFINITE`. Every "plateau" at 100 since build 900025 was this, not physics. Model C, the drag
fits and the 535/538 km/h predictions were all fitted **below** the wall and are therefore suspect
above it — the first reading past 100 m/s is a measurement, not a confirmation of an old number.

## Order of work

1. **Install 900032 and drive it.** Scanner reads **900032**; full restart (a CET reload does not
   pick up a YAML change). Expected: the car pulls to **342 km/h / 95 m/s** and stops there, because
   7th's `maxSpeed` is the ceiling. Report it in **m/s**, off the Aston's own dash (it reads the
   physics) if the HUD is in imperial mode.
   - Reads ~95 and holds → top speed is done, move to step 2.
   - Won't get past ~90 → thrust is short; raise `engineMaxTorque` (the only lever needed).
   - Anything at 100+ → tell me; that would mean the wall is not where SPEED-CAP.md says.
2. **The 80 m/s weave.** This is now the main open problem — stability outranks everything. Gearing
   is a dead end for it; steering gain, AWD, damping and downforce have all been falsified. The live
   thread is the hysteresis limit cycle (reach, wobble, brake, slow, repeat) — a lagging controller
   on an underdamped plant. Read `docs/STABILITY.md` before touching a field; it has 679 lines of
   what has already failed.
3. **Optional:** the bypass is researched and staged — [BYPASS-PLAN.md](BYPASS-PLAN.md) plus a
   complete, untested plugin in [`native/speedcap/`](../native/speedcap/). Two minutes of diagnosis
   decides it:

   ```powershell
   findstr /C:"593628708" /C:"4067628720" "<game>\x64\cyberpunk2077_addresses.json"
   ```

   Both found -> it is buildable (needs Windows + MSVC). Either missing -> blocked until RED4ext
   ships the hashes; do not write more code. **The 95 m/s car does not depend on this.**

## Do not repeat

- **Do not tune anything to get past 100 m/s.** Torque, drag, gear ratios, rpm floors, AWD: none of
  them are downstream of that function.
- **Do not treat the HUD number as the car.** It reports one value that the whole display path
  shares; the dash now reads the velocity vector instead.
- **Do not extrapolate a two-variable law from one point.** The `torqueMultiplier`/`maxSpeed` force
  law was settled wrongly twice that way, and the audit "correction" that followed had the right
  magnitude and the wrong sign.
- **Gear records stay internally consistent**: `torqueMultiplier × maxSpeed` inside the car's own
  27.9 family, `minEngineRPM ≈ maxEngineRPM × minSpeed/maxSpeed`, and consecutive gear windows must
  overlap (zero overlap is the stall). All three are guarded by tests.
- **Hold conclusions until the owner's number arrives.** Twice a result was announced before it was
  given.

## Resume commands

```powershell
cd $HOME\f1-cyberpunk-mod
git pull --rebase
git log --oneline -3
```

Install the build (game **closed**):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\update.ps1
```

Scanner should read **900032**. Full restart — a CET reload does not pick up a YAML change.
