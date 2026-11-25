# Phoenix True Speedometer — CET HUD

A speed readout that draws **its own HUD** and leaves the game's speedometer completely alone.
Nothing is overridden, no redscript is compiled, and nothing of the vanilla HUD changes — you switch
this one on when you want it.

```
bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\init.lua
```

Requires **Cyber Engine Tweaks**. If **Native Settings UI** is installed the same options also appear
in the game's own Mods menu; without it everything is in the CET overlay.

## Why a HUD instead of the old override

The previous build (redscript, commit `27493d9`) wrapped the vanilla widget. It read the right
number, but it inherited three things it could not fix: a widget sized for about four characters, a
`km/h` label that belongs to the game, and a tick bar drawn from the game's inflated curve. On top of
that every edit needed a redscript recompile, and a compile error disables *every* redscript mod on
the install, not just this one. Drawing our own text removes all four problems at once.

The number is unchanged, and still the reason the mod exists:

| real | the game's dial showed | ratio |
|---|---|---|
| 277 km/h | 572 | 2.06× |
| 58.8 m/s (17 s per km) | 110–117 | 1.92× |

The HUD never reads the game's HUD number. It reads the physics body —
`veh:GetLinearVelocity()` dotted with `veh:GetWorldForward()` — which the game never derives.

## Turning it on

The HUD is **on by default**. Hide and show it whenever you like:

1. CET overlay (`~`) → **Bindings**
2. `PhoenixSpeedometer_ToggleHud` — show/hide
3. `PhoenixSpeedometer_ToggleLabels` — units on/off

The state is remembered in `settings.ini` next to `init.lua`, so it survives a restart.

## Where the options live

Two places, both writing the same `settings.ini`:

1. **CET overlay** (`~`) — a *Phoenix True Speedometer* window, drawn whenever the overlay is open.
   Needs nothing but CET.
2. **Settings → Mods** — a *Phoenix Speedometer* tab, in three subcategories plus a reset:

   | subcategory | widgets |
   |---|---|
   | HUD | Show the HUD · Print the units · First person only |
   | Units | Slot 1 unit · Slot 2 unit (both offer `off`) · two custom multipliers |
   | Position and look | text size · X · Y · colour R/G/B · fallback smoothing |
   | (tab root) | **Reset to defaults** — also wired into Native Settings' own restore-defaults |

   That page is supplied by **Native Settings UI**
   ([Nexus 3518](https://www.nexusmods.com/cyberpunk2077/mods/3518)); without it the tab simply does
   not appear and nothing else changes. Resetting from either surface updates both, so the Mods tab
   never shows a stale value.

The redscript "Mod Settings" mod ([Nexus 4885](https://www.nexusmods.com/cyberpunk2077/mods/4885))
that the old build used plays no part here — that row disappeared with the `.reds`.

Everything is saved the moment it changes.

## Input

**The HUD does not take your mouse or keyboard.** CET only traps input for ImGui while its own
overlay is open: `Overlay.cpp` calls `SetTrapInputInImGui(m_enabled)`, and `D3D12::OnWndProc`
swallows mouse and keyboard messages only when that flag is set. With the overlay closed, every
event goes straight to the game.

The readout also carries `ImGuiWindowFlags.NoInputs`, so it is click-through by construction, even if
that routing ever changed. The settings window *is* interactive — but it only exists while the
overlay is open, i.e. while CET is trapping input anyway.

| option | default | what it does |
|---|---|---|
| Show the HUD | on | master switch, same as the hotkey |
| Print the units | on | `212 km/h` instead of `212` |
| First person only | off | hide in third person and photo mode |
| Slot 1 unit | `km/h` | the main number |
| Slot 2 unit | `m/s` | second number; any unit, or **off** for one number |
| custom multiplier | 1.0 | used when a slot is set to `custom`: value × multiplier |
| Text size | 2.2 | ImGui font scale |
| Horizontal / vertical position | 0.60 / 0.78 | fraction of the screen, 0–1 |
| Colour red / green / blue | 0.35 / 0.95 / 1.00 | text colour |
| Position-fallback smoothing | 0.25 | only used if the velocity methods are unavailable |

Units: `m/s`, `km/h`, `mph`, `knots`, `ft/s`, `Mach` (1 Mach = 343 m/s), `custom`, `off`.

Example at 58.8 m/s, both slots on:

```
212 km/h   58.8 m/s
```

If `m/s` should lead instead, set Slot 1 to `m/s` and Slot 2 to `km/h` — it is one click, both
numbers are on screen either way.

`settings.ini` is plain text and can be edited by hand while the game is closed. Every value is
clamped on load, so a typo cannot hide the HUD or move it off screen:

```ini
enabled=true
slot1=km/h
slot2=m/s
showLabels=true
fppOnly=false
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

## Where every API fact comes from

Nothing in this mod is guessed; each call below was checked against a shipping mod, a class dump or
CET's own source.

| call | evidence |
|---|---|
| `registerForEvent("onDraw" / "onInit" / "onUpdate" / "onOverlayOpen" / "onOverlayClose")` | `ScriptContext.cpp` — exactly these names exist, anything else logs an error |
| `onDraw` takes no arguments, `onUpdate` gets the delta | `ScriptContext.cpp` (`TryLuaFunction(m_logger, m_onDraw)`) |
| `registerHotkey(id, label, fn)` | `ScriptContext.cpp` overloads; BetterVehicleFirstPerson |
| sandbox has **no `debug` library**; `io.open` resolves relative paths against the mod folder | `LuaSandbox.cpp` whitelist + `InitializeIOForSandbox` |
| CET calls **nothing** after loading `init.lua`, and sets `registerForEvent` to nil straight after — a mod has to start itself during load | `ScriptContext.cpp` (`ExecuteFile`, then `env["registerForEvent"] = sol::nil`) |
| `_G` is not whitelisted | same whitelist — the mod never touches it |
| `ImGuiWindowFlags.<Name>`, `ImGuiCol.<Name>` are tables | whitelist entries; BetterVehicleFirstPerson, CET-Mod-Manager, GameUI-WhereAmI |
| `ImGui.Checkbox` / `DragFloat` return **value, changed** | BetterVehicleFirstPerson, CyberpunkVRPort_WristHud (both assign the first return) |
| `GetDisplayResolution()` returns width, height | whitelist; psiberx GameUI-WhereAmI |
| `ImGui.SetWindowFontScale` | BetterVehicleFirstPerson |
| input is trapped for ImGui only while the overlay is open | `Overlay.cpp` (`SetTrapInputInImGui(m_enabled)`), `D3D12.cpp` (`OnWndProc`) |
| `Game["GetMountedVehicle;GameObject"](Game.GetPlayer())` | BetterVehicleFirstPerson |
| `veh:GetLinearVelocity()`, `GetWorldForward()`, `GetWorldPosition()`, `IsPlayerDriver()`, `GetCameraManager()` | CET class dump of `vehicleCarBaseObject` |
| `cameraManager:IsTPPActive()` | CET class dump of `vehicleCameraManager` |
| `Vector4` instances expose `.x/.y/.z/.w` | CyberpunkVRPort geometry code (`p.x, p.y, p.z`) |
| Native Settings UI: `addTab`, `addSubcategory`, `addSwitch(path, label, desc, current, default, cb)`, `addSelectorString(path, label, desc, elements, index, defaultIndex, cb)` — selector callback receives the **index** | Native Settings UI's own `init.lua` and its official example |

## Verified

The Lua is executed against stubbed CET/ImGui/Game APIs (`tests/test_hud.py`, via `lupa`): **57 tests**,
all passing, and the harness deliberately reproduces CET's restrictions — `debug` is removed, the
working directory is the mod folder, and the stubs use CET's real return shapes. Putting
`debug.traceback` back into `guard()` fails 17 of them.

Speed and digits:

- digits at 0, 0.01714, 0.171, 9.876, 58.83, 100, 212.4, 999.6, plus `NaN` and a non-number
- every unit factor and label, custom-multiplier clamps, an unknown unit falling back to m/s
- the default readout is exactly `212 km/h   58.8 m/s` at 58.8 m/s; labels off, slot 2 off
- speed from body velocity; reverse travel reads positive
- position-difference fallback: 5.88 m in 0.1 s → 58.8 m/s, no speed on the first frame, none from a
  nonsense delta; missing velocity methods fall through instead of throwing
- first-person detection, and an unavailable camera query *shows* the HUD instead of hiding it

Drawing and settings:

- draws while driving; nothing with no vehicle, as a passenger, when toggled off, or in third person
  with first-person-only on
- positions and scales from `GetDisplayResolution()` (1920×1080 → 1152, 842, scale 2.2); still draws
  when the resolution query is unavailable
- the readout window carries `NoInputs`, so it cannot consume a click or a keystroke
- colour pushes and pops stay balanced; a colour API that throws leaves the stack untouched
- a widget that throws still closes both windows, and a throwing `ImGui.Begin` does not escape
  `onDraw`
- a checkbox click writes the **value**, not the "changed" flag
- a binding returning `nil` can never nil out a setting; drag floats are clamped
- the unit setter accepts a name or an index and rejects nonsense; a slot can be blanked to `off`
- settings round-trip; a corrupt line keeps the default; a hand-edited file cannot hide the HUD
  (`scale=99`, `posX=5.5`, `posY=-3`, unknown units → clamped); an unwritable file is not fatal
- Native Settings UI receives `addSwitch` and index-based selectors, and its callbacks move the slot

Startup:

- simply loading the file registers both events and both hotkeys — no explicit call needed. (Removing
  the self-start line fails 27 tests.)

Static:

- no `//`, `<<`, `>>`, `goto`, `%d`, `table.unpack`, `math.type`, `utf8`
- no `debug`, `os`, `_G`, `require`, `loadstring`, `loadfile`, `getfenv`, `package`, `coroutine`
- no C-style enum spellings (`ImGuiCol_Text`), only the whitelisted tables
- no redscript symbols; `init.lua` sits in `mods\phoenix_true_speedometer\`

## Honest limits

- **Only the game can prove the picture appears.** Every API shape is sourced (see the table above),
  but the rendering itself is unverifiable here. If a call is missing it is skipped, and the CET
  console (`~`) names the file and line — that is the first place to look.
- **Removing the old `.reds` triggers one redscript cache rebuild on the next launch.** That is
  normal, happens once, and is not a compile of this mod.
- **CET reload, not restart:** reloading CET while the game runs re-registers the Native Settings UI
  tab, which can leave a duplicate tab until the next launch. The overlay window and hotkeys are
  unaffected. A full restart is the clean path.
- **First person only** uses `IsTPPActive()`; if a future CET drops it the option turns inert and the
  HUD shows in every view — it fails visible, not invisible.

## If the HUD does not appear

Run the one-shot check — it prints nothing destructive and answers all of it at once:

```
.\tools\check-hud.ps1
```

It reports whether the file is installed (and whether it matches the repo), the other CET mods, the
saved `settings.ini`, and every CET log line about this mod. CET's log lives at
`bin\x64\plugins\cyber_engine_tweaks\cyber_engine_tweaks.log`.

Then read the two lines the mod prints:

| what you see | meaning |
|---|---|
| `[Phoenix True Speedometer] HUD ready - bind the toggle in CET > Bindings` | the file loaded and started |
| `[Phoenix True Speedometer] 1 s in: hud=true vehicle=true driver=true speed=58.8` | one second in: it can see the car and is reading it |
| `1 s in: ... vehicle=false` | running fine, but not in a car at that moment |
| `1 s in: ... speed=nil` | in a car, but the velocity read failed — the position fallback needs another frame |
| **no "HUD ready" line at all** | the file is not being loaded: wrong folder, or CET has it disabled |
| **"HUD ready" but no "1 s in"** | `onDraw` is not being called — CET or another mod is not rendering |

The only two build-level things that can produce "no HUD, no messages" are an old copy of `init.lua`
(the first three builds of this mod never started themselves) or a file outside
`bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\`.

## Uninstalling

```
.\tools\uninstall.ps1                    # removes the car, keeps the HUD
.\tools\uninstall.ps1 -WithSpeedometer   # removes the HUD as well
```

The HUD folder is
`bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\` and nothing else in the game
touches it. Deleting that folder removes the HUD; `settings.ini` lives inside it.
