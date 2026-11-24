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

## The physical basis, quantified

Take the game's numbers at face value as SI-ish: `springStiffness` 27 as N/mm wheel rate, damping
as N·s/m, corner mass 1800/4 = 450 kg. That gives a body mode of

    wn = sqrt(k/m) = sqrt(27000/450) = 7.75 rad/s = 1.23 Hz      c_crit = 2*sqrt(k*m) = 6971 N·s/m

and then the damping ratio of each candidate rate:

| damping | ζ | Q = 1/2ζ | |
|---|---|---|---|
| 2200 (reference bound) | 0.32 | 1.58 | |
| 2300 (reference rebound) | 0.33 | 1.52 | underdamped |
| 2500 (reference rear) | 0.36 | 1.39 | |
| 2900 (stock Aston bound) | 0.42 | 1.20 | |
| **5000 (stock Aston rebound)** | **0.72** | **0.70** | textbook well-damped |
| 6971 | 1.00 | 0.50 | critical |

**Two independent roads meet at the same number.** Vehicle dynamics practice targets ζ ≈ 0.6-0.8
for ride and body control; ζ = 0.65 needs c = 4,531 N·s/m. The stock mod's car happens to use
5,000. So the value we adopted is simultaneously "known good in this engine on this mass" and
"what the damping ratio criterion asks for" — which is the strongest position a number can be in.

Also: the reference's rebound/bump ratio is 2300/2200 = **1.05**, i.e. symmetric. Race practice is
1.5-3.0, because rebound has to control the spring's stored energy while bump mostly just follows
the road. The stock car's 5000/2900 = **1.72** is conventional. A symmetric damper lets the body
return at the same rate it compresses, which is precisely a body that keeps moving.

### Why a lagging controller cares

At 1.23 Hz, controller latency alone eats this much of the phase budget:

| ADE loop delay | phase lost at the body mode |
|---|---|
| 50 ms | 22° |
| 100 ms | 44° |
| 150 ms | 67° |
| 200 ms | 89° |

A second-order mode contributes up to 180° of phase across its resonance, and near ωn it
contributes 90° on its own. Add 45-90° of latency and the loop is at or past −180° at exactly the
frequency where the plant is *also* amplifying (Q = 1.5 in the reference). That is not a tuning
problem at the controller; it is the plant sitting in the wrong place in the loop. Raising ζ to
0.72 both moves the plant's phase transition away from the loop's crossover and cuts its peak
amplification from 1.5× to 0.7×.

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

## Where the physics is solid, and where it is borrowed

Solid, textbook:
- ζ ≈ 0.65-0.8 for body modes; the 1.23 Hz mode computed from wheel rate and corner mass.
- rebound > bump (1.5-3×) as the conventional asymmetry.
- phase loss from transport delay scaling with frequency, and a second-order mode contributing up to
  180°. This is why a lagging controller and an underdamped plant interact at all.
- **More grip would make it worse, not better.** Lateral grip is the plant's *gain*: raising it
  raises loop gain and drops phase margin. This is why nothing in the grip map was touched, even
  though "make it stick better" is the intuitive fix.

Borrowed or inferred:
- the unit assumption (N/mm, N·s/m). It is self-consistent and lands the stock car exactly on a
  textbook ζ, which is evidence, not proof.
- `turningRollFactor`'s exact formulation is inferred from its name and from the fact that only
  the reference sets it to 1. It is the one field in the overlay I would bisect last.
- ADE's actual poll rate; the table above spans the plausible range rather than claiming one.

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
