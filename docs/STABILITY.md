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

## The measured comparison that reframes the whole thing (2026-11-24)

Three cars, same road, same driver, same session. "Wobble" is the speed where ADE starts weaving;
"hold" is the highest speed a skilled hand can keep.

| car | ADE wobble | manual hold |
|---|---|---|
| stock Aston mod (xaires) | **80 m/s** | **85 m/s** |
| the Jesko | 63 m/s | 77 m/s |
| **our Phoenix** | **63 m/s** | **77 m/s** |

Three conclusions, and the last one is uncomfortable:

1. **The Jesko's chassis is the worst of the three** - 8 m/s below the stock Aston in both columns.
   The reference is a 1,400 kg-downforce track car; the stock Aston is a road car on this chassis.
   Copying the reference "exactly" copied the *worse* car, and inherited its ceiling.
2. **Our car is exactly the Jesko's car.** Same 63, same 77. The limit was never our numbers, our
   port, or our gearing - it is the chassis record we copied. That also explains why the top-speed
   measurements kept landing on the reference's own declared gear.
3. The stock Aston's 85 m/s is the number to beat, and it is reachable - it is the same mod, same
   chassis, same base car, with a different drive model.

Diverging the two drive models field by field, the whole `turnUpdate*` alternative family is
**Jesko-only**: `useAlternativeTurnUpdate: true`, `turnUpdateMaxSpeedTurnChangeMul 2.15`,
`turnUpdateMidSpeedTurnChangeMul 1.58`, `turnUpdateInputDiffForFastChange 1`,
`turnUpdateInputFastChangeSpeed 1.7`, `turnUpdateInputDiffProgressionPow 0.7`. The stock Aston has
**none of them** - it runs the plain model with `turnUpdateMaxSpeedThreshold 26` and
`turnUpdateMaxSpeedTurnMul 0.33`.

That is a mechanism, not a correlation: the alternative model scales the steering response by how
fast the *input* is changing (TurnChangeMul 2.15 at high speed). A hand sweeps the wheel; a control
loop taps it. A model that multiplies small fast changes by 2.15 is a model that turns ADE's
dithering into yaw. It also fits the numbers being identical between our car and the Jesko, and
different in the one car that lacks the feature.

### Step 2 (shipped)

    useAlternativeTurnUpdate      true -> false
    turnUpdateMaxSpeedThreshold   45   -> 26      (stock Aston's)
    turnUpdateMaxSpeedTurnMul     0.21 -> 0.33    (stock Aston's)

If the wobble point moves from 63 toward 80, the mechanism is confirmed and the remaining gap is
ordinary tuning. If nothing moves, the mechanism is wrong and the next lever is grip-floor
`minLatFrictionCoef` 0.62 -> 0.95 (also stock Aston's).

## The third car, and what it does and does not prove (2026-11-24)

The **Pagani (Zonda Revo)** tops at **48 m/s** against a 50 m/s top gear and is ADE-stable at
everything it can reach. It is a *weak* control and should be read that way: it never goes fast
enough to encounter the problem, so it cannot prove any drive model is stable at 80 m/s. What it
can do is vote on individual fields, and on the fields that matter it votes with the stock Aston:

| field | Jesko (63 / 77) | stock Aston (80 / 85) | Pagani (stable, slow) |
|---|---|---|---|
| `useAlternativeTurnUpdate` | **true** | absent | absent |
| `wheelTurnMaxAddPerSecond` | **137** | 94 | 100 |
| `turningRollFactor` | **1** | 0 | absent |
| `minLatFrictionCoef` | **0.62** | 0.95 | absent |
| `rearWheelsLatFrictionCoef` | **0.9** | absent | absent |

Every row is a thing **only the wobbling car has**. The two cars that do not wobble either lack
the field or set it to the conservative value. That is not proof of mechanism, but it is a
consistent direction across two independent witnesses, and the top-speed design work has already
taught us what happens when one coincidence is mistaken for a mechanism.

### Step 3 (shipped)

    wheelTurnMaxAddPerSecond    137 -> 94     stock Aston's; the Pagani runs 100
    minLatFrictionCoef          0.62 -> 0.95  the floor of lateral grip once sliding
    minLongFrictionCoef         0.8  -> 0.95  same, longitudinally
    rearWheelsLatFrictionCoef   0.9  -> 1     the reference's deliberate 10 % rear-grip cut

`minLatFrictionCoef` is the one with real physics behind it: it is how much lateral force the tyre
still makes once it is past its peak. A low floor is a car that lets go and keeps going; a high
floor is a car that slides predictably and recovers. At 77 m/s, "lets go and keeps going" is the
difference between a wobble and a spin.

The cost, stated honestly: `rearWheelsLatFrictionCoef` 0.9 -> 1 removes some of the handbrake's
rotation, so handbrake turns will be less lurid. That is a deliberate trade - rotation bias is
exactly what makes a 280 km/h car bite.

## Measured so far

| build | ADE wobble | manual hold |
|---|---|---|
| verbatim Jesko (= the reference car) | 63 m/s | 77 m/s |
| + damping overlay (step 1) | 63 m/s | 77 m/s |
| + alternative turn-update killed (step 2) | — combined with step 3 — | |
| **+ grip floors, steering rate 94 (step 3)** | **72 m/s** | **77 m/s** |

Steps 2+3 together moved the ADE limit **63 -> 72 m/s (+14 %)** and left the hand's limit alone at
77 - which is the 78.5 m/s gear ceiling, so the hand is no longer the limiting instrument. The goal
is ADE flat out, i.e. the wobble point at or above the top speed; the remaining gap is ~6 m/s.

## Step 4 (shipped)

Everything in this step is on one axis: **how readily the car agrees to rotate.**

| field | reference | Phoenix | why |
|---|---|---|---|
| `driftLimit` | 2.3 | **1.6** | the rotation limiter's threshold - the game's own anti-spin net. The reference allows 44 % more angular rate before it engages. |
| `handbrakeLimit` | 2.49 | **1.6** | same threshold, same reference-only field |
| `momentOfInertia` | 2600/780/3000 | **3137/926/3631** | yaw frequency goes as 1/sqrt(I). The reference is lighter in all three axes than the stock Aston; a car that answers the wheel faster than the controller can is how a weave starts. Stock's vector scaled to our 1800 kg from its 1750. |

Yaw mode frequency: sqrt(780/926) = 0.918, i.e. the yaw response is **8 % slower** than the
reference's - deliberately on the same side of the controller's bandwidth as the car that does not
wobble.

## Step 5, staged (not shipped)

If step 4 is not enough, the next axis is damping again: `antiSwaybarDampingScalor` 1 -> 1.15
(the Pagani's value), then `springReboundDampingLowRate` 5000 -> 6500 (ζ 0.72 -> 0.93), then
`slipAngleCurveScale`/`slipRatioCurveScale` 2 -> 1, which are the last Jesko-only fields left.

### The fields that named themselves

| field | Jesko | stock Aston | Pagani |
|---|---|---|---|
| `driftLimit` | **2.3** | **1.6** | absent |
| `handbrakeLimit` | 2.49 | absent | absent |

`driftLimit` lives in the rotation limiter helper (`gamedataRotationLimiter_Record`) - it is the
game's own anti-spin system, the angular rate the car is allowed to reach before the helper
intervenes. The reference raises it **44 %** above the stock Aston's. A car permitted 44 % more
rotation before the safety net engages is a car that spins *before* the net catches it, and it
costs nothing to give that back:

    driftLimit  2.3 -> 1.6      (stock Aston's)
    handbrakeLimit 2.49 -> 1.6  (or remove; it is Jesko-only too)

Also found and **deliberately left alone**, because their semantics are not documented and I am
not going to guess twice in a row: `slipAngleCurveScale: 2`, `slipRatioCurveScale: 2`,
`slipAngleMinSpeedThreshold: 3`, `slipRatioMinSpeedThreshold: 5` - all four are Jesko-only. They
shape the tyre slip curves, and a 2x scale could plausibly widen the linear region (good) or
sharpen the peak (bad). That is a question for a build, not for a paragraph.

## Step 5 (shipped): straights change the diagnosis

Every measurement so far has been **straight-line driving**. That rules out cornering, limit
handling and tyre saturation as explanations: at near-zero steering angle there is no steady-state
cornering to destabilise, so what is happening is a **limit cycle** - ADE corrects a lane error, the
yaw mode answers with overshoot, ADE corrects the overshoot, and the pair settles into oscillation
at some frequency of their own.

On a straight, a vehicle only has two knobs against that: **yaw damping** and **loop gain**.
Damping has been spent (63 -> 72 across steps 2-4). Step 5 spends loop gain:

| field | reference | Phoenix | why |
|---|---|---|---|
| `turnUpdateMaxSpeedTurnMul` | 0.21 | **0.21** (kept) | authority above 26 m/s = the gain ADE's error signal is multiplied by. Step 2 briefly adopted the stock Aston's 0.33; with the alternative turn update off, 0.21 is 36 % less response per correction, and phase margin is the thing being bought. Low-speed agility is untouched because it applies only above the threshold. |
| `antiSwaybarDampingScalor` | 0.75 | **1.15** | the Pagani's value, the highest of the three, on the only car that never wobbles |
| `springReboundDampingLowRate` | 2300 / 2500 | **6500 / 6500** | body-mode ζ = 0.93 on the 1.23 Hz mode, from 0.72 |

The trade is explicitly a *feel* trade: less authority above 26 m/s means the car answers the wheel
more lazily at speed. If it turns out dull rather than stable, that is the line to give back first,
in 0.03 steps (`0.21 -> 0.24 -> 0.27`).

## Step 6 (REVERTED — it made things worse)

The crest theory was good physics and a bad hypothesis: the build with steps 6+7 measured **67 m/s**,
down from 72. That is a regression, and the arithmetic separates the two steps cleanly. Effective
downforce is `maxSpeedFactorGround x ramp(v)`, and the step-7 pair (0.7 @ 80 -> 1.4 @ 139) reproduces
the old curve to within 0.005 below 80 m/s:

| m/s | old (0.7 @ 80) | new (1.4 @ 139) |
|---|---|---|
| 60 | 0.467 | 0.471 |
| 72 | 0.607 | 0.612 |
| 100 | 0.700 | 0.941 |

So step 7 was inert at the speeds being measured, and the whole -5 m/s belongs to step 6. Reverted,
with step 7 kept (it is what matters above 280 km/h).

Why step 6 backfired, most likely in this order:

1. **`smoothWheelContact{Decrease,Increse}Time` 0 -> 0.1 is 0.1 s of lag in the tyre force.** The
   entire difficulty here is a lagging controller; adding lag *to the plant* is the one thing
   guaranteed to make it worse. "Smooth" reads as "stable" and means "slower", and slower is the
   wrong direction for phase margin.
2. **`extremeCompressionEventScalor` 0.74 retains more spring force in a landing** - which makes the
   landing sharper, not softer. The reference's 0.46 is a *softer* car over an impulse, and soft is
   what absorbs a yaw kick.
3. `springDampingHighRateCompression` 0.36 is the only one of the three I would still consider
   trying on its own; high-rate damping should help a landing.

The lesson is worth recording because it is the third time it has bitten: **the stock car's values
are not transferable blindly** - they are correct for a car with different inertia, in a different
steering model. "Adopt what the stable car does" only holds where the mechanism is understood.

## Step 6 (original reasoning, kept for the record): the test road is a crest generator

The measurement road is 4.6 km of Badlands highway with gentle crests. A crest of radius R at speed
v unloads the car by `a = v²/R`, so it goes weightless when `R < v²/g`:

| speed | radius that lifts the car |
|---|---|
| 63 m/s (227 km/h) | 405 m |
| 72 m/s (259 km/h) | 528 m |
| 78 m/s (281 km/h) | 620 m |
| 139 m/s (500 km/h) | 1,970 m |

A 4.6 km Badlands highway has crests well under a kilometre, so **above roughly 70 m/s the car is
repeatedly going light and landing.** That is a speed-dependent trigger (it appears suddenly, as the
launch did), and a landing is an impulse — at 70 m/s, an impulse is a yaw excitation, which is
indistinguishable from a "wobble" from the driver's seat.

Nothing can stop the unload. What can be fixed is what happens on the way down:

| field | reference | Phoenix | why |
|---|---|---|---|
| `extremeCompressionEventScalor` | 0.46 F / 0.38 R | **0.74 / 0.67** | fraction of suspension force *kept* in an extreme compression event. The reference discards 54-62 % of its spring force exactly when it lands; the stock Aston discards 26-33 %. |
| `springDampingHighRateCompression` | 0.3 | **0.36** | the Pagani's: landings produce high shaft velocities, where the *low-rate* damping from step 1 does not apply at all |
| `smoothWheelContact{Decrease,Increse}Time` | 0 / 0 | **0.1 / 0.1** | reference-only fields, both zero: grip is dropped and restored instantly over a crest. 0.1 s turns a step into a ramp — an impulse becomes a force. |

This is also a **testable disambiguation**: if the wobble is terrain-triggered, the same build should
reach a higher speed on genuinely flat ground. If it does not move on flat ground either, then the
flat-road limit cycle of step 5 is the whole story and the terrain work is insurance rather than cure.

## Step 9 (shipped): keep the load, take the frequency down

Step 8's measured trade, and it is steep:

| build | ADE wobble onset | ADE/manual ceiling |
|---|---|---|
| step 7 (`maxSpeedFactorGround` 1.4) | 72 m/s | 72 (hand 77) |
| **step 8 (3.0)** | **55-58 m/s** | **78 m/s** (the gear ceiling) |

Both halves of the prediction happened. More load means later tyre saturation, so the car now runs
all the way to its 78.5 m/s gear ceiling — **ADE effectively drives flat out, which was the stated
goal.** But more load also means higher cornering stiffness, so the yaw mode moved nearer the
controller's bandwidth and the wobble starts 15 m/s sooner.

Since the load is what bought the ceiling, this step keeps it and pushes the frequency back down -
nothing here produces or removes speed:

| field | reference | Phoenix | effect |
|---|---|---|---|
| `momentOfInertia` | 2600/780/3000 | **3450/1020/3995** | stock Aston's vector scaled to our mass, then +10 %. Yaw frequency ~ 1/sqrt(I): 926 -> 1020 is **4.7 % lower** |
| `wheelTurnMaxAddPerSecond` | 137 | **85** | 10 % slower than the stock Aston's 94; a slower command is a first-order lag on the input, and the input is what ADE taps |
| `slipAngleCurveScale` | 2 | **1** | the last Jesko-only fields, and the direct plant-gain lever: they scale the tyre's slip response, i.e. cornering stiffness. 2 -> 1 takes stiffness down without giving up load |
| `slipRatioCurveScale` | 2 | **1** | same |

**Order to give things back if the car turns vague:** the two slip scales first (they change how the
car slides, the most likely to feel wrong), then the steering rate, then the inertia. The slip
scales are the only genuinely untested semantics in the set.

## Step 8 (shipped): downforce is free, so spend it

Measured: top speed was **77 m/s before and after step 7**. The engine models no induced drag, so
downforce costs nothing at all - it is the only stability axis where the currency is not top speed.
Every other field bought here (steering authority, damping, inertia) was paid for in feel; this one
is paid for in nothing.

`maxSpeedFactorGround` 1.4 -> **3.0**, ramp still to 139 m/s. That is 2.14x the aerodynamic load at
every speed above the 20 m/s ramp start:

| m/s | @1.4 | @3.0 |
|---|---|---|
| 60 | 0.471 | 1.008 |
| 72 | 0.612 | 1.311 |
| 78 | 0.682 | 1.462 |
| 139 | 1.400 | 3.000 |

For scale, a real LMH car makes 2-3x its own weight in downforce around 250 km/h, which is roughly
where 1.46 relative puts this car at 280 - so 3.0 is aggressive but not absurd.

**Two effects compete and I do not know which wins**, which is exactly why this is worth measuring:

- More load -> later tyre saturation -> the car has more to give before it starts sliding.
- More load -> higher cornering stiffness -> higher yaw natural frequency -> the mode moves nearer
  the controller's bandwidth. This is the correction I owed on step 7, and it is the mechanism by
  which "more grip" can make a weaver worse.

If the wobble point rises, load dominates and we go higher (4.0, 5.0) until something saturates. If
it falls, frequency dominates and the answer is damping, not load.

## Step 7 (shipped): downforce, the grip lever that damps

Raising a friction coefficient raises the plant's **gain**: more response per unit of steering,
less phase margin, worse for a lagging controller. That is why the grip map was left alone all
along. Downforce is not that. It raises **normal load**, and tyre cornering stiffness rises with
load, so it raises the yaw **damping** term itself (and the yaw frequency, which is the part to
watch). It also keeps the tyres loaded over crests, where step 6 could only soften the landing.

| field | reference | Phoenix | why |
|---|---|---|---|
| `maxSpeedFactorGround` | 0.7 | **1.4** | the value this car carried before the control experiment. Deliberately above every reference car (Jesko 0.7, stock Aston 0.6, Pagani 0.35) - this is our number, not a copied one. |
| downforce helper `maxSpeed` | 80 | **139** | the helper ramps 20 -> maxSpeed and then stops. At 80 m/s it saturated at 281 km/h, so beyond that **downforce was constant while drag kept growing as v²** — the car got relatively lighter the faster it went. The ramp now tracks v² to 500 km/h, which is what the real thing does. |

That second row is the one that matters for the eventual build: a car at 139 m/s with downforce
frozen at its 281 km/h value is a car whose grip per unit of aerodynamic load has halved. Whatever
the wobble turns out to be, that had to be fixed before 500 was reachable.

Cost, stated plainly: induced drag. Downforce is paid for in top speed, and the amount is not
modelled anywhere we can compute - so if the car stops accelerating earlier than it used to, this
is the first field to give back (1.4 -> 1.1 -> 0.9).

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
