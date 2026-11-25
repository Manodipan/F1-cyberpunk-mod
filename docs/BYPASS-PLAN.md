# How to bypass the 100 m/s wall — research

**Question:** how do we build a mod that lifts the game's vehicle speed wall?
**Answer:** a RED4ext plugin (C++) that hooks two native functions. It is genuinely small — the
hard part is not the code, it is whether the installed RED4ext knows where those functions are.
That is checkable from a text file before writing anything.

Everything below is verified against source, not memory: `WopsS/RED4ext`,
`WopsS/RED4ext.SDK`, and `jackhumbert/let_there_be_flight` (MIT, the mod that already does this).

## Why nothing else can work

| layer | can it lift the wall? | why |
|---|---|---|
| TweakXL / YAML | no | runs before physics; the limit is in native code |
| redscript | no | wraps script functions; `Recalculate` is native |
| CET (Lua) | no | can read speed, cannot replace the physics integrate step |
| **RED4ext plugin** | **yes** | only layer that can detour native code |

## Why Vehicle Speed Unlimiter 1.0.2 stops the game loading

Not incompatibility — **an error path**. The SDK helper it resolves addresses with:

```cpp
// RED4ext.SDK, include/RED4ext/Relocation-inl.hpp
auto address = resolveFunc(aHash);
if (address == 0) {
  stream << L"Failed to find the address for the hash (" << aHash << ") provided by the plugin.\n"
         << L"This issue is likely caused by the mod using an incorrect or outdated hash.";
  ShowErrorAndTerminateProcess(stream.str(), 0);   // <- message box, then ExitProcess
}
```

A hash missing from the current game's address database is a **message box and a process exit**, not
a disabled mod. That is exactly "doesn't even let the game load". So their plugin may be 95 %
correct and still be fatal.

**Corollary: the error box names the failing hash.** That number is the single most useful
diagnostic available for free — see step 1.

## Where addresses come from

RED4ext does not use hardcoded RVAs. `RED4ext.dll` loads a plain JSON at startup:

```
<game>\x64\cyberpunk2077_addresses.json
{ "Addresses": [ { "hash": "593628708", "offset": "1:1A2B3C4" }, ... ] }
```

`offset` is `segment:hex` — segment 1 = `.text`, 2 = `.rdata`, 3 = `.data` — and the loaded
address is `image base + offset`. Plugins call the export
`RED4ext_ResolveAddress(uint32_t hash) -> uintptr_t` (0 when absent).

**Consequences:**

1. The database is **patch-keyed data, not code**. When the game updates, RED4ext updates this
   file; plugins do not need rebuilding. That is why "not updated for 2.5" is the wrong thing to be
   worried about — the fix may be *updating RED4ext*, not the mod.
2. Whether a bypass is possible on a given install is **readable from disk**, with no game launch.
3. A plugin can call the resolver **directly** and stay alive on a miss. That is the one design
   change that turns "game won't start" into "mod does nothing".

## The two functions, and why these two

From `let_there_be_flight`, `src/red4ext/Physics/VehicleSpeedUnlimiter.cpp` (MIT):

| hash | function | role |
|---|---|---|
| `593628708` | `vehicle::RigidBody::Recalculate(vehicle::PhysicsData*) -> short` | where the frame's velocity is decided; returns `FP_INFINITE` at the wall and the update is discarded |
| `4067628720` | `vehicle::RigidBody::ForceSetLinearVelocity(PhysicsData*, Vector3*)` | the game's direct velocity writes (summon, respawn, autopilot) must survive too |

Both are registered by LTBF's *current* tree, which supports 2.5 — so those IDs should exist in the
address database of a current RED4ext. If they do not, no mod using them works, including LTBF's own
unlimiter, and the answer is "update RED4ext", not "write more code".

The struct needed is small, and its layout is documented in the SDK fork
(`include/RED4ext/Scripting/Natives/vehiclePhysicsData.hpp`):

```
force 0x00 · torque 0x0C · velocity 0x18 · angularVelocity 0x24 · inverseMass 0x30
```

The hook recomputes `v += F × (1/m)` itself, calls the original, and — only when the original
returned `FP_INFINITE` — writes its own velocity back over the refused one.

## Plan, in order, with the decision gates

### Step 1 — read the database (2 minutes, no game)

```powershell
findstr /C:"593628708" /C:"4067628720" "<game>\x64\cyberpunk2077_addresses.json"
```

- **Both found** → step 2.
- **One or both missing** → check the RED4ext log/version and update RED4ext to the current release,
  then look again. If they are still missing, this approach is blocked until RED4ext ships them; no
  amount of plugin code fixes a gap in the database.
- **Also worth doing:** reinstall VSU once and read the hash in its error message. If it names a
  *different* hash than these two, our two are fine and VSU simply has other stale hooks.

### Step 2 — build the plugin

Source is in [`native/speedcap/`](../native/speedcap/) — complete, ~150 lines, with CMake and a
build/install note. It uses only the public SDK: `Sdk->hooking->Attach`, `Sdk->logger`, and
`GetProcAddress("RED4ext.dll", "RED4ext_ResolveAddress")`. No Detours, no MinHook, no fork of
anything.

Requires Windows + MSVC 2022 + CMake. **Nothing here can be compiled or tested in this workspace**,
which is the main reason it is staged rather than shipped.

### Step 3 — test, cheaply and reversibly

1. Back up the save. Vehicle physics corruption is the failure mode, not a crash.
2. Install `red4ext\plugins\speedcap\speedcap.dll`, launch, check `red4ext\red4ext.log` for
   `attached=1`.
3. Drive the Aston (currently built for **95 m/s**) and see whether it will now pass 342 km/h. The
   gear ceiling is still 95 m/s, so **to test the wall the ladder has to go back above it** — keep a
   >100 m/s build for this test, or the answer will be "it stopped at 342" and look like a failure.
4. If it works: re-size the ladder for the real target (`docs/TOPSPEED-TEST.md` has the sizing
   history; 900029 was the last above-wall build at 538 km/h predicted).

### Step 4 — if the wall moves, re-derive the model

Our drag and thrust fits were calibrated **below** 100 m/s and the engine's air-resistance branch
behaves differently above it (`VehiclePhysicsUpdate.cpp` applies resistance conditionally at
`speedSquared >= 10000`). The first reading past the wall is a measurement, not a confirmation:
expect to re-fit `k` and `T` from two or three real numbers.

## Risks, stated plainly

| risk | severity | mitigation |
|---|---|---|
| wrong struct layout / signature corrupts the rigid body | high | test on a backed-up save; keep the DLL easy to delete |
| another mod already hooks `Recalculate` | medium | `Attach` returns false, we log and leave the game alone |
| hash present but pointing at a stale address after a patch | high | same class of failure the 2025 mod hit — the lesson is *fail soft and log*, which this does |
| physics instability above 100 m/s (collision tunneling, streaming) | medium | that is the game's own guard doing its job; drive the Badlands, not the city |
| we spend another night on a research project | **high** | this is optional. The 95 m/s car is finished, stable and shipped. |

## The honest recommendation

Two of these are worth doing **now**, because they cost minutes:

1. `findstr` on the JSON — settles feasibility on this install.
2. Re-read VSU's error hash, if it still shows one.

Then decide. If the hashes are there, building `speedcap` is an evening's work on a Windows machine
plus one test run. If they are not, the correct move is to wait for RED4ext to ship them rather than
fight the database — and the car keeps its 95 m/s, which is faster than anything the game offers.
