# The wobble: damping, not grip

The car weaves under ADE and it is the car's fault. This note explains why, what was changed, and
what to try next if it is not enough.

## Why an AI driver makes an underdamped car look broken

ADE is a controller with lag. Every 100 ms or so it measures heading error, commands a steering
angle, and waits for the car to answer. A human driver does the same thing but *predicts* — they
feel the car start to rotate and release the wheel before the error is even measurable, which is
how people drive badly damped cars without noticing.

The consequence is textbook: a control loop is stable when its phase margin is positive, and that
margin depends on plant damping. Give the same robot a car whose yaw/roll modes are damped and it
drives smoothly; give it an underdamped car and every correction is answered by an overshoot,
which it corrects again — a sustained weave at the loop frequency, appearing as a wobble. **The
controller cannot fix that by being smarter, only by being slower.** Which is why the fix belongs
in the car.

## What was actually wrong

The physics is the Jesko Attack's, copied verbatim, and the Jesko is a *track* car: stiff bars,
low low-rate damping, and roll deliberately coupled into the turn. On its own mass, inertia and
geometry that is a sharp, settled car. Ours has different inertia and different suspension
geometry, so the same rates leave it underdamped — the body keeps moving after the car has
stopped rotating, and ADE chases that residual motion.

## The overlay

Five fields in `tools/port_to_phoenix.py` (`STABILITY_OVERLAY`), applied after the reference copy.
**Nothing that produces speed is touched** — power, drag, gearing, mass, brakes and grip are all
untouched, so every top-speed measurement so far stays valid.

| field | reference | Phoenix | why |
|---|---|---|---|
| `springBoundDampingLowRate` (F / R) | 2200 / 2500 | **2900 / 2900** | the stock Aston's rate; low shaft speeds are where small steering inputs live |
| `springReboundDampingLowRate` (F / R) | 2300 / 2500 | **5000 / 5000** | the stock Aston's rate — 2x the rebound control of the reference |
| `antiSwaybarDampingScalor` | 0.75 | **1.0** | the reference damps its anti-roll bars to 75 %; that lets the body keep rocking |
| `wheelTurnMaxAddPerSecond` | 137 | **110** | steering rate, 20 % slower: less excitation per command |
| `turningRollFactor` | 1 | **0** | the reference couples roll into turning; the stock Aston, and every other car in the corpus, does not |

The two damping rates come from the stock mod's own car — a car that people drove happily in this
game, at this weight. That is the whole argument for those numbers: they are known-good on this
chassis, not invented.

## What to try next, in order

If it still weaves, in order of likely payoff:

1. **`turnUpdateMaxSpeedTurnChangeMul` 2.15 -> 1.0.** This scales how sharply the turn update
   responds to *changes* in input at high speed — i.e. it is a gain on exactly the oscillation
   ADE produces. Halving it is the most direct damping available, and it costs only steering
   response, not grip.
2. **`useAlternativeTurnUpdate` true -> false.** A different steering response model. The
   reference uses it; the stock Aston does not. Swap it and see which model weaves less.
3. **Rear grip up, front grip down.** A car that understeers slightly is self-damping — the front
   saturates first and stops adding yaw. `frictionMulLateral` 1.30 F / 1.28 R is nearly neutral;
   1.20 F / 1.35 R builds in stability, at the cost of some turn-in.
4. **`swaybarStiffness` 18 / 15 -> 14 / 12** and `swaybarDisplacementLimit` 0.14 -> 0.18, letting
   the body roll a little more, more slowly.

Each is one line; each is testable in a single drive.
