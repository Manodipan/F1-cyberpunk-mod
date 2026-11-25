# speedcap — experimental RED4ext plugin

Lifts the game's vehicle speed wall at **100 m/s = 360 km/h = 223 mph**. See
[../../docs/BYPASS-PLAN.md](../../docs/BYPASS-PLAN.md) for the research and
[../../docs/SPEED-CAP.md](../../docs/SPEED-CAP.md) for the diagnosis.

**Not built, not tested.** It exists so the work is not re-derived from scratch, and so nobody
starts from `Vehicle Speed Unlimiter` 1.0.2 — which stops the game from loading on 2.5 because it
resolves addresses through a helper that shows a message box and exits when a hash is missing.
This one gives up quietly instead: worst case the mod does nothing and the game starts.

## Check the addresses exist before building anything

The plugin never hardcodes an address. It asks RED4ext, whose database is a plain file:

```powershell
findstr /C:"593628708" /C:"4067628720" "<game>\x64\cyberpunk2077_addresses.json"
```

- **Both found** → this plugin can hook. Build it.
- **Either missing** → nothing that uses those hashes can work, including Let There Be Flight's
  unlimiter, which is where the hashes come from. Update RED4ext first; do not write more code.

## Build

Needs Windows, MSVC (VS 2022) and CMake. There is no build of this in the repo.

```powershell
git clone https://github.com/WopsS/RED4ext.SDK.git native/deps/red4ext.sdk
cmake -S native/speedcap -B native/speedcap/build -G "Visual Studio 17 2022" -A x64
cmake --build native/speedcap/build --config Release
```

## Install

```
<game>\red4ext\plugins\speedcap\speedcap.dll
```

Uninstall = delete the folder. No game files are touched.

## What to look at afterwards

`<game>\red4ext\red4ext.log`:

```
speedcap: Recalculate at 0x... attached=1 original=0x...
speedcap: ForceSetLinearVelocity at 0x... attached=1
```

`attached=0` means the hook was refused (already hooked by another mod, or the address is wrong):
the game runs, the wall stays. A missing hash logs `is not in cyberpunk2077_addresses.json` and
never touches the process.

## Risk

This hook runs in the physics loop at 60 Hz. A wrong signature or a bad offset corrupts the car's
rigid body — save the game before testing, and test on a car you can afford to lose.
