# Phoenix True Speedometer — CET HUD

A small always-there speed readout. It draws its own window, leaves the game's speedometer completely
alone, and has exactly one setting: a dropdown for the unit.

```
bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\init.lua
```

Requires **Cyber Engine Tweaks**, and nothing else — not Native Settings UI, not Mod Settings, not a
second mod of any kind.

## What this is, and why it is so small

An earlier version of this mod grew into a full settings system: a CET settings window, a Native
Settings UI tab, nine sliders, two unit slots, colour controls, a reset button, hotkeys. All of it
tested, and none of it ever appeared on the user's install.

What *did* appear was a 71-line diagnostic probe: a bare `registerForEvent("onDraw", ...)` with
`ImGui.Begin`, `ImGui.Text`, `ImGui.End` and no conditions at all.

So the rule is now: **ship the thing that drew.** This file is that probe with one feature added. The
larger version is still in the repo at `mods/phoenix_true_speedometer/init.lua` for reference, but it
is not what gets installed.

| | probe | this mod |
|---|---|---|
| registers `onDraw` at file scope | yes | yes |
| draws every frame, no conditions | yes | yes |
| draws with no vehicle | yes | yes (`-- km/h`) |
| hotkeys, settings window, other mods | none | none |
| unit dropdown | — | **yes** |
| movable / pinnable window | — | **yes** |
| remembers the unit and the position | — | yes (`unit.txt`) |

## Turning it on

Nothing to bind and nothing to enable. The window is on screen from the moment CET loads the file,
including in the main menu and on foot, showing `-- km/h` when there is nothing to read.

It starts **bottom middle**, which is out of the way of the game's own speedometer.

## The unit

Press `~` (CET's overlay) and the window shows two dropdowns. Pick a unit: `km/h`, `mph`, `m/s`,
`knots`, `ft/s`, `Mach`. The choice is written to `unit.txt` beside `init.lua` and read back on the
next launch. If that file cannot be written the dropdown still works for the session.

## Moving the window

Three positions, in the second dropdown:

| position | behaviour |
|---|---|
| `free` | drag it anywhere. **The default.** Dragging only works while `~` is open — see below |
| `top` | pinned, horizontally centred, 20 px from the top edge |
| `bottom` | pinned, horizontally centred, 20 px from the bottom edge |

`free` is the default on purpose: a window that cannot be moved is worse than one that starts
somewhere awkward, and the first run has no remembered place to restore.

A dragged position is remembered: it is written to `unit.txt` when the overlay closes and restored
on the next launch.

### How the drag works

The window follows the mouse with `IsMouseDown` + `GetMouseDragDelta` + `SetWindowPos`, rather than
relying only on ImGui's own window-move handling. `GetMouseDragDelta` is cumulative since the button
went down, so the position is `grab position + delta` — anchoring at the grab and never accumulating
frame by frame. That distinction is what makes the window follow the cursor exactly instead of
running away or stalling.

**Why dragging needs `~` open.** CET routes input to ImGui only while its own overlay is open — that
is the behaviour of CET itself, not of this mod. While the overlay is closed the window carries
`NoMove` and `NoInputs`, so the mouse passes straight through and nothing steals a click while
you drive. While it is open it has neither flag, so it can be grabbed by its body and moved.

```lua
-- closed: decoration removed, no input, cannot be moved
flags = AlwaysAutoResize + NoSavedSettings + NoDecoration + NoMove + NoInputs
-- open:   no decoration and movable/clickable
flags = AlwaysAutoResize + NoSavedSettings + NoCollapse
```

What the pinned math actually does, measured in the harness at 1920×1080:

```
bottom -> x = (1920 - 120) / 2 = 900,  y = 1080 - 24 - 20 = 1036
top    -> x = 900,                     y = 20
```

There is no separate probe anymore: the mod is the probe, and `PHOENIX PROBE OK  frames=N` appears
in the window while the overlay is open, so there is always a sign it is alive.

## What it reads

`veh:GetLinearVelocity()` dotted with `veh:GetWorldForward()` — the body's own speed in m/s, not the
game's curve-warped HUD number. An earlier build measured the stock dial at **2.07× the real speed**,
which is why this reads the body and not the gauge.

Reverse reads positive. With no vehicle (or on foot) it shows `--` rather than a stale number.

## Digits

Three significant figures, whole numbers once the value reaches 100:

| m/s | shown (m/s) | shown (km/h) |
|---|---|---|
| 58.83 | `58.8` | `212` |
| 9.876 | `9.88` | `35.6` |
| 0.1714 | `0.171` | `0.617` |
| 100.0 | `100` | `360` |
| 0 | `0` | `0` |

## Units

The game reports m/s, so each unit is a multiplier on that:

| unit | factor |
|---|---|
| `m/s` | 1 |
| `km/h` | 3.6 |
| `mph` | 2.23694 |
| `knots` | 1.94384 |
| `ft/s` | 3.28084 |
| `Mach` | 1 / 343 (Mach 1 = 343 m/s at sea level) |

## Why not the earlier approaches

The previous build (redscript, commit `27493d9`) wrapped the vanilla widget. It read the right number,
but it inherited the game's own label, the game's tick bar, and a widget sized for about four
characters. Every edit also needed a redscript recompile, and a compile error disables *every*
redscript mod on the install, not just this one.

Drawing our own text removes all of that — and the file that does it is 151 lines with no
dependencies, which is the point.

## What is proven, and what is not

Proven, by running the file:

- it loads and registers `onDraw` with nothing else called (CET calls nothing after loading a mod, and
  nils `registerForEvent` immediately after — so the registration has to be at file scope)
- it draws a window every frame, `Begin`/`End` balanced
- it draws with no vehicle, and shows `--` rather than a stale number
- every unit reaches the screen; a click changes the unit on the next frame (immediate mode draws the
  text before the dropdown)
- bottom and top pin to the horizontal centre with the measured coordinates above
- a position set to `free` stops being forced — the one line that made dragging snap back
- a drag moves the window by exactly the mouse delta (540,425 after a 40x25 drag from 500,400),
  keeps following while the button is held even with the cursor outside the window, and stops when
  released
- a closed overlay cannot drag it, and neither can a pinned window
- every variable the file assigns is declared — an undeclared one reads as a silent `nil`, which is
  how the restore silently stopped working
- `NoMove`/`NoInputs` while closed, absent while open, so the mouse is only ever captured in `~`
- a dragged position round-trips through `unit.txt` and is restored after a reload
- the chosen unit survives a reload; a corrupt or unwritable `unit.txt` does not stop the HUD
- a throwing ImGui call or a throwing vehicle read cannot escape `onDraw`
- 19 tests, passing on **Lua 5.1** (CET's LuaJIT) and 5.5

Not proven here:

- **The picture itself.** Only the game can show that. The version that is shipped is the one that
  already drew `PHOENIX PROBE OK` on screen; the only addition since is `BeginCombo`/`Selectable`/
  `EndCombo`, which are bound by CET (`src/sol_imgui/sol_imgui.h`) but cannot be exercised outside it.
  If the dropdown misbehaves, everything else still draws.
- **Exact speed at the top end** — the game's own physics wall is 100 m/s (360 km/h); see
  `docs/PHYSICS.md`.

## Install

```powershell
cd $HOME\f1-cyberpunk-mod
git pull --rebase
.\tools\update.ps1
```

`update.ps1` installs `Phoenix_true_speedometer\probe\init.lua` as
`mods\phoenix_true_speedometer\init.lua`, and removes the old separate `phoenix_probe` folder.

Verify what is installed:

```powershell
Get-FileHash "$env:GAME\bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\init.lua"
```

## If it does not appear

The mod prints two lines to the CET console (`~`) and to
`bin\x64\plugins\cyber_engine_tweaks\cyber_engine_tweaks.log`:

```
[PhoenixSpeed] init.lua executed
[PhoenixSpeed] 2 s in: vehicle=true speed=58.8 unit=km/h
```

| what you see | meaning |
|---|---|
| both lines and the window | working |
| `init.lua executed` only | the file loaded but `onDraw` is not being called — CET is not drawing |
| neither line | the file is not being loaded at all: wrong folder, or CET is not running |

`. \tools\check-hud.ps1` prints the install path, the installed file's hash, the other CET mods and
the log tail in one go.

## Uninstalling

Delete `bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\`. Nothing else is touched:
no redscript, no archives, no game files.
