# Phoenix True Speedometer — CET HUD

A speed readout that draws **its own HUD** and leaves the game's speedometer completely alone.
Nothing is overridden, no redscript is compiled, and nothing of the vanilla HUD changes — you switch
this one on when you want it.

```
bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\init.lua
```

Requires **Cyber Engine Tweaks**. If **Native Settings UI** is installed as well, the same options
also appear in the game's own Mods menu; without it everything is in the CET overlay.

## Why a HUD instead of the old override

The previous build (redscript, commit `27493d9`) wrapped the vanilla widget. It read the right
number, but it inherited three things it could not fix: a widget sized for about four characters, a
`km/h` label that belongs to the game, and a tick bar drawn from the game's inflated curve. On top of
that every edit needed a redscript recompile — a compile error disables *every* redscript mod on the
install, not just this one.

Drawing our own text removes all four problems at once. A Lua error, worst case, disables this one
mod until it is fixed and says so in the CET console.

The number itself is unchanged, and it is still the reason the mod exists:

| real | the game's dial showed | ratio |
|---|---|---|
| 277 km/h | 572 | 2.06× |
| 58.8 m/s (17 s per km) | 110–117 | 1.92× |

The HUD never reads the game's HUD number. It reads the physics body —
`veh:GetLinearVelocity()` dotted with `veh:GetWorldForward()` — which the game never derives.

## Turning it on

The HUD is **on by default**. Hide and show it whenever you like:

1. CET overlay (`~` by default) → **Bindings**
2. `PhoenixSpeedometer_ToggleHud` — show/hide
3. `PhoenixSpeedometer_ToggleLabels` — units on/off

The state is remembered in `settings.ini` next to `init.lua`, so it survives a restart.

## Options

In the CET overlay a **Phoenix True Speedometer** window appears whenever the overlay is open (it is
not drawn while you are driving with the overlay closed). Everything on it is saved immediately.

| option | default | what it does |
|---|---|---|
| Show the HUD | on | master switch, same as the hotkey |
| Print the units | on | `212 km/h` instead of `212` |
| First person only | off | hide in third person, photo mode, cutscenes |
| Slot 1 unit | `km/h` | the main number |
| Slot 2 unit | `m/s` | second number; any unit, or empty for one number |
| custom multiplier | 1.0 | used when a slot is set to `custom`: value × multiplier |
| Text size | 2.2 | ImGui font scale |
| Horizontal / vertical position | 0.60 / 0.78 | fraction of the screen, 0–1 |
| Colour red / green / blue | 0.35 / 0.95 / 1.00 | text colour |
| Position-fallback smoothing | 0.25 | only used if the velocity methods are unavailable |

Units: `m/s`, `km/h`, `mph`, `knots`, `ft/s`, `Mach` (1 Mach = 343 m/s), `custom`.

Example at 58.8 m/s, both slots on:

```
212 km/h   58.8 m/s
```

`settings.ini` is plain text and can be edited by hand while the game is closed:

```ini
enabled=true
slot1=km/h
slot2=m/s
showLabels=true
scale=2.2
posX=0.60
posY=0.78
colorR=0.35
colorG=0.95
colorB=1.00
```

## Digits

Three significant figures, whole numbers once the value reaches 100:

| m/s | km/h | shown (m/s) | shown (km/h) |
|---|---|---|---|
| 58.8 | 211.7 | `58.8` | `212` |
| 9.876 | 35.6 | `9.88` | `35.6` |
| 0.1714 | 0.617 | `0.171` | `0.617` |
| 100.0 | 360.0 | `100` | `360` |
| 0 | 0 | `0` | `0` |

## Verified

This is the first part of the project that could be tested instead of inspected. The Lua is executed
against stubbed CET/ImGui/Game APIs (`tests/test_hud.py`, via `lupa`): **44 tests**, all passing. The
stubs deliberately copy the return shapes of shipping CET mods, so the conventions themselves are
under test.

Digits, conversion, readout:

- digits at 0, 0.01714, 0.171, 9.876, 58.83, 100, 212.4, 999.6 — plus `NaN` and a non-number
- every unit factor and label, the custom-multiplier clamps, an unknown unit falling back to m/s
- the default readout is exactly `212 km/h   58.8 m/s` at 58.8 m/s; labels off and slot 2 empty work

Speed:

- speed from the body velocity; reverse travel reads positive
- position-difference fallback: 5.88 m in 0.1 s → 58.8 m/s, with no speed on the first frame and
  no speed from a nonsense frame delta
- missing velocity methods fall through to the fallback rather than throwing
- first-person detection, and an unavailable camera query *shows* the HUD instead of hiding it

Drawing:

- the HUD draws while driving; draws nothing with no vehicle, as a passenger, or when toggled off
- first-person-only really hides in third person
- it positions and scales from `GetDisplayResolution()` (1920×1080 → 1152, 842, scale 2.2)
- it still draws when the resolution query is unavailable — no position beats no readout
- colour pushes and pops stay balanced, and a colour API that throws leaves the stack untouched
- a widget that throws still closes both windows (an ImGui window left open corrupts later frames)
- a throwing `ImGui.Begin` does not escape `onDraw`

Settings:

- a checkbox click writes the **value**, not the "changed" flag — the CET return order, tested
- a binding that returns `nil` can never nil out a setting; drag floats are clamped to their range
- the unit setter accepts a name or a 1-based index, and rejects nonsense
- the settings window only draws while the overlay is open
- settings round-trip through `settings.ini`; a corrupt line keeps the default
- a hand-edited file cannot hide the HUD (`scale=99`, `posX=5.5`, `posY=-3`, unknown units → clamped)
- an unresolvable settings path is reported, not fatal

Static:

- no `//`, `<<`, `>>`, `goto` or `%d` (CET runs LuaJIT), no `table.unpack`/`math.type`/`utf8`
- no redscript symbols; `init.lua` sits in `mods\phoenix_true_speedometer\`
- a regression guard on the widget order: `local value, changed = ImGui.Checkbox(`

## Honest limits

- **Only the game can prove the HUD appears.** The API shapes are copied from three shipping CET
  mods (BetterVehicleFirstPerson, psiberx's GameUI-WhereAmI, CyberpunkVRPort_WristHud) rather than
  guessed, but the picture itself is unverifiable here. If something is missing, the call is
  skipped and the CET console (`~`) names the file and line — that is the first place to look.
- **The velocity methods** `GetLinearVelocity` / `GetWorldForward` are the same ones the redscript
  build used. They are called through `pcall`; if this CET version does not expose them to Lua the
  mod falls back to differentiating `GetWorldPosition`, which is smoothed and less exact.
- **First person only** uses `veh:GetCameraManager():IsTPPActive()`. If that method is missing the
  option is inert (the HUD then shows in every view) — it fails visible, not invisible.
- The HUD is drawn every frame from `onDraw`, independently of the game's own HUD widgets, so it
  cannot disappear when the game decides to hide or re-scale its speedometer.

## Uninstalling

```
.\tools\uninstall.ps1                    # removes the car, keeps the HUD
.\tools\uninstall.ps1 -WithSpeedometer   # removes the HUD as well
```

The HUD folder is
`bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\` and nothing else in the
game touches it. Deleting that folder removes the HUD; `settings.ini` lives inside it.
