# Paint and livery — what actually changes the colours

Status: **done — confirmed in game 2026-11-24.** The Phoenix paints from the
*Aston Martin Valkyrie LMH* pane of **Xaires's Car Manager** with the v3 compat patch
(`compat/xaires_car_manager/repatch.ps1`). No art, no textures, no dependency mod.

This page records what the stock mod does, why our car was excluded from it, the patch
(v1 → v2 → v3, including the two bugs that made the first attempts fail), and the two
fallbacks that are no longer needed.

## What the stock mod does (Nexus, mod 38493)

> The car spawns in the original **The Heart of Racing #007** livery. With
> **Xaires's Car Manager 1.3 or newer** you can change:
> **Livery / paint:** the original livery, 70 basic colours or 79 real manufacturer
> colours. **Second colour:** the selected livery panels, in the same 70 + 79 colours,
> carbon black or the original livery. **Rims:** the original finish or a rim colour.
> **Window tint** and **engine volume**.

So the "extra styles you had to download" are not textures. They are a **CET mod**
(`Xaires's Car Manager`) that recolours the car at runtime: it drives the material
parameters of the panels, which is also why it can offer 149 colours plus "carbon
black" without shipping 149 texture sets. The two slots match what you asked for:

| Slot in the manager | What it paints |
|---|---|
| **Livery / paint** | the whole painted body |
| **Second colour** | the livery panels (`seg_*`/`g_*` in the dashboard art), i.e. the accent |

Colour references to aim at (sRGB starting points, not gospel):

| Name | Hex | Notes |
|---|---|---|
| Rosso Fiorano | `#6E1B1B` … `#7A2320` | Ferrari's deep, slightly brown red — darker than Rosso Corsa (`#D40000`) |
| Bronze (metallic) | `#A97142` … `#B08D57` | keep metallic low-gloss so it reads as bronze, not gold |

## Why it probably does not work on Phoenix yet

The manager has to recognise the car it is looking at. The stock car is
`Vehicle.xaires_aston_valkyrie`; ours is `Vehicle.phoenix_aston_valkyrie`. A CET mod
usually matches on exactly that record (or on its display name), so the Phoenix is
likely invisible to it — the tab still opens, the sliders just do nothing.

### Confirmed 2026-11-23

`…\cyber_engine_tweaks\mods\xaires_car_manager\init.lua` line **225**:

```lua
records = rec('xaires_aston_valkyrie' …
```

The manager names the stock record explicitly, so the Phoenix
(`Vehicle.phoenix_aston_valkyrie`) is not among the cars it paints.

The file is data-driven: one table entry per car —

```lua
key = 'amv', ad = 'Aston Martin Valkyrie LMH',
records = rec('xaires_aston_valkyrie'),
slots = {
  { id = 'kaplama', ad = 'Livery / paint', palet = 'sdh0.paint', onek = 'paint_', comps = PAINT_COMPS, marka = true, ... },
  { id = 'renk2',   ad = 'Second colour',  palet = 'sdh0.paint', onek = 'k_',
    comps = { 'body_renk2', 'door_fl_renk2', 'door_fr_renk2' }, marka = true, ... },
  { id = 'jant',    ad = 'Rims',           palet = 'sdh0.rim',   onek = 'rim_', comps = RIM_COMPS, ... },
}
```

and `carOf(veh)` iterates `car.records` to find the mounted vehicle. The colours are
applied as **component appearance names** (`paint_<colour>`, `k_<colour>`,
`rim_<colour>`) on those components — and because the Phoenix shares the stock `.ent`
and mesh, every one of those appearances already exists for our car. So route 1 is
literally one added id: `compat/xaires_car_manager/README.md`.

### Check it in 10 seconds, no game launch

```powershell
$GAME = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
Get-ChildItem "$GAME\bin\x64\plugins\cyber_engine_tweaks\mods" -Directory | Select-Object Name
Select-String -Path "$GAME\bin\x64\plugins\cyber_engine_tweaks\mods\*\*.lua" `
  -Pattern "aston_valkyrie" | Select-Object -First 25 Path, LineNumber, Line
```

* Hit on `xaires_aston_valkyrie` and nothing else → our record is not in its list.
* A hit on a config table / JSON list you can add to → easy compat patch.
* A hit on the *appearance* name (`aston_valkyrie`) only → it may already work, because
  both cars share the appearance; test in game before doing anything else.

In-game test: sit in the Phoenix, open CET ▸ *Xaires's Car Manager*, pick a colour.
If the body changes, the job is done — no work needed, just pick Rosso Fiorano and
bronze.

## Routes, cheapest first

### 1. Compat patch for the manager (hours, no art)

Only if the check above shows a data-driven vehicle list (a Lua table or JSON with
record ids). Adding `Vehicle.phoenix_aston_valkyrie` next to the stock entry is a
one-line change to *our* copy of the config — ship it as
`Phoenix_aston_cheats/…` (a CET mod ships under
`bin/x64/plugins/cyber_engine_tweaks/mods/…`, which the packaging validator already
allows as a game-root folder). No textures, no .app, works with every colour the
manager offers.

### 2. Bake the two colours into our own archive copy (a day, needs art)

The livery is painted with a multilayer material: a base albedo plus an MLMASK whose
layers select the panels. Repainting = editing the mask-linked layer colours (or the
albedo `.xbm`) in **our** copy of `phoenix_aston_valkyrie.archive`, so the stock mod is
untouched.

1. WolvenKit ▸ Asset Browser ▸ **Mod Browser** tab → `phoenix_aston_valkyrie.archive` →
   list `xaires\aston_valkyrie\…` → look for `.mlsetup`, `.mlmask`, `*_d.xbm`
   (albedo), `*_n.xbm`, `*_rm.xbm`.
2. Export the mlsetup to JSON, install the **MlsetupBuilder** plugin
   (*Home ▸ Plugins*), open it, find the layer that covers the painted body
   (layer 0 usually covers everything; later layers cut out the carbon, windows,
   logos).
3. Set layer 0 to Rosso Fiorano and the panel layer to bronze; export, convert back.
4. Pack that archive (`Pack`), verify with
   `python tools/inspect_archive.py <archive>` and reinstall.

Result: a fixed two-tone car. It replaces the stock livery's colours — you keep the
#007 decals now baked into the albedo, so decide whether the decal layers stay visible
or are masked out.

### 3. CrystalCoat (weeks, effectively a separate mod)

CDPR's paint system is opt-in per vehicle and needs:

* an extra appearance in the `.app` with the paint as an ink widget over the body,
* `hasVisualCustomization: true` and `customizableAppearance: <that appearance>` in the
  vehicle record,
* a script side (`Crystal Coat Fix` or `Enhanced Vehicle System` as a dependency), plus
  a wrapper so the colour picker opens for our car instead of the vanilla one.

That gives an in-game colour wheel, two colours, and "off/on" material states — very
close to what the Car Manager already does, for a lot more work. Only worth it if route
1 fails and you want runtime colour choice rather than one fixed scheme.

## What the UI looks like after the patch (expected, not a bug)

The manager's left column is **xa1res's whole catalogue** — Porsche Mission R, Apollo,
Bolide, Countach, 296 GT3, 9X8, SC63, A424, … — whether or not those mods are installed.
It has no per-record discovery; it just lists the cars its author built.

The Phoenix consequently has **no row of its own**: our patch points its record at the
`amv` entry, so the Phoenix is painted from the *Aston Martin Valkyrie LMH* pane. That is
the intended result — one palette, two cars. A separate row would mean a forked copy of
the manager.

Where the palette lives inside that pane:

| Row | Meaning |
|---|---|
| `Livery (n)` | the baked liveries — for the AMV that's *The Heart of Racing #007* |
| `Ferrari (13)`, `Lamborghini (16)`, `McLaren (10)`, … | real manufacturer colours (flat paint) |
| `Solid / Metallic / Matte (22 each)` | generic colours |
| `Second colour` (further down) | the accent panels; has *Livery original* and *Carbon black* first |

Pick a swatch → the choice is *stored*, and applied **when the car is spawned or
looked at** (the pane's own note: *"Choices are saved and applied when you get in or
look at this car"*). It is not a live preview of the car you are standing next to, and
the left column is a fixed catalogue you can click at any time — so the UI alone proves
nothing about whether the Phoenix is recognised. The test is: pick a colour, spawn the
Phoenix, look at it.

For the Rosso Fiorano + bronze look: a dark red from the Ferrari group for
**Livery / paint**, then a bronze from `Metallic` for **Second colour**.

## Code path verified 2026-11-24 (`carOf`)

```lua
local recordIndex = nil
local function carOf(veh)
  if not recordIndex then                      -- built once, from CARS
    recordIndex = {}
    for _, car in ipairs(CARS) do
      for _, r in ipairs(car.records) do
        local id = TweakDBID.new(r)
        recordIndex[tostring(id.hash) .. ':' .. tostring(id.length)] = car
      end
    end
  end
  ...
  return recordIndex[tostring(rid.hash) .. ':' .. tostring(rid.length)]
end
```

So `carOf` hashes whatever strings `car.records` holds and compares them with the mounted
vehicle's `GetRecordID()`. Our patched line puts `phoenix_aston_valkyrie` into
`CARS.amv.records`, which hashes to exactly our record — no further code change is
needed. (`currentVehicle()` additionally recognises the car you *look at*, not only the
one you sit in.)

Differences between the two cars are irrelevant here because the paint is applied as
component appearance names on components that exist in the shared `.ent`/mesh.

## Saved selection as of 2026-11-24

`ayarlar.json` (the manager's own settings, keyed by car `key`) had:

```json
"amv": { "renk2": "orijinal", "jant": "orijinal", "kaplama": "rosso_dino", "film": "yok" }
```

`rosso_dino` is Ferrari **Rosso Dino** (rgb 242,96,42 — the bright orange-red), *not*
Rosso Fiorano (`rosso_fiorano`, rgb 98,16,26). If the car comes out orange after
spawning, that is the stored choice working, not a bug.

For the requested look, pick in the pane:

| Slot | Group | Entry | rgb |
|---|---|---|---|
| Livery / paint | Ferrari | **Rosso Fiorano** | 98, 16, 26 (metallic 0.55 / rough 0.25) |
| Second colour | `Metallic` or `Special` | **Bronze** | 181,128,84 (`metallic_bronze`) or 163,111,59 (`bronze`) |

## Stuck on "Original livery" — 2026-11-24

Reported *after* the patch and a CET reload: the Phoenix still shows the stock
*The Heart of Racing #007* livery, the pane sits on **Original livery**.

"Stuck on original livery" hides three different failures. They look identical in game
and need different fixes, so the next measurement is chosen to tell them apart:

| # | What you see | What it means | Fix |
|---|---|---|---|
| **A** | you click a swatch and the pane snaps back to *Original livery* / the row stays on it | the click is not even **stored** — the write path refuses this car | `ayarlar.json` → `"amv".kaplama` stays `orijinal`; the guard is in the click handler |
| **B** | the pane **keeps** Rosso Fiorano, the car still looks stock | the choice is stored but the **apply** path bails for our record | `ayarlar.json` shows `"kaplama":"rosso_fiorano"`; the guard is in `apply`/`desired` |
| **C** | the *Livery / paint* slot only ever lists **Original livery** — no Ferrari / Lamborghini / Solid / Metallic groups under it | the palette file did not load for this slot | `marka_renkleri.json` / `sdh0_palet.json` / `kaplamalar.json` content |

### The dump answered it (2026-11-24) — and exposed a bug of ours

Two separate faults, both in the one line we had patched:

**1. v2 was a Lua syntax error.** The regex that applied it replaced only
`records = rec('xaires_aston_valkyrie')` and left the line's own comma behind, so the
file read

```lua
records = (function() ... end)(),,
```

`X,,` is not valid Lua — the **whole file** fails to parse, so the manager does not load
at all. v3 rewrites the entire line and refuses to write if `),,` would appear.

**2. The id was never going to match.** `carOf()` (line 435) hashes whatever string sits
in `car.records`:

```lua
local id = TweakDBID.new(r)
recordIndex[tostring(id.hash) .. ':' .. tostring(id.length)] = car
```

while the lookup uses `veh:GetRecordID()` (line 440-442), i.e. the TweakDBID of the
**full record name** `Vehicle.phoenix_aston_valkyrie`. `rec('xaires_aston_valkyrie')` is
not a passthrough — the entries it returns are the full names (that is the only way the
stock car resolves). A hand-written bare `phoenix_aston_valkyrie` hashes to a different
key, so the Phoenix stayed invisible to the manager while the stock Aston kept working —
exactly the symptom reported.

v3 therefore carries **both** forms: whatever `rec('phoenix_aston_valkyrie')` returns, plus
the literal `'Vehicle.phoenix_aston_valkyrie'`. Extra keys in `recordIndex` cost nothing.

```lua
records = (function() local t = rec('xaires_aston_valkyrie') local p = rec('phoenix_aston_valkyrie') if type(p) == 'table' then for i = 1, #p do t[#t + 1] = p[i] end end t[#t + 1] = 'Vehicle.phoenix_aston_valkyrie' return t end)(),
```

### Proven with a Lua interpreter, not by eye

The three candidate lines were loaded into a real Lua VM (`lupa`) with the manager's own
logic stubbed out — `rec()` returning `Vehicle.<name>`, `carOf()`'s hash lookup, and
`GetRecordID()` as the TweakDBID of `Vehicle.phoenix_aston_valkyrie`:

| Line | File parses? | stock Aston resolves | Phoenix resolves |
|---|---|---|---|
| v1 (bare string) | yes | **yes** | **no** |
| v2 (`end)(),,`) | **no** — `unexpected symbol near ','` | — | — |
| v3 (`rec()` + `'Vehicle.phoenix_aston_valkyrie'`) | yes | yes | **yes** |

That table is the whole story: v1 reproduces the reported symptom exactly, v2 explains
why nothing worked at all afterwards, v3 is the one that resolves both cars.

Also checked: our archive contains **no** `paint_`, `body_01` or `body_renk2` strings —
the component names and paint appearances live in the **shared** `xaires\aston_valkyrie\
aston_valkyrie.ent` (our YAML still points at it, line 122), which is why one added record
id is enough and why the Phoenix inherits every colour the stock car has.

A static test now guards all of this: `tests/test_compat.py` (14 checks) — the canonical
line must be identical in `repatch.ps1` and this README, must end in exactly one comma,
must carry both id forms, and the script must keep its `),,` refusal.

### What the rest of the source confirms

| Line | Fact |
|---|---|
| 13 | `PAINT_COMPS = { 'body_01', 'door_fl_a', 'door_fr_a' }` — the livery slot paints these three |
| 231-232 | AMV second colour paints `body_renk2`, `door_fl_renk2`, `door_fr_renk2` |
| 402, 413 | palette entries become `mesh = { comps = slot.comps, app = slot.onek .. id }` → `paint_rosso_fiorano`, `k_bronze`, `rim_…` |
| 576-588, 613-626 | applied as `c.meshAppearance = CName.new(app)` + `c:LoadAppearance()` (plus a redscript `SyncVC` call) |
| 461, 789 | livery tables come from `kaplamalar.json`, whose keys are `apollo, bolide, f296, g3r` — **no `amv`**; so the AMV's *Livery* entry is just component appearance `default`, i.e. the baked #007 skin |
| 27 | `rec(base, extra)` — `extra` is a list of livery variants (see the Apollo / 992 / 499P entries) |

All of those components exist for the Phoenix because it shares the stock `.ent`, so once
`carOf` matches, our car paints exactly like the stock one.

Colour ids confirmed present in the manager's own palette files:
`marka_renkleri.json` → `rosso_fiorano`; `sdh0_palet.json` → `metallic_bronze` (line 293)
and `bronze` (797, 1075). No guessing needed.

`redscript_rCURRENT.log` also confirms the install is healthy: both `xaires_*` and
`phoenix_*` script files compiled.

### What the test machine actually showed (2026-11-24)

> "the aston changes the original aston, but doesn't affect the phoenix"

That rules out A (the click *is* stored — the stock car obeys it) and C (the palette
loads). It leaves one thing: **`carOf()` still does not resolve the Phoenix**, so the
apply loop never runs for our vehicle. The paint works; the lookup misses.

Which means the v1 patch added a string that `carOf` hashes into a different key than
`GetRecordID()` returns. The only way that happens is if the entries in `CARS.amv.records`
are **not plain record names** — e.g. `rec()` prefixes `Vehicle.`, or resolves the name
through TweakDB. v1 hand-wrote `'phoenix_aston_valkyrie'`; if the stock entry really
expands to something else, our key never matches.

v2 asks `rec()` for our id as well, so whatever it does to the stock name it also does to
ours — correct in both worlds:

```lua
records = (function() local t = rec('xaires_aston_valkyrie') local p = rec('phoenix_aston_valkyrie') if type(p) == 'table' then for i = 1, #p do t[#t + 1] = p[i] end end return t end)(),
```

Apply with `compat/xaires_car_manager/repatch.ps1` (rebuilds from `init.lua.orig`, keeps
`init.lua.prev`, prints the body of `rec()`), reload mods, spawn, pick Rosso Fiorano.

If v2 also leaves the Phoenix untouched, `rec()`'s body and the apply loop are in
`paint_dump.txt` (sections `FUNCTION INDEX`, `init.lua 160-260`, `PAINT APPLY CODE`), and
the next patch is aimed by that code instead of guessed.

The cheap way to separate A/B from C: the Ferrari, Lamborghini, Porsche … groups exist
for **every** car in the catalogue, because they come from `marka_renkleri.json`
(car-independent). If they are visible under *Livery / paint*, C is out.

### Isolation test that costs nothing (do this first)

Spawn the **stock** Aston and paint it the same way:

```lua
Game.GetVehicleSystem():EnablePlayerVehicle("Vehicle.xaires_aston_valkyrie", true, false)
```

* Stock Aston paints, Phoenix does not → the problem is on our side of the record
  (A or B above).
* **Neither** paints → the Car Manager's paint path is broken on this install, patch or
  no patch (a manager update, a missing dependency, or the palette files), and the
  Phoenix was never the problem.

### Then, in the same session

1. Click **Rosso Fiorano**; get *into* the car and drive a few metres (the pane applies
   on mount, and some managers re-apply on a tick).
2. Run `tools/dump-car-manager.ps1` **after** the click — it now also dumps the apply
   path and the palette files, so the stored value is visible:

```powershell
cd $HOME\f1-cyberpunk-mod
git pull
powershell -ExecutionPolicy Bypass -File .\tools\dump-car-manager.ps1
```

New sections in that file:

| Section | Answers |
|---|---|
| `SAVED CHOICES` | was the click stored? (`"amv".kaplama`) → A vs B |
| `PAINT APPLY CODE (init.lua 455-640)` | what `apply`/`desired` actually calls |
| `PAINT KEYWORD INDEX` | line numbers for `appearance` / `Component` / `comps` |
| `PALETTE FILES` | do the palette JSONs have an `amv` block, and what keys |
| `ARE THE TWO COLOURS IN THE PALETTE?` | is `rosso_fiorano` / a bronze spelled the way we think (the author writes Turkish — `bronz`, `metalik_bronz`) |

## Applied 2026-11-23 (local, needs in-game confirmation)

The one-liner is in place on the test machine — `init.lua` line 225 now reads

```lua
records = (function() local t = rec('xaires_aston_valkyrie') t[#t+1] = 'phoenix_aston_valkyrie' return t end)(),
```

backup at `init.lua.orig`. Remaining questions, in order:

1. does the Car Manager tab now paint the Phoenix (stock Valkyrie must keep working too),
2. which palette entry is closest to Rosso Fiorano,
3. does the choice persist per car entry (`amv`) as expected — i.e. shared with the
   stock Valkyrie.

### Collecting evidence without copy-paste

`tools/dump-car-manager.ps1` writes one text file with the four things that decide the
diagnosis — the manager folder listing, its saved-choices JSON, `init.lua` lines 420-463
(`chosen` / `carOf` / `currentVehicle`) and the CET log tail:

```powershell
cd $HOME\f1-cyberpunk-mod
git pull
powershell -ExecutionPolicy Bypass -File .\tools\dump-car-manager.ps1
```

It writes `car_manager_dump.txt` in the repo root and opens it. If the CET log complains (`attempt to get length of a ... value`), `rec()` does not
return a table and the patch needs a different append — send the log line.

## Recommendation

1. Run the 10-second check and the in-game test.
2. If the manager already works → choose **Rosso Fiorano + bronze** there and stop.
3. If it does not and its list is data-driven → route 1 (a compat entry, no art).
4. Otherwise → route 2 with the two hex targets above, baked into our archive copy.

Nothing here touches the stock mod, and none of it changes physics.
