# Fast car mods, and what they actually deliver

Checked 2026-11-23. Requirements and versions change; the arithmetic in §1 does not.

## 1. First, the ceiling: 360 km/h. Nothing exceeds it.

This repo reverse-engineered the vehicle integrator: `vehicle::RigidBody::Recalculate`
(hash `593628708`) returns `FP_INFINITE` for the whole body once `speedSquared >= 10000.0`, i.e.
**100.0 m/s**. It is native C++, reached from no tweak, no redscript and no TweakXL file
(`docs/SPEED-CAP.md`).

So when a car mod advertises 500 km/h, one of three things is happening:

| what the page says | what the engine does |
|---|---|
| "top speed 400 km/h" | gear `maxSpeed` is set high, the car accelerates to **≤ 360**, then sits there |
| "500 km/h hypercar" | same — the number is the *tweak*, not the result |
| "top speed about 350" | honest, and under the wall, so it is actually reachable |

**The practical fastest a car can go in this game is ~355–360 km/h**, and only if it has enough
thrust to reach the wall and low enough drag not to stop short of it. Anything past that on a Nexus
page is a value in a YAML, not a speed.

## 2. The mods that change how speed *feels*

| mod | author | size | what it really changes | true top speed | 2.5? | our Phoenix |
|---|---|---|---|---|---|---|
| **Authentic Shift** (6823) | imbamakaber | 4 797 end. / 793 k DL | gearbox RPM curves only — **no power, speed, grip or weight change**. Runs once at load, zero runtime cost | **none** | yes, 16 Nov 2026 | no conflict |
| **＋ Realistic Vehicle Physics Collection** (38670) | imbamakaber | new, v0.9.4-beta | 105 vanilla/PL cars given **real** weight, power, brakes, grip, gearbox, top speed, downforce 100–300 km/h, real gravity in the air, **no launch boost, no slope assist** | **real-world values** | yes, 16 Nov 2026 | **modded cars are left alone** → Phoenix untouched |
| **Cyber Vehicle Overhaul** (3016) | Erok / E3roKK | 18 556 end. / 1.27 M DL | per-vehicle overhaul of top speed, gearing, torque, brakes, suspension, tyres; multipliers in `init.lua` | raised, then the wall or drag decides | v2.1, Jul 2025 — verify | only vanilla cars listed → no overlap |
| **GTA 2077** (30578) | Mertkso77 | 141 end. / 10.7 k DL | GTA-V arcade handling, keyboard input smoothing bypassed, instant response | unchanged | Jun 2026 | no overlap |
| **Better Vehicle Handling** (210) | RB / CalinZ2 | long-running | one `.ini` of handling variables, no code at all → patch-proof | unchanged | author: still works | global ini |

### The measured numbers, from the Collection's own page

This is the only vehicle mod in the ecosystem that publishes a calibration table against **road
tests of real cars**, done on a 5 km flat platform:

| test | real car | in game |
|---|---|---|
| 100 kph → stop | McLaren 750S **33.0 m** | Caliburn **34.3 m** |
| 100 kph → stop | Mustang GT **36.8 m** | Type-66 **36.2 m** |
| 0 → 100 kph | McLaren 750S **39 m** | Riptide **41 m** |
| cornering @100 | Civic **0.87 g** | Hella **0.87 g** |
| cornering @100 | McLaren **1.13 g** | Riptide **1.11 g** |

Cornering within 0.02 g, braking within 1.3 m. That is a *measurement*, not a claim.

> **Speedometer warning:** with the Collection on, the game's speedo shows **up to twice the real
> speed**. Use the Authentic Shift GUI. This is also a reminder that the stock dashboard is a
> derived number, not the physics velocity — which is why our dash reads the vehicle body directly.

**The reason is the same in both cases, and we have measured it.** The game feeds the HUD speed
through a `speed_to_multiplier` curve, and at the top of the range that curve is at roughly **2x**:
this repo's own HUD wrapper was written after seeing **277 km/h displayed as 572**. Authentic
Shift's "up to twice the real speed" is that curve. It also explains every "500 km/h car mod" that
never reaches 360 — the number on the dial, not the integrator.

Our `phoenix_aston_valkyrie.reds` wraps `hudCarController.OnSpeedValueChanged` and writes the true
figure instead, and it does so for **every** vehicle: `PhoenixAMV_TrueSpeedo()` gates on
`IsDefined(vehicle)`, not on the Phoenix record. Only the wheel screen, LED and audio stay
Aston-only. So with the scripts installed, the HUD reads physics speed in any car; without them,
the curve is back.

**Correction, measured in a 599 XX (build 900035).** The first version of that wrapper wrote
`AbsF(speedValue)` - the value the callback is handed. On a car timed at **17 s/km (58.8 m/s)** the
dial read **110-117**, i.e. **1.92x**. The callback argument has already been through
`speed_to_multiplier`, so writing it as m/s reprints the curve in the wrong unit; 1.8x-2.1x
depending on speed. The wrapper now reads `PhoenixAMV_FwdSpeed(this.m_activeVehicle)` - the same body
velocity the wheel screen has always used - so it cannot be handed a derived number.
`apply_hud_body_speed()` in `tools/port_to_phoenix.py` performs the substitution at port time.

## 3. Real cars, from the authors who are actually consistent

Content mods set their own `maxSpeed`, so their top speed is whatever the author typed — and then
the wall or drag applies. The authors worth trusting, by download volume and update cadence:

| author | what | why |
|---|---|---|
| **SDH0** | Ferrari F40 (147 k), F40 ZEPHYR, BMW M4 CS (185 k) | CrystalCoat + Live Tuning + Garage support, frequent updates |
| **xa1res** | Lamborghini Sesto Elemento, Countach Liberty Walk, Porsche 992 GT3 R | 140+ colours, custom sounds, current |
| **Morpheus9436** | Pagani Huayra (126 k), Porsche 718 GT4, Toyota GR GT | standalone, CrystalCoat |
| **yellingintothevoid** | Skyline R33 (314 k), R32 — 80+ tuning parts | the most complete JDM conversions |
| **MAXSA5** | Huracán EVO (6.1 k, five bodies + police/weaponised) | current, Virtual Car Dealer |
| **BATOUFL** | BMW M5 E60 (V10), Renault Clio V6 | real interiors, working gauges |

Framework: **Virtual Car Dealer** (DJ_Kovrik, 39 k endorsements) — how you buy/own them.

## 4. What I would actually install, in this order

Recommendation depends on what the speed is *for*. Given this repo's history — measuring a hold at
95 m/s on a known road, distrusting the speedometer, wanting the car to stop feeling floaty —
three of these are directly on target and the rest are toys.

**The measurement stack** (this is the one I'd push):

1. **Authentic Shift 2.26.9** — stock power, stock speed, only the RPM curves. Cost: a load-time
   pass, nothing at runtime.
2. **Authentic Shift GUI** (38669) — a **real speedometer**, G-meter, and it is the only in-game
   readout that shows true speed when other mods rescale it. Pairs with the dash we built.
3. **Vehicle Test Platform** (38671) — **5 km of flat road in the sky**, purpose-built for flat-out,
   stop and corner tests. That replaces route A *and* removes terrain from the measurement.
4. **Realistic Vehicle Physics Collection** — 105 cars with real numbers, and it strips the launch
   boost and **the slope assist**, which is the "help up a slope" this repo has been fighting in
   the gear ladder all along.

**The fun stack**, if the goal is just to enjoy driving fast:

1. **Cyber Vehicle Overhaul** — the single biggest "every car in the game is now better and faster"
   step, and everything is tunable in `init.lua` (gear speed multiplier, torque, brakes).
2. **GTA 2077** — arcade handling for keyboard, no fighting the car at 300 km/h.
3. **One hero car** — Huracán EVO, 992 GT3 R, or the Skyline R33 depending on taste.

Do **not** stack CVO and the Authentic Shift Collection: one overwrites per-vehicle performance
values, the other applies a profile at load, and whichever lands second wins on the cars both touch.
Pick a philosophy, not both.

## 6. Actual cars

Standalone add-ons, from the authors who keep a catalogue rather than a one-off. In-game top speed
is `min(what the author typed, 360)` — see §1. The real-world column is the real car's own figure,
which is why so many of these end up identical in game.

| car | author | traction | uploaded | real vmax | **in game** |
|---|---|---|---|---|---|
| **Rimac Nevera** | aalexbug | EV, 4 motors | Apr 2024 | 412 km/h | **360** — reaches it fastest |
| **Koenigsegg Jesko Absolut** | aalexbug | RWD | Apr 2024 | listed >480 | **360** |
| **Bugatti Chiron SuperSport** | aalexbug | AWD | Dec 2023 | 440 km/h | **360** |
| **Koenigsegg Jesko Attack** | bob1479512 | RWD | Oct 2026 | ~480 | **360** — but see CAR-MODLIST: this is our reference car, and `STABILITY.md` ranks its chassis worst of three (63/77 vs the Aston's 80/85) |
| **Bugatti Chiron Pur Sport** | aalexbug | AWD | Mar 2024 | 350 km/h | **350** — under the wall |
| **Pagani Huayra** | Morpheus9436 | RWD | May 2025 | 383 km/h | **360** |
| **Lamborghini Sesto Elemento** | xa1res | AWD | Nov 2026 | 355 km/h | **355** |
| **Lamborghini Huracán EVO** | MAXSA5 | AWD | Nov 2026 | 325 km/h | **325** |
| **Ferrari F40** | SDH0 | RWD | 2025 | 324 km/h | **324** |
| **McLaren Senna** | Morpheus9436 | RWD | Dec 2024 | 340 km/h | **340** |
| **Porsche 992 GT3 R** | xa1res | RWD race car | Nov 2026 | ~285 km/h | **285** |
| **KTM X-BOW GTX** | aalexbug | RWD, 1000 kg | 2024 | ~300 km/h | **300** |

### Why the top of that list is a lie you should ignore

Four cars read "360" because the engine stops them there, not because the mod is slow. **A Chiron and
a Jesko have the same top speed in this game.** What separates them is:

1. **How fast they get to the wall** — thrust vs drag. The Nevera's four motors and AWD put it there
   in the shortest distance; a RWD Jesko spends its advantage spinning.
2. **What it does at 300+** — this is where the good ones earn it. The Jesko Attack's changelog
   explicitly retunes steering for high speed ("the steering wheel turns less at high speed");
   the GT3 R and Senna have actual downforce models.
3. **Whether the gearbox hunts at the top** — the same failure this repo spent weeks on. A car with
   7 usable ratios and a ceiling above its drag limit holds; one geared to the wall sits on it.

That is the recommendation: **Nevera for the pull, Jesko Attack for the high-speed manners, 992 GT3 R
or Senna for a car that actually has downforce.** Skip anything whose page sells a number above 360 —
it is selling you a YAML field.

### Patch compatibility, honestly

aalexbug's catalogue is 2023–24, i.e. pre-2.5. Add-on cars are ArchiveXL archives plus TweakXL
records, so most still load, but nothing on the page promises 2.5. The 2026 uploads (Jesko Attack,
Huracán EVO, Sesto Elemento, 992 GT3 R) are current-patch by construction. Test one 2023 car before
installing five.

See also: **[CAR-MODLIST.md](CAR-MODLIST.md)** — cars only, filtered to mods updated on or after
22 Oct 2026 (i.e. under 2.5), with the same wall applied to their claimed speeds.

## 7. What none of them fix

- **The 360 km/h wall.** No mod on Nexus can lift it without native code (`docs/BYPASS-PLAN.md` has
  the parked research; the 2025 unlimiter crashes the game on load).
- **ADE's 119 m stopping radius.** That is inside ADE, not the car (`docs/ADE-INTERFACE.md`).
- **A speedometer that disagrees with physics.** Ours reads the body; the stock dial does not.
