# ADE, read from its source

**Auto Drive Enhanced** — nobo, Nexus 23157, v0.0.0.22 (2026-10-30). Redscript + TweakXL +
CET. The owner uploaded the full mod to this repo, so this is read from its code, not inferred.

Paths below are relative to the mod root:
`auto_drive_enhanced 23157 0.0.0.22 2026-10-30T10-41Z UQrhQSIqI/`

## The one thing to understand: ADE does not drive

It builds an AI command and hands it to the game's own vehicle AI:

```redscript
// driving_ai.reds:533
public func Create() -> ref<AIVehicleDriveToPointAutonomousCommand> {
    let cmd = new AIVehicleDriveToPointAutonomousCommand();
    cmd.clearTrafficOnPath = this.m_settings.clearTrafficOnPath;
    cmd.driveDownTheRoadIndefinitely = this.m_settings.driveDownTheRoadIndefinitely;
    cmd.useKinematic = this.m_settings.useKinematic;
    cmd.minimumDistanceToTarget = this.m_settings.minimumDistanceToTarget;
    cmd.maxSpeed = this.m_speed.max;
    cmd.minSpeed = this.m_speed.min;
    cmd.targetPosition = Vector4.Vector4To3(this.m_destination);
    return cmd;
}
```

So **throttle, brake and steering are native code** — "the lagging controller" in every earlier note is
the vanilla AI, not ADE. ADE supplies the target speed, the corner speed floor and three policy
flags. That is the entire interface, and it is why car tuning could never fix a hysteresis cycle
ADE was asking for: **the target it asked for was the thing oscillating.**

## What ADE reads out of our car

| our field | ADE uses it for | code |
|---|---|---|
| every gear's `maxSpeed` | the car's "maximum speed" | `driving_ai.reds:857` |
| `wheelTurnMaxAddPerSecond` + `wheelTurnMaxSubPerSecond` | corner speed floor | `driving_ai.reds:840` |
| `total_mass` | braking-distance factor | `driving_ai.reds:817` |
| front/back `maxBrakingTorque` | braking-distance factor | `driving_ai.reds:812` |
| current speed | stopping radius | `driving_ai.reds:806` |

```redscript
// driving_ai.reds:857 — the top speed is OUR gear ladder
private func GetVehicleMaxSpeed() -> Float {
    let gears: [wref<VehicleGear_Record>];
    this.GetVehicle().GetRecord().VehEngineData().Gears(gears);
    let max = 0.0;
    for gear in gears { max = MaxF(max, gear.MaxSpeed()); }
    return max;
}

// driving_ai.reds:765 — the target
let maxSpeed = this.GetVehicleMaxSpeed() * autoSpeedControlMaxSpeedRatio;
let minSpeed = MinF(MaxF(this.GetSteeringFactor() * 10.0, 3.0), maxSpeed * 0.75);

// driving_ai.reds:840 — the floor is set by our steering rate
return (dmd.WheelTurnMaxAddPerSecond() + dmd.WheelTurnMaxSubPerSecond()) / 2.0 / 100.0;
```

## The design rule this produces

> **ADE's cruise target = (highest gear `maxSpeed`) × `Max Speed Ratio`.** The car's drag-limited
> balance point must sit **≥ 1.5 m/s above that target**, and the gear ceiling must sit **above the
> balance point**.

Miss the first and ADE pins at full throttle (stable, but it is not *holding* anything). Miss the
second and the car ends on the rev limiter — a step nonlinearity, which is what 900032 shipped.

Build 900033 sits inside both constraints:

| quantity | value |
|---|---|
| gear 7 ceiling (what ADE reads) | 98 m/s |
| car's drag-limited balance | 96.9 m/s |
| net thrust at 95 m/s | +335 N (+0.19 m/s²) |
| **ADE target at ratio 0.97** | **95.06 m/s** — 1.84 m/s of headroom |

## Settings that make ADE drive at 95 m/s

**Primary** — Auto Speed Control **ON**, `Max Speed Ratio` **0.97** (range 0–1, step 0.01):

| setting | value | effect |
|---|---|---|
| Auto Speed Control | ON | target = 98 × ratio |
| **Max Speed Ratio** | **0.97** | **95.06 m/s** |
| **Clear Traffic On Path** | **OFF** | no lane changes — see below |
| Driving AI | Modded Normal AI | as configured |

Check the slider: **ADE's code default is 0.7** (`settings.reds:158`), which would target 68.6 m/s and
look exactly like "ADE refuses to go fast". A reset after a mod update silently changes the target.

**Alternative, exact** — Auto Speed Control **OFF**, `Cruising Max Speed` = **95** (range 1–200,
step 1). Then the target is the number itself with no multiplication. Downside: the fixed-speed
policy also fixes the corner floor from `Cruising Min Speed` (default 10) instead of deriving it from
our steering rate.

## Why lane changes are the route-B skid

`clearTrafficOnPath` is passed straight to the native AI, which then treats traffic as something to
go *around* rather than something to slow behind. A one-lane change at 95 m/s asks for peak lateral
acceleration that this tyre model cannot give:

| lane change duration | peak lateral |
|---|---|
| 1.0 s | 17 m/s² |
| 1.5 s | 7.7 m/s² |
| 2.0 s | 4.3 m/s² |

Anything under ~2 s is beyond the car. **ADE's own default for this flag is `false`**
(`settings.reds:139`); it was set to ON in the recorded configuration. Turn it off and the AI brakes
behind traffic instead of swerving — slower, stable.

## The limitation that no setting fixes

ADE starts slowing at the destination when the car is within `GetStoppingDistance()` (`driving_ai.reds:792`):

```redscript
let distance = 10.0 + (this.GetStoppingFactor() * 15.0);   // autoSpeedControl ON
// GetStoppingFactor = (speed/16) × (mass/1000) × clamp(400/avgBrakingTorque, 0.7, 2.0)
```

For this car at 95 m/s: `(95/16) × 1.75 × 0.7 = 7.28` → **radius 119 m**. The distance the car
actually needs to stop from 95 m/s at a realistic 10 m/s² is **451 m**.

The radius scales *linearly* with speed; braking distance scales with the **square**. So ADE will
always brake far too late at 95 m/s (and the setting can only go to 100 m with the fixed-speed
policy, which is shorter still). It will overshoot the end of a run. **Nothing in the car can change
that** — the formula is in the mod.

Practical consequences:

- Engage autodrive with the destination far beyond where you want to stop, and take control for the
  final brake.
- Expect overshoot at the end of a straight; do not read it as a car problem.
- On the straights in between, this does not apply at all — ADE's speed target is the whole story,
  which is what §2p of TOPSPEED-TEST.md measures.

## What this means for tuning, in one line

The car sets the **target** (gear ceiling), the **corner floor** (steering rate) and the **brake
radius** (mass, brake torque). The controller that holds the speed is native and not tunable. So the
car should be built to make its target *easy*: reachable with headroom, no limiter under it, and a
gentle thrust curve at the operating point — which is exactly what 900033 is.
