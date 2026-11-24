# Next session — start here

**Written 2026-11-24, at the owner's bedtime after a ~12 h session.** Nothing is half-applied:
the repo is committed, pushed and clean.

- **Shipped HEAD:** `fd99f4d` (docs) on top of `5e01110` (**build 900031**).
- **Installed in the owner's game:** **900028**. Builds 900029 / 900030 / 900031 were never
  installed — the owner (correctly) declined to keep reinstalling while the premise was wrong.
- **Tests:** 138, green. `make all` clean.

## The one thing that unblocks everything

> **There is an engine-level vehicle speed limit at exactly 100 m/s = 360 km/h = 223 mph.**
> It is not a record, not a TweakXL value, not redscript-reachable. See
> [SPEED-CAP.md](SPEED-CAP.md) for the evidence, the mechanism and the source.

The game discards the frame's velocity when native `vehicle::RigidBody::Recalculate` returns
`FP_INFINITE`. Every "plateau" at 100 since build 900025 was this, not physics. Model C, the drag
fits and the 535/538 km/h predictions were all fitted **below** the wall and are therefore suspect
above it — the first reading past 100 m/s is a measurement, not a confirmation of an old number.

## Order of work

1. **Ask whether RED4ext is installed.** `Vehicle Speed Unlimiter` and `Let There Be Flight` are
   both RED4ext plugins; if the game only has redscript/TweakXL/ArchiveXL, neither can run.
2. **Try to move the cap, with no mod reinstall.** Install *Vehicle Speed Unlimiter* (Nexus 22155,
   v1.0.2, MIT) over the current 900028 install and drive. Its hooks resolve through
   `UniversalRelocBase::Resolve(hash)`, a version-keyed relocation database, not hardcoded
   addresses, so a June-2025 build can still resolve on 2.5. A failure shows up as a resolution
   error in the log, not a crash.
   - If it does not resolve → *Let There Be Flight* (current release) ships the same
     `Physics/VehicleSpeedUnlimiter.cpp` hooks **unconditionally**; flight does not have to be
     engaged. Heavier, maintained, 2.5-aware.
   - If neither works → build the two hooks as a standalone MIT plugin (needs a Windows
     toolchain; do not ship an untested DLL).
3. **Once the cap moves, install 900031** and measure. It is the right build to measure with:
   drag 0.10, so the unknown air-resistance branch above 100 does not dominate before we have read
   it; 6th 66→110 (mult 0.254), 7th 100→160 (mult 0.174), torque 4900, mass 1750, AWD.
   The Aston dash now reads `GetLinearVelocity` in km/h — **the physics, not the HUD value** — so
   the wall is resolved to 1 km/h = 0.28 m/s. Ask for it in **m/s** as always.
4. **Re-size the ladder against the measured resistance above 100**, not against the old fit.
   Then set drag for the actual 500 target rather than leaving the 0.10 probe value in.
5. **The 80 m/s weave is still unsolved** and independent of all of this. Gearing is a dead end for
   it; steering gain, AWD, damping and downforce have all been falsified. It is the next real
   physics problem after 500.
6. **Long-standing unanswered numbers** (ask once each, then drop them): the manual top speed on
   900025; whether the wall was *exactly* 100.0 in build 28; whether any other vehicle mod
   (a third-party speed limiter) is installed.

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

Scanner should read **900031**. Full restart — a CET reload does not pick up a YAML change.
