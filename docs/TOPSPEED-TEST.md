# Top-speed test — hands off the wheel

Goal: prove the v2 physics reach the **138.89 m/s (500 km/h)** ceiling in gear 7, with no
human input in the loop. Auto Drive drives the car with the game's own AI, so the throttle
is applied smoothly and consistently — better evidence than a keyboard hold.
Background on what sets the ceiling (gears, drag, and the engine-level speed limiter):
[`VEHICLE-MODEL.md`](VEHICLE-MODEL.md) §4–§5.

Test mod: **Auto Drive Enhanced** (Nexus 23157, by nobo). Requires ArchiveXL, redscript,
Input Loader, TweakXL; Mod Settings is optional but is where the knobs live.

## 1. Configure the mod (once)

Settings → **Mod Settings** → **Auto Drive** (main menu or pause menu, the tab the mod adds):

| Setting | Set to | Why |
|---|---|---|
| **Max speed** | the vehicle's maximum / **100 %** | vanilla autodrive obeys a road-speed limiter; this is the setting that lifts it. If yours is a plain number, use `500` (km/h) |
| **Driving AI** | **Modded AI** | drives with the car's own physics instead of the vanilla planner, which is what we want measured |
| Restrictions (v0.0.0.15+) | remove **"valid lane"** and **"not in combat"** | the AI otherwise aborts the run on a lane it does not like |
| Cheat settings (v0.0.0.19+) | optional: **no damage** | a 500 km/h kiss with a barrier otherwise ends the run before the number is read |

Version note: **0.0.0.20+** is the first that stops an internal minimum speed from
overriding your max-speed setting, and **0.0.0.21+** is the one that works on 2.5. If
the car refuses to pass ~150 km/h, that is the version, not the car.

## 2. Run it

1. Spawn the Phoenix, sit in it.
2. Set a destination down a **long straight** — the Badlands highway is the usual one.
   Corners are the enemy of this test: the AI brakes for them, and we are measuring the
   drag wall, not cornering.
3. Engage autodrive and **do not touch the controls**.
4. Watch the car's own HUD read-out (the Phoenix dash is scripted, so it reports km/h
   directly) and the gear indicator.

## 2b. The test roads

Two routes, both used, recorded here so a number always comes with the road it was taken on.
Every speed in this repo is only comparable within one route.

**Route A — the 4.6 km Badlands highway.** Gentle crests, straight or very gentle curves. The
route every number up to build 900021 was measured on. Its defect: crests. A crest of radius R
unloads the car by `v²/R`, so at 78 m/s any R below 620 m puts the car weightless, and a 4.6 km
highway has sub-kilometre crests — the car is repeatedly going light and landing, which is a yaw
impulse every few seconds. That was a live hypothesis for the wobble for four builds (steps 6-8).

**Route B — Badlands edge to the south of the map (found 2026-11-24).** **11.3 km** as the
waypoint measures it (surveyed from the map, 2026-11-24), one nearly continuous straight through
the Badlands with **three perpendicular turns** in the whole run. At 330 km/h that is a **123 s**
traverse; at 500 km/h, **81 s**. Compare Route A's 4.6 km, which was 46 s at 330 and ended before
the car was done accelerating.

Route B is the better instrument for three reasons:

- **It exonerates or convicts the crest hypothesis for free.** If the wobble appears on a long flat
  straight too, crests are not the mechanism and the remaining steps of that theory can be closed.
- **It can show a terminal speed.** Route A ends before the car is done accelerating; a run long
  enough to flat-line turns "top speed" from *where the wobble started* into a measured plateau.
- **It scales to the 500 km/h build.** Reaching 138.9 m/s from the stock car's 91.7 needs distance,
  and `d = (v₂² − v₁²) / 2a` is brutal up there:

  | excess thrust | constant-a distance 91.7 → 138.9 m/s |
  |---|---|
  | 2.0 m/s² (0.20 g) | 2.7 km |
  | 1.5 m/s² (0.15 g) | 3.6 km |
  | 1.0 m/s² (0.10 g) | 5.4 km |
  | 0.5 m/s² (0.05 g) | 10.9 km |

  Those are optimistic. Thrust falls as `1 − (v/v_term)²`, so the approach to terminal speed is
  asymptotic and the real distance is `d = (v_t² / 2a₀) · ln[(v_t² − v₁²)/(v_t² − v₂²)]`, which is
  much worse than a constant-acceleration estimate near the top. On Route B's 11.3 km the question
  becomes: how much thrust does 500 km/h need to still fit?

  | terminal speed | excess accel needed at 330 km/h to reach 500 in 11.3 km |
  |---|---|
  | 522 km/h | 1.85 m/s² (0.19 g) |
  | 540 km/h | 1.47 m/s² (0.15 g) |
  | 576 km/h | 1.14 m/s² (0.12 g) |
  | 648 km/h | 0.87 m/s² (0.09 g) |

  Read it backwards: **the shipped car needs roughly 0.12–0.19 g of margin at 330 km/h, with a
  terminal speed 20–60 km/h above the target**, to demonstrate 500 on the longest straight on the
  map. A car that is merely *capable* of 500 has infinite distance — it reaches it asymptotically
  and never arrives. This is why every real record car is built for a terminal speed well above
  the number it is named after, and it is the sizing constraint for the 500 build.

To make Route B reusable, note the **fast-travel point at each end** and the three turns the first
time it is driven properly; the table above is only useful if the same road is measured twice.

## 2c. The two numbers measure different things (2026-11-24, owner's observation)

> "ADE is better at lifting throttle for actual turns, usually, and I'm better at giving the
> gentle nudges for straight-line speeding."

That is not a detail, it is a correction to how this whole log has been read. Every "ADE 80" in
this repo has been treated as a statement about the **car**. It is not. It is a statement about
the **car and a controller**, and the controller has a policy:

| | Auto Drive | the owner |
|---|---|---|
| throttle | full, until its own corner anticipation tells it to lift | planted, held through small corrections |
| steering | discrete corrections, no anticipation — a **lagging** controller | small continuous nudges with **lead** |
| good at | slowing for corners, never missing a braking point | holding a straight at speed |

Three consequences, in order of how much they matter:

1. **Part of the 80 may be ADE lifting, not the car weaving.** Route A has gentle curves. A
   controller that lifts for curves it can see is slower on a road that has them, and the deficit
   would be *policy*, not physics. The old number cannot separate the two.
2. **Route B separates them for free.** Long straights, three perpendicular turns: inside a leg
   there is nothing to lift for, so a dip in the speed trace is the controller or the car, never
   the road.
3. **The manual number is the capability; the ADE number is closed-loop behaviour.** A human adds
   phase lead, which is exactly what a plant with poor phase margin needs. So "the human can hold
   86 and ADE cannot hold 80" is the same statement as "the plant can be driven, but not by a
   lagging controller" — which is the frame this entire wobble investigation has been circling.
   The fix for a lagging controller is a plant with more margin, not a better driver.

### Protocol that settles it — one build, two legs, Route B

Same leg, same direction, build unchanged between runs (a restart is only needed between builds):

1. **Leg 1, ADE.** Engage autodrive down the longest straight. Record peak speed, and
   **whether the speed dips while the road ahead is clear** — that dip is policy.
2. **Leg 2, manual.** Same leg, throttle planted, gentle nudges. Record peak and hold.
3. Note whether the car ever actually weaved in leg 1, and where.

How to read it:

- **ADE ≈ manual on Route B (within ~2 m/s)** → the Route A gap was ADE's corner policy, the car
  is not the problem on straights, and the "wobble" needs re-measuring before another build is
  spent on it.
- **ADE well below manual, no corners ahead** → genuine closed-loop instability; the number is
  about the car again and the gain axis is the lever.
- **ADE dips even with an empty road** → the controller is reacting to something other than
  geometry (traffic, a lane edge, a junction it plans for).

## 2d. The controller is a mod, and it has settings (2026-11-24)

Auto Drive is not vanilla: a Mod Settings screen for **Auto Drive Enhanced** drives it, and its
values are part of the measurement whether or not anyone looks at them. As configured on
2026-11-24:

| setting | value | what it does |
|---|---|---|
| Driving AI | Modded Normal AI | which AI the player's autodrive uses |
| **Auto Speed Control** | **ON** | selects the speed *policy*: cruise as a fraction of the car's own maximum |
| **Max Speed Ratio** | **1.0** | "ratio of maximum cruising speed to maximum vehicle speed" — the fraction in question |
| Cruising Max / Min Speed | 30 / 10 | the *other* policy: fixed speeds, used when Auto Speed Control is **OFF** |
| Clear Traffic On Path | **ON** | ADE paths around traffic — so a lane change is **its own decision**, not geometry |
| Sync speed with vehicle in front | OFF | it will not match the car ahead |
| Stopping Distance | 50 | planning distance for stops |
| Base / Speed / Mass / Braking-Torque factor for brake time | 1 / 1 / 1 / 1 | default brake model |

Two consequences that were invisible until now:

1. **The ceiling may be a target, not a limit.** With `Max Speed Ratio 1.0` ADE aims at the car's
   own maximum speed. If its idea of that maximum is ~80 m/s, then every "ADE stops at 80" in this
   log is ADE *arriving at its target*, and the weave starts where it begins modulating around it —
   not where the car runs out of anything. One slider settles it (matrix below).
2. **Lane changes are ADE's own idea, and they are violent.** See the arithmetic below.

### What a lane change costs at 80 m/s

For a lane change of one lane width, d = 3.5 m, modelled as a half-cosine offset, peak lateral
acceleration is `a = (d/2)(π/T)²`:

| duration T | peak lateral | 
|---|---|
| 0.8 s | 27.0 m/s² = **2.75 g** |
| 1.0 s | 17.3 m/s² = **1.76 g** |
| 1.5 s | 7.7 m/s² = **0.78 g** |
| 2.0 s | 4.3 m/s² = **0.44 g** |
| 3.0 s | 1.9 m/s² = **0.20 g** |

A road car's lateral budget is order 1 g, and with downforce more — but not 2.75 g at 288 km/h. So
**a one-second lane change at 80 m/s is a demand no tyre can meet**: the car breaks away because it
was asked to, not because it is unstable. The owner's own version of the same manoeuvre takes two
to three seconds and costs 0.2-0.4 g, which is why it never skids.

At 80 m/s the whole manoeuvre must fit inside ~1.5 s of road (119 m) to stay under 0.8 g. ADE does
not appear to budget for that.

### The matrix that separates policy from physics — no restart, no new build

All three runs on one build, changing only Mod Settings (they apply live):

| run | change | if the ceiling moves | if it holds at 80 |
|---|---|---|---|
| 1 | ratio 1.0, traffic ON (as now) | — | baseline |
| 2 | **ratio raised to its maximum** | the ceiling was ADE's target | the ceiling is the car |
| 3 | **Clear Traffic On Path OFF** on an empty road | the weave was the lane change | the weave is the car |

Run 2 is the single most informative test in this document: it is the only setting that can make
the "80 m/s onset" vanish without touching the car at all.

## 2e. The sawtooth is a free thrust bench

ADE's limit cycle is: climb to 80 m/s, weave, brake, fall, climb again, every **18-22 s**. The
climb half is a full-throttle acceleration run that the controller performs for us, repeatedly,
on the same road. Two readings turn it into data:

- **the trough speed** `v_min` - how far the brake lets it fall
- **the climb time** - how long from `v_min` back to 80

Then `a = (80 - v_min) / t_climb` and the **net force** at ~77 m/s is `F = m·a` with m = 1750 kg:

| Δv (80 → trough) | climb time | mean accel | net force |
|---|---|---|---|
| 5 m/s | 16 s | 0.31 m/s² | 547 N |
| 10 m/s | 16 s | 0.62 m/s² | 1 094 N |
| 15 m/s | 16 s | 0.94 m/s² | 1 641 N |
| 20 m/s | 16 s | 1.25 m/s² | 2 188 N |
| 20 m/s | 20 s | 1.00 m/s² | 1 750 N |

That is the surplus over drag, in the game's own units, at the speed where the 500 km/h problem
lives. Nothing else in this project has ever measured it.

### Why it matters: the sizing question, in one line

If the stock car's **86 m/s manual hold is its terminal speed** (the top gear allows 91.7, so the
car either runs out of thrust at 86 or is gear-capped at 91.7 - see the test below), then drag
force goes as `factor · v²` and reaching 138.9 m/s needs:

- **the drag factor down from 1.35 to ~0.52** (force × 0.385), or
- **2.6× the force** with drag left alone.

Which of those is the real job depends on one observation, and it costs nothing: **flat out down
the whole 11.3 km and watch whether the number stops at 86.** A plateau at 86 means drag-limited,
and the 500 build is a drag-and-gearing job. A number that creeps toward 91.7 and then stops means
the gearbox is the cap, and the 500 build is a gearing job with drag as the secondary.

## 2f. MEASURED: the stock car is drag-limited at 86 m/s, and the 500 build follows from it

Build 900022, Route B, 2026-11-24:

| reading | value |
|---|---|
| flat-out plateau, manual, 11.3 km | **86 m/s** (310 km/h); **87 sustained / 88 in burst** on 900024 |
| ADE sawtooth top | **81 m/s best**, 77-75 on some terrain, 80 typical |
| ADE sawtooth trough | **61 m/s** (31-41 only after hitting a barrier - exclude those, it is external) |
| cycle, brake to brake | 18-22 s |

The plateau is **86, not the top gear's 91.7** - so the car runs out of thrust before it runs out
of gearing. **The 500 km/h problem is a drag-and-thrust problem, not a gearbox problem.**

### The fit

Two readings give the whole force curve, assuming constant thrust in the top gear and
`D = k·v²`:

- sawtooth: 61 -> 81 m/s in ~16 s = 1.25 m/s² over 1750 kg = **2 188 N net at 71 m/s**
- terminal: net force is zero at **86 m/s**

`k = 2188 / (86² - 71²) = 0.929 N/(m/s)²`, `T = k·86² = 6 870 N` at the top of the run.

With 900024's measured 87 m/s sustained, the same fit gives `k = 0.866`, `T = 6 551 N`, and the
900025 design moves from 543 to **549 km/h** terminal with the same 3.0 km to 500. The design is
insensitive to a ±1.5 m/s baseline, which is what you want from something sized off a hand-held
measurement.

### The design points

Drag force scales with the `airResistanceFactor` dial in proportion to the dial (the field is *a*
drag dial, not a CdA - see `docs/TOPSPEED-DESIGN.md` §4), and thrust scales with `engineMaxTorque`.
Distance is `d = (m/2k')·ln[(T - k'v₁²)/(T - k'v₂²)]` from 91.7 to 138.9 m/s:

| drag factor | torque | terminal | distance to 500 | power at 500 |
|---|---|---|---|---|
| **0.55** | **×1.25 (1 625 Nm)** | **542 km/h** | **3.3 km** | **1 193 kW = 1 599 hp** |
| 0.55 | ×1.50 (1 950 Nm) | 594 km/h | 2.0 km | 1 431 kW = 1 919 hp |
| 0.65 | ×1.50 (1 950 Nm) | 546 km/h | 2.7 km | 1 431 kW = 1 919 hp |
| 0.75 | ×1.75 (2 275 Nm) | 549 km/h | 2.2 km | 1 670 kW = 2 239 hp |

**The first row is the recommendation, and it lands on the real cars by itself:** 1 599 hp at
500 km/h is the Chiron Super Sport's 1 578 hp, and the assumed CdA was the Jesko Absolut's 0.523.
The game's own numbers, fitted from a sawtooth on a desert highway, agree with the record cars to
1 %. That is the strongest evidence yet that the sizing is right.

It also fits the road: 3.3 km of acceleration inside an 11.3 km straight leaves two thirds as
margin, so the run demonstrates the plateau rather than arriving at it.

### What it predicts about the wobble

Onset / terminal: stock **81 / 86 = 0.94**; the Jesko control was **63 / 78.5 = 0.80**. Two points
are not a law, but if the weave begins at a fixed fraction of terminal speed, then **cutting drag
raises the terminal *and* the onset together** - the 500 build would be a stability build by
accident. Cheap to check: the first build that moves the plateau above 86 should move the weave
onset by the same ratio. If the onset stays at 81 while the plateau climbs, the two are independent
and the wobble stays a steering problem.

## 2g. 900024 measured: the gain axis does not move the onset — so what does?

| reading | 900022 (AWD) | 900024 (AWD + all three gain levers) |
|---|---|---|
| sawtooth top | 81 best, 77-75 some terrain | **no change** |
| trough | 61 | **61-67** (same, collisions excluded) |
| cycle | 18-22 s | ~25 s, erratic 12-30, many collisions |
| recovery | recovers, occasionally spins | **recovers, but slower** |
| manual plateau | 86 | **87 sustained, 88 in burst** |

Four levers have now been tried against the onset and none of them moved it: AWD, damping
(step 1), and the three-part gain axis including a **-36 % cut in steering authority above 26 m/s**
(900024). What that build did buy is a measured **+1 m/s of manual top speed (86 -> 87 sustained,
88 in burst)**, at the cost of a lazier recovery - so the gain axis is worth its place for the
driver's hands even though it does nothing for the controller. Meanwhile the same build *raised* the manual top speed. That combination is a real
finding: **the weave is not driven by steering loop gain.** Reducing the controller's authority by
more than a third changed the onset by zero, while changing something unrelated (drag-limited top
speed) changed the manual number.

The two explanations still standing both come from coincidences in the data:

**A. The 6 -> 7 transition.** The weave starts where the car shifts into top gear:

| car | gear 6 ceiling | weave onset |
|---|---|---|
| stock Aston | 80.6 m/s | 81 (best) |
| Jesko, verbatim control | 62.47 m/s | 63 |

Two for two, to within 1 m/s, on the two cars that ever ran their own gearbox unchanged. The aero
builds never tested it - their terminals (72, 65, 55-58) fell *below* the 80.6 boundary, so they
never reached the transition at all.

**B. Onset tracks terminal speed.** Three aero builds, three times the plateau and the onset fell
together (72/72, 65/65, 55-58), and the stock car sits at 81/86 = 0.94.

Both predict the same fix, and it is the build the project exists for.

## 2h. Step 16 — the 500 km/h build, which is also the stability experiment (build 900025)

| field | stock | 900025 |
|---|---|---|
| `airResistanceFactor` | 1.35 | **0.55** |
| `engineMaxTorque` | 1300 | **2750** (x2.08) |
| gear 6 ceiling | 80.6 | **100** |
| gear 7 window | 77 -> 91.7 | **100 -> 155** (558 km/h declared) |

Thrust in the new top gear is `6 870 N x 2.08 x (91.7/155) = 8 600 N`, against `k = 0.929 x
0.55/1.35 = 0.378 N/(m/s)^2` of drag: **terminal 150.7 m/s = 542 km/h**, and 500 km/h (138.9)
arrives after ~3.0 km of 7th gear on top of ~2 km getting to 100 m/s - comfortably inside the
11.3 km straight. Power required at 500: **1 195 kW = 1 602 hp**, the Chiron SS's 1 578 hp, from a
sawtooth on a desert highway.

**Why it is also the stability test.** The stock car's top-gear transition sits at 80.6 m/s against
a plateau of 86 - the car lives on top of the transition for its entire top-speed range, which is
the one thing every failed stability build had in common and never changed. In 900025 the
transition moves to **100 m/s (360 km/h)** and the plateau to **542 km/h**: the car spends its
whole accelerating life in a gear it can pull. If the onset follows the transition, the weave moves
to ~100 m/s. If it follows the terminal, it moves to ~0.94 x 150 = **141 m/s** - i.e. clear of the
entire 500 km/h run.

Both predictions say the same thing: **watch whether the weave appears below 100 m/s, at ~100, or
above 300 km/h.** Any of those three answers identifies the mechanism, and the third one is the
deliverable.

## 2i. SOLVED (mechanism): the car weaves when it shifts into its top gear

900025 moved the 6 -> 7 shift to 100 m/s. The weave moved to **100 m/s**. Third confirmation, and
the first where the variable was ours:

| car | top-gear entry | weave onset |
|---|---|---|
| stock Aston | 80.6 m/s | 81 |
| Jesko, verbatim control | 62.47 m/s | 63 |
| build 900025 (6 -> 7 at 100) | 100 m/s | **100** |

Three for three, and 900025 rules out the surviving alternatives one by one:

- **not the drag wall** - the weave sat 52 m/s below 900025's own terminal
- **not a fixed speed** - it was 100, not 80
- **not steering loop gain** - four levers failed to move it, including -36 % authority above 26 m/s
- **not a constant fraction of terminal** - stock 81/86 = 0.94, Jesko control 63/78.5 = 0.80,
  900025 100/148 = **0.68**. No constant exists, so "onset tracks top speed" dies here too.

And it is **intermittent, not a wall**: on 900025 ADE is *capable* of reaching 100 m/s, weaving
sometimes and not others. That fits a hunting loop rather than a hard limit - whether the revs
settle above the downshift threshold depends on the load at that instant, so the same car on the
same road either catches the gear or hunts for it.

**Why a gearbox does this.** The top gear is the one gear with nothing above it, so the shift logic
can hunt at its boundary: upshift, the revs land under the downshift threshold, downshift, upshift
again. Every cycle is a torque transient, and a torque transient through driven tyres is a yaw
kick - which the loop then amplifies into the weave ADE reacts to. It also explains the terrain
sensitivity: whether the engine can pull the tall gear at all depends on load, so the hunt starts
sooner or later depending on the road.

It explains every failed build, too. Nothing done to the steering, the dampers, the inertia or the
driven wheels can stop a gearbox hunting.

## 2j. Step 17 — never reach the top gear (build 900026)

| field | 900025 | 900026 |
|---|---|---|
| gear 5 ceiling | 69.4 | **95** |
| gear 6 ceiling | 100 | **160** (576 km/h) |
| gear 7 floor / ceiling | 100 / 155 | **160 / 180** - above the terminal, so the gear is never used |
| drag, torque | 0.55, 2750 | unchanged |

The car's terminal is ~148 m/s (534 km/h), so **7th becomes unreachable** and the last upshift it
ever makes is into 6th at 95 m/s.

- **If the weave appears at ~95 m/s** -> any upshift does it, and the gearing must be arranged so
  the final upshift happens below the speed range that matters.
- **If the weave vanishes** -> it is specific to the top gear, which is what the stock car's record
  says (its 33 / 44 / 55 / 66 m/s upshifts were all harmless), and the 500 km/h car just needs a
  gear above its terminal that it never reaches.

Either answer is a design rule; the second one is the deliverable.

Numbers for 900026: 6th thrust 8 328 N, terminal 148.3 m/s = **534 km/h**, 500 km/h reached
**3.6 km** into 6th, **1 157 kW = 1 551 hp** at 500. Acceleration in 6th: 2.81 m/s² at 95, 0.59 at
500. One caution: 5th now makes 14 kN of thrust (~0.8 g) and may spin the tyres - if it does, the
torque comes down before the gearing does.

## 3. What to record

| Reading | Pass | Notes |
|---|---|---|
| Top speed reached | **~500 km/h** (138.89 m/s), then flat | the drag wall is `airResistanceFactor 0.90`; if it stops at e.g. 420, that number is what we tune |
| Gear at top speed | **7th**, no hunting between 6 and 7 | gear 7 is a long overdrive by design |
| Time to 300 km/h | record it, no target yet | acceleration is torque 3824 Nm over 1750 kg |
| Steering behaviour | tracks straight hands-off | any **wobble here is the car**, because no human is steering |
| Audio / LEDs | revs climb, LEDs sweep, no cut-out | audio ceiling = 138.89 |

## 3b. Known: it plateaus at ~330 km/h (reported 2026-11-24)

**330 km/h = 91.7 m/s = the *stock* Valkyrie's gear-7 `maxSpeed`.** Our record sets that
same field to **138.89**, so a hard plateau on 91.7 is a **ceiling being enforced**, not
the car running out of power: with `engineMaxTorque 3824` and `airResistanceFactor 0.90`
the terminal velocity is north of 450, nowhere near 330.

Three candidates, cheap to separate:

| Candidate | Check |
|---|---|
| the installed YAML is stale (old gear set) | `tools/gearbox-check.ps1` prints the **installed** file's gear 7 and counts `138.89` |
| the `gears:` `!remove` / `!append` block did not take (TweakXL error) | same file shows the TweakXL log lines; an `Ambiguous`/`not found` on the gear records is the answer |
| drag wall after all | negative result of both, *and* the engine sits **mid-rev** at the plateau |

In-game tell, no tools: at the plateau, are the rev lights pinned (engine maxed → the game
thinks that is top gear) or mid-scale (engine has headroom → drag)?

```powershell
cd $HOME\f1-cyberpunk-mod
powershell -ExecutionPolicy Bypass -File .\tools\gearbox-check.ps1
```

If the file is clean and the logs are silent, the A/B test settles it: set gear 7
`maxSpeed` to `100` (360 km/h) and rerun — plateau moves to 360 means it is the gear
ceiling and the append is being ignored; still 330 means it is drag, and
`airResistanceFactor` comes down from 0.90.

## 3c. The 572 km/h reference (Koenigsegg Jesko Attack) — what it proved

`reference/vehicles/jesko_attack/jesko_attack.yaml` is that car's actual tweak file (kept
from the corpus the collector built on 2026-11-24). Its numbers:

| | Jesko Attack (572 km/h) | Phoenix (stops at 330) |
|---|---|---|
| last gear `maxSpeed` | **78.5 m/s = 283 km/h** | 138.89 m/s = 500 km/h |
| gears | 8, one explicit `gears: [ … ]` list | 8, via `8 × !remove` + `8 × !append` |
| `airResistanceFactor` | **0.66** | 0.90 |
| `engineMaxTorque` | 1000 | 3824 |
| `total_mass` | 1800 | 1750 |
| steering | 137 / threshold **45** / mul **0.21** | 94 / 26 / 0.33 |
| `maxSpeedFactorGround` (downforce) | 0.7 | 1.40 |
| `turningRollFactor` | 1 | 0 |
| `driftLimit` / `maxAngularSpeedRad` | 2.3 / 2.6 | 1.6 / 2.6 |
| `frictionMulLateral` | 1.3 | 1.60 front / 2.00 rear |

Two conclusions, and one of them kills our earlier theory:

1. **A car's top speed is not its gear table.** The Jesko does 572 km/h on a gear set
   whose last entry says 283 km/h — exactly 2× over. So `maxSpeed` per gear is the
   *shift point*, not a hard cap, and "330 = the stock 91.7 gear value" was a coincidence
   of arithmetic, not a proof of where the wall is.
2. **Our engine block is the suspicious part, not our gear numbers.** It inherits
   `Vehicle.VehicleEngineData_4_SuperSport` and then removes that record's 8 inline gears
   and appends ours. If those 8 `!remove` lines miss their targets, the inherited gear set
   stays **in front of** ours and the transmission drives the car it inherited from. The
   Jesko avoids this entirely: one explicit list, no inherited gears at all.

**Fixed in the deliverable, 2026-11-24.** The port tool now emits that form itself
(`explicit_gears()` in `tools/port_to_phoenix.py`), so the shipped YAML carries

```yaml
gears: [ Vehicle.phoenix_amv_gear_r, …, Vehicle.phoenix_amv_gear_7 ]
```

with no `!remove` and no `!append`, and two tests enforce it
(`test_gearbox_is_one_explicit_list`, plus the existing "committed tree == tool output").
Nothing to install by hand: `git pull`, copy the deliverable YAML over the game's copy,
restart.

**Result in game, 2026-11-24: still ~300 km/h, still wobbly.** So the explicit list was
necessary (a fragile block is gone for good) but it was *not* the wall. §3d is what the
second failure revealed.

```powershell
$d = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\r6\tweaks\phoenix"
Copy-Item "$d\phoenix_aston_valkyrie.yaml" "$d\phoenix_aston_valkyrie.yaml.stock" -Force   # once, as insurance
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" $d -Force
```


## 3d. The wall was the gear *ratio* — the overdrive (2026-11-24, second failure)

Conclusion 1 in §3c was half right in a way that mattered. `maxSpeed` per gear is not a
cap, but it is not decorative either: **a gear's window sets its ratio**, and the Phoenix
was given one heroic overdrive:

| | window | ratio span | torque multiplier |
|---|---|---|---|
| stock 7th | 77 → 91.7 m/s | **1.19×** | 0.306 |
| Phoenix 7th (failed) | 77 → 138.89 m/s | **1.80×** | 0.306 |
| Phoenix 6th | 66 → 80.6 m/s | 1.22× | 0.348 |

One gear was asked to cover **277 → 500 km/h** while carrying the weakest multiplier in
the box — and 6th still ended at 290 km/h. So the car ran out of pull exactly where its
last *usable* gear ended: ~300 km/h, twice reported. The stock car never showed this
because its 7th only spans 15 m/s, which is why "stock tops out at exactly 91.7" looked
like a cap and was really a short, pullable top gear.

The fix is a real 7-speed ladder — equal steps, short top window, tapering multiplier
(`PHOENIX_GEARBOX` in `tools/port_to_phoenix.py`, mirrored into the redscript virtual
gearbox so the HUD revs stay honest):

| gear | window (m/s) | tops | torque multiplier |
|---|---|---|---|
| 1 | 0 → 32 | 115 km/h | 0.78 |
| 2 | 29.8 → 40.9 | 147 | 0.72 |
| 3 | 38 → 52.2 | 188 | 0.665 |
| 4 | 48.5 → 66.6 | 240 | 0.61 |
| 5 | 61.9 → 85 | 306 | 0.56 |
| 6 | 79.1 → 108.6 | 391 | 0.53 |
| 7 | 101 → **138.89** | **500** | 0.50 |

Steps are 1.276–1.279× — the spread a seven-speed actually needs to reach 500 from a
sane first gear. No single gear has to double its speed any more.

Two more changes ride along, because they answer the other complaint and a different
question respectively:

Three more changes ride along in the same build:

| Change | From | To | Why |
|---|---|---|---|
| `turnUpdateMaxSpeedThreshold` / `…TurnMul` | 26 m/s / 0.33 | **45 m/s / 0.21** | the 572 km/h car's band: keep authority to 162 km/h, then cut to 21 %. Ours still handed over a third of full lock at 400+ |
| `airResistanceFactor` | 0.90 | **0.60** | second lever on the same wall; 0.66 is what the 572 km/h car uses |
| rear lateral/longitudinal grip | 2.00 / 1.85 | **1.70 / 1.68** | all five cars we have data for run the axles within 6 %; 25 % apart was the last unexplained source of yaw nervousness |
| `wheelTurnMaxSubPerSecond` | inherited from the 911 base | **150**, written out | the other four cars state it (135 / 140 / 170); a slow return to centre makes corrections ring |
| engine record: `flyWheelMomentOfInertia` 0.12, `finalGearTorqueDecimationScalor` 1.0, `gearChangeTime` 0.1, `gearChangeCooldown` 0.15, `fastR1GearChange` true, `wheelsResistanceRatio` 15 | inherited from the SuperSport base | **written out explicitly** | the 572 km/h car inherits *nothing* in its engine record. Ours inherited the entire half that governs how hard the last gear pulls — and a top-gear torque decimation we never chose |

That last row is the one nobody had looked at: our engine is `$base:
Vehicle.VehicleEngineData_4_SuperSport` plus four overrides, so the flywheel, the shift
timing and `finalGearTorqueDecimationScalor` all came from a car that is not supposed to
do 500 km/h. Nothing invisible is left there now.

Install after `git pull` (YAML **and** scripts — the redscript gear table changed too):

```powershell
$root = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" `
          "$root\r6\tweaks\phoenix\" -Force
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie\*" `
          "$root\r6\scripts\phoenix_aston_valkyrie\" -Force
```

Restart the game (TweakXL reads YAML at boot; CET reload alone does not take).

| Outcome | What it means | Next |
|---|---|---|
| **~500 or beyond** | the ladder was the wall | if it overshoots, raise `airResistanceFactor` in steps (0.60 → 0.70 → 0.80) until it sits at 500 |
| stalls **~390** (= new 6th) | the *next* ratio is still too tall for the available force | drop 7th's `minSpeed` (101 → 95) and raise its multiplier (0.50 → 0.56) |
| stalls **~300 again** | ratio and engine-record theories are both dead | it is the engine-level speed limiter (`docs/VEHICLE-MODEL.md` §5c) — that needs the RED4ext unlimiter, not YAML. Report it; we decide whether the Phoenix ships with that dependency |
| still wobbly at 400+ | steering band and grip symmetry are both now fixed, so the remaining suspects are downforce (1.40 vs 0.35-0.7 in every reference) and damping | report the speed it starts at; `stability-tweak.ps1` is the fallback |

## 3e. The experiment that ends the guessing: drive the OTHER cars

Every change to torque (×2.9), gear windows, drag (0.90 → 0.60) and the engine record has
moved the plateau by noise: ~300, ~330, 308. Numbers that ignore a 2.9× torque change are
not being limited by force. There are only two explanations left:

* the game clamps vehicle speed natively (`docs/VEHICLE-MODEL.md` §5c), or
* our physics records are not the ones the car is driving.

**Both are settled by one run in a car you already have installed.** Same protocol as §2 —
Auto Drive Enhanced at 100 %, long straight, hands off:

| Car | Its YAML says | If it reads this | Then |
|---|---|---|---|
| **Pagani Zonda Revo** | 180 km/h (last gear 50 m/s) | **~180** | physics applies normally in this install, and its YAML is structurally near-identical to ours (same 911 base, same inline record bases) — so the fault is something specific to the Phoenix |
| | | **~330** | inline/`$base` physics is being ignored by the install for this whole family of mods, ours included |
| **Koenigsegg Jesko Attack** | 283 km/h (last gear 78.5 m/s) | **~572** | nothing clamps the game; speed above 330 is reachable and our file is wrong |
| | | **~283** | the 572 number was never real (or was HUD-inflated) |
| | | **~330** | a native cap, exactly as the speed-unlimiter mod implies |

Two cars, two numbers, and the answer is unambiguous. No reinstall, no restart — just drive
them the way you drive the Phoenix and read the speedo.

**Shipped in the same build as this section:** the physics blocks are now *named records*
referenced from the vehicle (`vehEngineData: Vehicle.phoenix_amv_engine`, matching the
Quadra and the Jesko), and the gears declare `$type: gamedataVehicleGear_Record` instead of
inheriting from `..._quadra_turbo_r_inline10…14`. Values are unchanged; the shape no longer
depends on the position of somebody else's record.

## 3n. The control result: 278 km/h, and a display hypothesis (2026-11-24)

With **every** physics value and the whole vehicle record copied from the Jesko - engine, gears,
drive model, helpers, wheels, `curvesPath` - the car tops out at **278 km/h**. Twice, before and
after the vehicle record was made explicit.

The Jesko, on the identical records, is reported at **500+**. That is not a data difference, so
the data is no longer the suspect. Look at the ratios instead:

| car | declared top gear | dash reading | dash / declared |
|---|---|---|---|
| Zonda | 180 km/h | 355 | **1.97×** |
| Jesko | 283 km/h | 500+ | **1.77×** |
| **Phoenix** | **283 km/h** | **278** | **0.98×** |

Both reference cars read *exactly* a multiple of their own declared top speed. Our car reads
its declared top speed, because **our dashboard is the only one in this install that does not go
through the game's `speed_to_multiplier` curve** - `phoenix_aston_valkyrie.reds` writes
`SpeedValue × 3.6` straight into the HUD, and its own comment says the game inflates the number
at high speed.

So the leading hypothesis is that nothing was ever capped: the game stops cars at their declared
top gear, the two "fast" cars are reporting an inflated number, and 278 km/h real is *exactly*
what a 500 km/h dash reading is made of here - 278 × 1.77 is 492.

### The test that settles it without touching the display

Time, not speed. Time is display-independent.

| If the car really does | 1 km takes |
|---|---|
| 278 km/h | **12.9 s** |
| 500 km/h | 7.2 s |

Run the same stretch in both cars - the Jesko and the Phoenix - from a rolling start, and time
it (the game's own trip/distance readout works, or a phone stopwatch). If the Jesko is genuinely
77 % faster it will be unmistakable. If they arrive together, the 500 was a number on a screen.

The long north-south straight out of the city works, or any highway between two junctions with a
rolling start.

### MEASURED (2026-11-24, user): the display was the answer

Distance/timed runs over 1 km, rolling start, same stretch, same session:

| car | 1 km | real speed | dash reading | inflate |
|---|---|---|---|---|
| Jesko | **13 s** | **277 km/h** | 572 | **2.07x** |
| Phoenix (Jesko control build) | **13 s** | **277 km/h** | 278 | 1.00x |

**The reference car does not do 500 km/h. It does 277 km/h and displays 572.** Our control
build does the same 277 km/h - the physics copy was correct and complete, and the two cars are
equal in real terms. The whole 278-vs-500 gap was the game's `speed_to_multiplier` display curve,
which the Phoenix is the only car in the install to bypass (see `phoenix_aston_valkyrie.reds`).

Consequences:
- **There is no speed cap in TweakDB.** Nothing clipped us at 278; 278 *is* the Jesko's real
  top speed with those records.
- **"500 km/h" is a display value.** It corresponds to ~242 km/h real (500 / 2.07).
- **Genuinely 500 km/h real** is a different project: drag-dominated power scales with v^3, so
  500 real needs ~2.9x the driving force we had at the 350 km/h real of v9 (`3fd6d17`), i.e.
  ~1,800-2,000 hp-equivalent at CdA ~0.9 - Chiron territory, not hypercar-copy territory. Our
  earlier real-physics anchor (2,000 hp + CdA 0.95 -> 493 km/h) says the game's force model can
  represent it, but the 350 km/h "brake" event of v9 has to be cracked first.

### The curve, measured on a vanilla car too

A **vanilla** vehicle (Yaiba Semimaru, not a mod, not ours) reports **372** km/h and actually does
**160**: 2.33x. With the two known points the display curve fits a clean power law -

    displayed = 6.96 * real^0.784

| real km/h | old dial | multiplier |
|---|---|---|
| 160 | 372 | 2.33x |
| 200 | 443 | 2.22x |
| 233 | 499 | 2.14x |
| 277 | 572 | 2.06x |
| 350 | 687 | 1.96x |
| 500 | 909 | 1.82x |

- It is **not** near 1.0 at low speed (an earlier guess in this file): at a car's 160 km/h it is
  still 2.33x. The curve does not inflate harder as speed rises, it **compresses the top end** -
  roughly double everywhere, a little less the faster you go. Below ~150 km/h we have no data.
- **A real 233 km/h displays as 500.** The car already does 277 real, which the game's own HUD
  would print as 572 - the same number the Jesko shows, since it is the same machine underneath.
- That also fixes the shape of the build job: with a truthful dashboard, a dial reading of 500
  means **500 km/h real**, not 233.

### Delivered: a TRUE speedometer, for every vehicle

`phoenix_aston_valkyrie.reds` already bypassed the display curve, but only for our car
("diger araclara dokunmaz"). `TRUE_SPEEDO_ALL_VEHICLES` (default on, `tools/port_to_phoenix.py`)
widens the guard to `IsDefined(vehicle)`, so **every** car you drive reports `SpeedValue x 3.6`
- the speed it is actually doing. The game's imperial setting shows the raw **m/s** instead of
miles (`MPH_MODE_SHOWS_MPS`), because the imperial setting is not used here and m/s is the unit
every number in this repo is quoted in. Our dash, rev LEDs and audio
stay gated on `PhoenixAMV_IsTarget`. Flip the flag to `False` to return to Phoenix-only.

Read a stock car's dial now and you see what the curve was hiding: a car that "does 210" is
usually doing ~170, and everything above that was inflation.

Original hypothesis section follows.

### If the display is the answer

Then the fix is one file: make the Phoenix's HUD use the game's own speed math like every other
car, and the dash reads ~500 at 278 km/h real. The physical car is already as fast as the reference
- and the remaining work is the wobble, not the top end.

## 3m. THE CONTROL: the Jesko's physics, copied byte for byte (2026-11-24)

Instruction: *"copy the jesko curves exactly, precisely. don't innovate, we need a control."*

Done, and done literally: `tools/port_to_phoenix.py` now **reads
`reference/vehicles/jesko_attack.yaml` and copies its record blocks as raw text**, renaming only
the record IDs (`Vehicle.jesko_attack_X` → `Vehicle.phoenix_amv_X`). A test
(`test_every_record_is_byte_identical_to_the_reference`) asserts that every copied block appears
in the deliverable unchanged, so this cannot drift into an "adaptive" build by accident.

What is now the reference car's, not ours:

| | value |
|---|---|
| Engine | 1000 torque, 7900 rpm, 900 idle, `large_balanced_turbo`, 0.12 flywheel, 150 engine braking |
| Gearbox | its 8 gears verbatim — top gear 62.47 → **78.5 m/s (283 km/h declared)** |
| Drivetrain | **RWD** (its wheel roles: front not driven, handbrake rear only) |
| Drive model | all 51 fields: drag 0.66, downforce 0.7, mass 1800, inertia 2600/780/3000, grip 1.30/1.28, brakes 1165/785, damping 3000/3200 + 3300/3500, swaybar 18/15, steering 137/170, `turningRollFactor` 1, `useAlternativeTurnUpdate` |
| Helpers | its seven helper records and its burnout record, values included |
| Wheels | its dimensions (tireRadius 0.3798 / 0.3988) and its two driving presets |

**The vehicle record too (added the same day).** Ours still carried
`$base: Vehicle.v_sport2_porsche_911turbo`, which is not a physics record but does carry
`curvesPath` (`default_car.vehcurveset`), `driving` / `drivingParamsGeneric` / `drivingParamsPanic`
/ `drivingParamsRace`, `crowdMemberSettings`, camera manager params, impact and crowd settings —
none of which any drive-model field can override. It is now `$type: gamedataVehicle_Record` with
the reference's 91 fields written out and no `$base` at all.

Ours: mesh, entity, textures, paint, name, icons, audio resource, scanner card, dealer entry,
driver animation rig (`porscheCorrectivePose`), and the camera/FPP rigs.

**This is a measurement, not a tune. Two outcomes, both informative:**

| Result | What it proves |
|---|---|
| **runs to ~500 km/h like the Jesko** | our numbers were the problem all along, and the last four builds were chasing a ladder fault in a car that was fine |
| **stops where the Jesko does not (283 or ~350)** | the physics is not the difference — the meshes/entity/base are — and no further tuning of these fields can fix it |

If it is the second, the next question is what else the Phoenix inherits that the Jesko does not:
`$base: Vehicle.v_sport2_porsche_911turbo` on the vehicle record, its entity, and the data
package. That is where a cut-off would live that no drive-model value can reach.

## 3l. The Jesko map (2026-11-24)

Requested: *"why not take the Jesko - that works - and map to the Phoenix, then tune grip to
improve it?"* Correct instinct, and reading its file settled two things outright.

**1. The 0.90 shift fraction is now measured, not inferred.** Every one of the Jesko's six gear
floors is exactly 0.90 × the previous gear's top speed, to 0.01 m/s:

| | floor | 0.90 × previous top |
|---|---|---|
| gear 2 | 21.60 | 0.90 × 24.00 = 21.60 |
| gear 3 | 29.78 | 0.90 × 33.08 = 29.77 |
| gear 4 | 37.95 | 0.90 × 42.17 = 37.95 |
| gear 5 | 46.12 | 0.90 × 51.25 = 46.12 |
| gear 6 | 54.30 | 0.90 × 60.33 = 54.30 |
| gear 7 | 62.47 | 0.90 × 69.42 = 62.48 |

**2. Our ladder shape was wrong in a second way.** The Jesko's steps *taper* toward the top
(1.378, 1.275, 1.215, 1.177, 1.151, 1.131); ours were a flat 1.20. Ours are now its ladder
scaled ×1.769 so the top gear lands on 138.89 m/s:

| gear | m/s | km/h | torque mult |
|---|---|---|---|
| 1 | 0 → 42.46 | 0 → 153 | 1.000 |
| 2 | 37.79 → 58.53 | 136 → 211 | 1.000 |
| 3 | 52.09 → 74.61 | 188 → 269 | 0.670 |
| 4 | 66.40 → 90.68 | 239 → 326 | 0.494 |
| 5 | 80.71 → 106.74 | 291 → 384 | 0.387 |
| 6 | 95.00 → 122.82 | 342 → 442 | 0.316 |
| 7 | 109.31 → 138.89 | 393 → **500** | 0.265 |

**3. The chassis we were inheriting is now written out.** The Jesko declares ~40 drive-model
fields the 911 base was supplying silently — `turningRollFactor` (we had 0, it runs 1),
`antiSwaybarDampingScalor`, `slipAngleCurveScale`, `slipRatioCurveScale`,
`tireRollingResistanceCoef`, `brakingFrictionFactor`, `useAlternativeTurnUpdate`, weight-transfer
factors, the full `turnUpdate*` set. All copied. Grip is the one place we aim **above** it:
lateral **1.46 / 1.44** against its 1.30 / 1.28, longitudinal 1.06 / 1.10 against 0.95 / 0.98.

| Outcome | Meaning |
|---|---|
| **500+** | the inherited chassis was the problem all along; we tune from a working base |
| still ~350, but the wobble is gone | the chassis map fixed the driving, not the speed — then it is drag, and `airResistanceFactor` 0.66 is the dial |
| worse everywhere | revert in one command: `git revert` the map commit; the 3fd6d17 build is intact behind it |

## 3k. "It just dies": the limiter was 100 rpm above the gear ceiling

Reported after 3j: manual driving, no ADE, and the car **dies** instead of braking. The ladder
in 3j was geometrically right but had two structural faults left:

| Fault | Numbers | Effect |
|---|---|---|
| **no limiter headroom** | `maxRPM` 7900 vs gear ceiling 7800 | a 100 rpm gap, so the rev limiter fires before the next shift lands. That is a power cut, and it reads as "the car just dies" |
| **overlap only valid at 0.90** | floors 5300, window 1.47 | fine if the shift is at 0.90 of range and *negative* below that. The 6→7 overlap was 3.4 m/s — one bad shift and the hole is back |

**Rebuilt on three rules that leave no room for either failure:**

1. **Overlap from 0.80, not 0.90.** `minSpeed[next] <= 0.80 x maxSpeed[this]` → window
   ≥ step / 0.80. With step **1.20** (LMH-real; the real car's Xtrac is 1.22–1.28) and floors
   at **5000 rpm**, the window is **1.52** and every shift has +0.5 to +12.8 m/s of margin.
2. **600 rpm of limiter headroom.** Gear ceilings at **7600**, engine `maxRPM` at **8200**. The
   limiter now cannot fire before a shift under any circumstances.
3. **Force where it is needed.** Gears 6 and 7 at **0.66** instead of 0.53/0.50, and the torque
   curve swapped to **`large_balanced_na`** — the real car is a naturally aspirated V12, and NA
   holds torque at the top of the range, which is where a 500 km/h run lives.

| gear | m/s | km/h | overlap @0.80 |
|---|---|---|---|
| 1 | 0 → 46.51 | 0 → 167 | — |
| 2 | 36.7 → 55.82 | 132 → 201 | +0.5 |
| 3 | 44.1 → 66.98 | 159 → 241 | +0.6 |
| 4 | 52.9 → 80.38 | 190 → 289 | +0.7 |
| 5 | 63.5 → 96.45 | 228 → 347 | +0.8 |
| 6 | 76.1 → 115.74 | 274 → 417 | +1.0 |
| 7 | 91.4 → 138.89 | **329 → 500** | +1.2 |

If it still dies, the two changes to bisect are, in order: the curve (one line, back to
inherited) and the multipliers (6/7 back to 0.53/0.50).

## 3j. SOLVED: it was the gearbox braking the car, not the brakes (2026-11-24)

Result of the ADE test: **it brakes at 350 km/h at 100 %, 85 % and 50 % alike.** So ADE is not
capping anything — the point does not move with the setting, which means it is in the car.

The arithmetic names it exactly. 350 km/h = 97.2 m/s, and our gear 6 spans 79.1 → 108.6 m/s at
5 680 → 7 800 rpm, so it upshifts at 0.90 × its range, i.e. at **97.7 m/s (352 km/h)**. Gear 7's
window started at **101.0 m/s (364 km/h)** — twelve km/h too high. The box dropped the clutch
into a gear the car was too slow for, the speed mapped *below* gear 7's 5 670 rpm floor, the
engine produced nothing, and drag did the rest. It was never a brake: it was engine braking into
a void, at every shift, and only the top one was big enough to be fatal.

**The rule, which is now a test:** the engine upshifts at ~0.90 of a gear's range, so

```
minEngineRPM / maxEngineRPM  <=  0.90 / step     (i.e. window >= step / 0.90 = 1.42 at 1.278)
```

Ours was 5 680 / 7 800 = **0.728**, above the 0.704 limit — a hole at every one of the six
shifts. Floors are now **5 300 rpm**: window 1.47, and a 1.0–3.4 m/s overlap at every step.

| Outcome | Meaning |
|---|---|
| pulls through 400+ | the ladder was the last wall. Trim drag to land on 500 |
| brakes again at ~390 | 7th's own shift point; give 7th more range (its step to nowhere) |
| brakes at a new, higher number | each plateau so far has been a shift boundary — tell me the number and I will read it the same way |

## 3i. Is it the car, or is it Auto Drive? (and a units landmine)

Asked 2026-11-24: *"is it because of some definition not letting ADE drive faster than 1x max
speed?"*

**In that form, no — but the evidence is weaker than it looks, and here is why.**

Ruled-out version: ADE capping at 1× the vehicle's declared top gear. Under the same ADE at
100 %, the Zonda reached 355 km/h on a table that says 180 (1.97×) and the Jesko 500+ on 283
(1.77×). A cap at 1× declared would have stopped both dead at 180 and 283.

**The units landmine that weakens all of it:** this car's dash shows `SpeedValue × 3.6`, raw
km/h, because `phoenix_aston_valkyrie.reds` bypasses the game's `speed_to_multiplier` display
curve *for this vehicle only*. Every vanilla car goes through that curve, which inflates the
number as speed rises. So "Jesko 500+ displayed" is not "500 km/h real", and comparing it to
our honest 350 is comparing an inflated number with a true one. The rpm evidence in §3g is
unaffected (rpm is rpm), but no cross-car *speed* comparison in this document is trustworthy
until the inflation curve is known.

**Three runs that settle it** (in order of value):

| # | Test | If the brake point… |
|---|---|---|
| A | ADE max speed **50 %** instead of 100 % | **halves** → ADE is capping, and it scales with the setting. The car is fine |
| B | **manual** full throttle, no ADE, long straight | disappears → ADE was braking. Still happens → the car does it |
| C | ADE 100 % in the **Zonda** | still overshoots its 180 table → ADE does not read the table; the Phoenix cap would have to come from something the Zonda lacks |

Test A is the cheapest and the most decisive, because it turns ADE's own setting into the
measuring instrument.

## 3h. The car braking itself at 350 (2026-11-24)

Reported right after 3g worked: *"it hits 350+ but as soon as it does it hits the brakes,
brakes are too good."* Two things, and the five-car table named both:

| Cause | Evidence |
|---|---|
| **brakes too strong** | ours were 1850 / 1550 Nm — the highest of all five cars (next: 1410/1200; Jesko 1165/785; Zonda 1350/1150; Quadra 1203/802). Handbrake was 2600 against 1600 (Jesko) and 1156 (Quadra) |
| **engine braking inherited, then doubled by AWD** | `resistanceTorque` — documented as "the decrease in torque during throttle lift-off" — was never written in our engine record, so it came from the SuperSport base with an unknown value. In 3f we made **all four wheels driven**, so that unseen brake now acts through four wheels instead of two. Auto Drive lifts at the end of a fast section; that is the moment the car "hits the brakes" by itself |

**Shipped:** `maxBrakingTorque` → **1400 / 1150**, `handbrakeBrakingTorque` → **1600**,
`resistanceTorque` → **150** (explicit, the Jesko's value).

If it still brakes hard, the remaining suspect is the shift itself: tell me **which gear
number the dash shows when it happens** — if it is 7, the box is upshifting into a gear whose
window starts above the current speed and the game is retarding rather than accelerating.

## 3g. SUPERSEDED — "the engine was revving past its curve"

> **Corrected 2026-11-24.** This section's theory is wrong and is kept only as a record of it.
> A `.curveset` stores `x` as *normalised* RPM (0→1) and `y` as torque fraction, so a curve can
> never impose an absolute rpm ceiling — `maxRPM` stretches it. The plateaus at 308 and 352 km/h
> are explained by the shift-hole (§3j), not by a curve ending. What survived from this
> investigation is the shift point (0.90 of a gear's range), which is now an invariant test.
> See [`TUNING-FROM-REAL-RACING.md`](TUNING-FROM-REAL-RACING.md) §2 and §6.

The control run answered the big question first: **the Zonda reaches 355 km/h from a gear
table that says 180, and the Jesko passes 500 from a table that says 283.** Nothing in this
install clamps speed, and gear `maxSpeed` is not a ceiling — those two cars run ~1.8-2× past
their own declared top gear.

That left our car's plateau with a very specific address. Two runs, two different gearboxes:

| Run | Speed | Gear it was in | RPM at that speed |
|---|---|---|---|
| previous ladder | ~300 km/h | 7th (77 → 138.89 m/s, 7800 → 9950 rpm) | **~8 020 rpm** |
| installed ladder | 308 km/h | 6th (79.1 → 108.6 m/s, 7250 → 9950 rpm) | **~7 845 rpm** |

Different ratios, same rpm. **That is the torque curve, not the gearing.** Our engine record
claimed `maxRPM: 10100` but inherited the SuperSport `gearCurvesPath`; no curve in the game
reaches 10 100, and past the end of a curve the engine produces nothing. Both reference cars
write their own curve and both top out near 7 600-7 900 rpm.

**Shipped:** `maxRPM` 10100 → **7900**, and every forward gear re-geared to finish at
**7 800 rpm**, so 138.89 m/s now lands inside the curve instead of past it.

| Outcome | Meaning |
|---|---|
| **~500 or beyond** | the curve was the wall. Trim drag so it lands on 500 |
| ~390 / ~310 again | read the revs where it stops — if it is still ~7 800, the curve ends there and we need a different `gearCurvesPath`; tell me the number and I will pick a curve that reaches higher |
| slower but stable | we lost speed to the rpm drop; raise the multipliers before touching anything else |

## 3f. Wobble build: AWD + downforce + damping (shipped 2026-11-24)

Three changes, all aimed at the wobble, none of them aimed at top speed. If the car gets
stable but no faster, that is the expected result and it is progress.

| Change | Was | Now | Why this one |
|---|---|---|---|
| drivetrain | RWD | **AWD** (`DRIVETRAIN` in the port tool) | Auto Drive holds **100 % throttle**; 3824 Nm through two tyres keeps them at the friction limit for the whole run, and that is where yaw instability lives. Four driven wheels halve the longitudinal demand per tyre. It cannot raise top speed — drag, gearing and any native cap still own that |
| `maxSpeedFactorGround` | 1.40 | **0.70** | twice every car we have data for (0.35 / 0.6 / 0.7). Excessive downforce through stiff springs is a porpoising source on a bumpy road, and it costs drag |
| `springReboundDamping` / `…LowRate` | 4300/4500 and 5000/2900 | **3750/3900** and **3600/3600** | the stock pair was the real outlier: front low-rate rebound 5000 against a 2900 bound (1.72×), while the rear used 2900 for the same part (1.00×). Every reference car sits near 1.25× |

`docs/VEHICLE-COMPARISON.md` has all five cars side by side, including the new damping rows.

**AWD is a diagnosis, not a destination.** The real AMR-LMH is rear-drive. If AWD fixes the
weave, we know the cause is power oversteer — and the authentic cure is rear grip and torque
delivery, then flip `DRIVETRAIN` back to `"rwd"`. If it changes nothing, the wobble is
aerodynamic or suspension and AWD was never the answer.

Read the result in this order:

| What you see | Meaning |
|---|---|
| stable, still ~310 | wobble was drivetrain/aero — now tune grip and put RWD back |
| stable **and** faster | downforce was costing speed as well as stability |
| still wobbly | it is not power oversteer. Next: `RotationLimiter.maxAngularSpeedRad` (2.6 → ~1.2), which caps how fast the car can yaw at all |
| worse / understeers | AWD took too much away — say so and we revert to RWD with the other two kept |

## 4. If it wobbles while autodriving

That is the useful result of removing human input: **any** yaw oscillation is now
attributable to the physics, not to your thumbs. The cause is almost certainly steering
authority that was tuned for 330 km/h:

At 500 km/h the same wheel angle generates roughly **2.3×** the lateral acceleration it
does at 330, so a third of full authority is a lot. **The high-speed band is now in the
deliverable** (§3d: threshold 45 m/s, multiplier 0.21), so the script below is no longer
the first move — it is the fallback if the shipped band is still not enough. It works on
the game's copy of the YAML (backup kept, repo untouched, reversible):

```powershell
cd $HOME\f1-cyberpunk-mod
powershell -ExecutionPolicy Bypass -File .\tools\stability-tweak.ps1
```

It changes 94 → **64**, threshold 26 → **30**, mul 0.33 → **0.12**, prints the three lines
back, and needs a game restart (TweakXL reads YAML at boot). Undo with `-Revert`.

If the car then tracks straight but feels numb at low speed, the honest fix is a
speed-dependent curve rather than one number, and the values above are the starting point
for that second pass.

## 5. Report

One line per row of §3, plus one sentence per surprise ("held 7th at 470, never reached
the wall"; "yaw oscillation started at ~350 km/h and grew"). That is what turns v2 into a
final tune instead of a guess.
