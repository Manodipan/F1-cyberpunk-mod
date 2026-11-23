# Paint and livery — what actually changes the colours

Status: **route 1 available** (one-line compat patch, `compat/xaires_car_manager/`).
This page records what the stock mod does, why our car is excluded from it, and the
three routes — cheapest first.

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
