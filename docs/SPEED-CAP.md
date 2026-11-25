# The 100 m/s wall is the game, not the car

**Verdict (2026-11-24): there is a hard, engine-level vehicle speed limit at exactly 100 m/s =
360 km/h = 223 mph. It is not in any record we can tune, and no torque, gearing, rpm or aero value
will move it. It has to be bypassed with a RED4ext plugin that hooks the native physics function.**

The owner called it first: *"100 is too specific and too round a number to be math."* It isn't
math — it's the point where the game's own rigid-body recalculation stops returning a usable
velocity.

## The evidence

**Other players hit the same wall, at the same number.** r/cyberpunkgame, April 2025:

> "The speed limit is ~360 km/h, not mph. ... I tried modding the bikes ... and tried to make em as
> fast as I can, but as soon as you hit 360 kmh real speed, **the vehicle slams into an invisible
> wall**."

**The engine clamps vehicle movement, not the car's stats.** Rock Paper Shotgun, June 2025, on
*Vehicle Speed Unlimiter*:

> "gets rid of the automatic limits the game puts on car movement speed — ... **the ones you'd bang
> your head against even if you modded or file tweaked a car to go beyond its base top speed
> value**."

That sentence is the whole diagnosis. Tweaking the car cannot pass it. We spent three builds
proving that from the inside.

## The mechanism

`vehicle::RigidBody::Recalculate` is native code. It returns a float-class code
(`FP_INFINITE` = the computed value was not finite). At the limit the game's own function returns
`FP_INFINITE`, and the frame's velocity change is **discarded** — the car keeps the velocity it had,
so it hits a wall that no force can push through. This is why the stop is abrupt and exactly at a
round number rather than asymptotic.

*Vehicle Speed Unlimiter* (Nexus 22155, Jack Humbert, v1.0.2, MIT) does not raise a parameter. From
`jackhumbert/let_there_be_flight`, `src/red4ext/Physics/VehicleSpeedUnlimiter.cpp`:

```cpp
// void vehicle::RigidBody::Recalculate(void)   reloc hash 593628708
REGISTER_FLIGHT_HOOK_HASH(short, 593628708, RigidBody_Recalculate, RED4ext::vehicle::PhysicsData *ps) {
  // apply force to linear velocity
  RED4ext::Vector3 unlimitedVelocity;
  unlimitedVelocity.X = ps->velocity.X + ps->force.X * ps->inverseMass;
  unlimitedVelocity.Y = ps->velocity.Y + ps->force.Y * ps->inverseMass;
  unlimitedVelocity.Z = ps->velocity.Z + ps->force.Z * ps->inverseMass;

  auto result = RigidBody_Recalculate_Original(ps);

  // ignore speed limit in og function
  if (result != FP_INFINITE) {
    ps->velocity = unlimitedVelocity;     // <- the bypass
  }
  return result;
}
```

It recomputes the velocity from force itself and **overwrites what the engine refused**. That is the
only kind of fix that works here: our data path is upstream of the problem and cannot reach it.

A second hook on `vehicle::RigidBody::ForceSetLinearVelocity` (hash 4067628720) does the same for
the game's own direct velocity writes.

## What it means for the builds

- **Everything below ~100 m/s is untouched.** The ladder, ratio invariant, rpm floors, overlap rule
  and the 80 m/s weave work are all still valid and still needed.
- **Our top-speed predictions were fitted on data the cap contaminated.** The 535/538 km/h figures
  came from a drag model calibrated below the wall. Above the wall the resistance is *unknown*, and
  the LTBF hook suggests the engine handles air resistance in a different branch entirely
  (`// only need to apply air resistance when speed is >= 100.0`, `VehiclePhysicsUpdate.cpp`). The
  first reading past 100 is the first real measurement, not a confirmation of an old number.
- 900031's drag 0.10 was a probe for a hypothesis that is now dead. It stays shipped because it is
  the safer build for the first run past 100: air resistance is the unknown term up there, and 0.10
  keeps it from dominating before we have measured it.

## Bypass options, in order of preference

1. **Install *Vehicle Speed Unlimiter* (v1.0.2) and try it.** The hooks resolve through RED4ext's
   `UniversalRelocBase::Resolve(hash)`, a version-keyed relocation database, **not hardcoded
   addresses** — so a plugin built before 2.5 can still resolve on 2.5 if RED4ext carries those
   hashes for the current build. If it fails it fails with a resolution error in the log rather
   than a crash. Cheapest thing to test, and it is exactly the two hooks needed.
2. **Install *Let There Be Flight* (current release).** Same author, MIT, actively maintained
   against 2.5 (repo updated 2026-11-24), and it contains these hooks **in the shipped plugin**,
   registered unconditionally — the unlimiter applies to every vehicle whether or not flight is
   engaged. Heavier mod, but it is the maintained path.
3. **Build a minimal standalone plugin from the MIT source** — two hooks, ~40 lines, no game
   files touched. Needs a Windows toolchain and an untested DLL; not something to ship blind.

## Building our own bypass

Researched and staged: [BYPASS-PLAN.md](BYPASS-PLAN.md) and `native/speedcap/`. Short version: a ~150
line RED4ext plugin hooking two functions whose addresses come from a JSON database, and the one
thing that must be checked first is whether that file contains the two hashes.

## What is not going to work, so we stop trying

- More `engineMaxRPM`, more `engineMaxTorque`, taller gears, shorter gears, zero drag, AWD.
- Any redscript or TweakXL change: both run above this function.
- The speedometer, the dash, the HUD: they *report* the wall, they never caused it.
