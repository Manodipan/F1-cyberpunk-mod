# Phoenix True Speedometer

A speedometer mod with no car in it. It replaces the HUD speed number with the vehicle's actual
velocity, in the unit you choose, at runtime, from a Mod Settings tab.

```
r6\scripts\phoenix_true_speedometer\phoenix_true_speedometer.reds
```

Requires **Mod Settings** (which ADE already needs) and obviously redscript. Nothing else: no
ArchiveXL, no TweakXL, no CET, no tweak file.

## Why the number needs replacing at all

The game does not put velocity on the HUD. It puts `speed_to_multiplier(velocity)`, a curve that is
roughly linear at town speeds and about **2× at the top**. Two measurements from this repo:

| real | dial showed | ratio |
|---|---|---|
| 277 km/h | 572 | 2.06× |
| 58.8 m/s (17 s per km) | 110–117 | 1.92× |

That second one is the reason this mod exists in its current form. The first fix wrote the value the
HUD callback is handed — but that value has *already* been through the curve, so it reprinted the
curve in a different unit. This mod ignores the callback's value entirely and reads
`Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward())` — the body — which the game
never derives.

## Two slots

Both slots are applied to the same body velocity, and both are shown **with their unit spelled out**:

```
58.8 m/s | 212 km/h
```

Nothing has to be remembered: the label belongs to the number that produced it. Slot 2's number is
never a mislabelled copy of slot 1's, because each slot converts from m/s independently.

A **custom** slot cannot be named, so it labels itself with the multiplier it is using - `58.8 x0.06`
for km/min. That is the honest version of "whatever unit I want": the HUD shows the arithmetic.

Turn the labels off (**Print the unit next to the number**) if the string overflows your HUD scale;
you get `58.8 | 212` back.

| setting | what it does |
|---|---|
| **Slot 1 – unit** | m/s · km/h · mph · knots · ft/s · **Mach** · custom |
| **Slot 1 – custom multiplier** | how many of *your* unit per m/s, used when slot 1 is custom |
| **Slot 2 – show a second unit** | off = one number only |
| **Slot 2 – unit** | same seven options |
| **Slot 2 – custom multiplier** | free multiplier for slot 2 |
| **Print the unit next to the number** | `58.8 m/s \| 212 km/h` on, `58.8 \| 212` off |

Digits are not a setting: every number carries **three significant digits**, or **whole numbers
above 100**.

| reading | shown | why |
|---|---|---|
| 212.4 m/s | `212` | over 100 → whole |
| 58.83 m/s | `58.8` | 3 sig |
| 9.876 m/s | `9.88` | 3 sig |
| Mach 0.1714 | `0.171` | 3 sig |
| Mach 0.01714 | `0.0171` | 3 sig, zero-padded |

That is the rule the wheel is read at, not a preference: at three digits the last one is real, at one
decimal on a Mach number it is noise.
| **Only in player vehicles** | leaves passenger seats, cutscenes and AVs alone |

### In the tooltips

Every setting carries its own reference table, so the menu is usable without this document:

- **Slot 1 / Slot 2 – unit** → `m/s = x1.0 | km/h = x3.6 | mph = x2.23694 | knots = x1.94384 | ft/s = x3.28084`
- **custom multiplier** → the same table plus `km/min 0.06 | yards/s 1.09361 | furlongs/fortnight 6012.9 | Mach 0.0029`, and the rule (`3600 ÷ the unit's length in metres`)
- **Print the unit** → what on and off look like
- **Decimal places** → `0 = whole, 1 = 58.8, 2 = 58.75`

### Custom multipliers

The multiplier is simply `your unit per metre per second`:

| unit | multiplier |
|---|---|
| m/s | 1.0 |
| km/h | 3.6 |
| mph | 2.23694 |
| knots | 1.94384 |
| ft/s | 3.28084 |
| **Mach** | **1/343** (Mach 1 = 343 m/s) |
| km/min | 0.06 |
| yards/s | 1.09361 |
| furlongs/fortnight | 6012.9 |
| Mach | 0.00291545 (= 1/343) |

Anything else: take **3600 ÷ (your unit's length in metres)** and you have it. Range is 0.0001 to
1000.

**Mach** is the sixth preset: `1/343`, i.e. Mach 1 = **343 m/s** at sea level and 15 °C. Because the
numbers are small — 58.8 m/s is Mach 0.171 — the significant-digit rule gives Mach three decimals by
itself, with no special case needed. `0.2 Mach` would be a lie about a measurement; `0.171` is not.
Sound speed scales with temperature (343 at 20 °C, 340 at 15 °C in dry air, 295 at -50 °C), so this
is a fixed sea-level reference, not a local one.

## Install

```powershell
cd $HOME\f1-cyberpunk-mod
git pull --rebase
powershell -ExecutionPolicy Bypass -File .\tools\update.ps1
```

Or by hand, game closed:

```powershell
$root = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
New-Item -ItemType Directory "$root\r6\scripts\phoenix_true_speedometer" -Force
Copy-Item .\Phoenix_true_speedometer\r6\scripts\phoenix_true_speedometer\*.reds `
          "$root\r6\scripts\phoenix_true_speedometer\" -Force
```

Full restart — redscript compiles at boot.

Then: **Mod Settings → Phoenix True Speedometer → Units**.

## Coexistence with the car mod

`phoenix_aston_valkyrie.reds` also wraps `hudCarController.OnSpeedValueChanged`. Redscript chains
wrappers and the outer one wins, so with both installed whichever loads last writes the number. The
car mod writes `km/h` or `m/s` (its own `m_kmOn` switch); this mod writes what you chose.

**If you want the unit picker, install this mod only** — that is the intended arrangement now. The
car mod's dash (wheel screen, gear, rev lights) is separate and unaffected either way.

## Later idea, not built

The in-game **odometer** plus a timestamp is an independent measurement of the same thing: distance
delta ÷ time delta. Two uses:

1. **Cross-check.** Sample the odometer and the body velocity over the same window; if they
   disagree, one of them is not what we think it is. That would settle any remaining doubt about
   which readout to trust, using a number the game maintains for its own purposes.
2. **Fallback.** If a future patch stops `GetLinearVelocity` from tracking the vehicle (it is the
   physics velocity, so unlikely), the odometer derivative keeps working.

Cost: a sampled timer, and an odometer that only counts some vehicles. Parked until there is a
reason — the body read is exact and cheap.
