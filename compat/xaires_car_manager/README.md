# Compat patch — make Xaires's Car Manager paint the Phoenix

The manager decides which car it is looking at by matching the mounted vehicle's record
against a per-car list. For the Valkyrie that list is built from one id, so our
`phoenix_aston_valkyrie` record is unknown to it and every slider silently does nothing.

Because the Phoenix shares the stock `.ent` and mesh, the appearance names the manager
switches (`paint_<colour>`, `k_<colour>`, `rim_<colour>`) already exist for our car. One
added id is all that is needed — no art, no new records.

> **Confirmed in game 2026-11-24 with v3.** The Phoenix repaints from the *Aston Martin
> Valkyrie LMH* pane (Rosso Fiorano on the body). The choice is stored per manager entry,
> so the Phoenix and the stock Aston always share one paint.

## What the file looks like

`…\bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager\init.lua`, line 225:

```lua
records = rec('xaires_aston_valkyrie'),
```

`rec()` returns the list of record ids for that car. We do not need to know what its
second argument means — we append to whatever it returns.

## The patch (one line)

### v3 — 2026-11-24 (use this; it repairs v1 and v2)

```lua
records = (function() local t = rec('xaires_aston_valkyrie') local p = rec('phoenix_aston_valkyrie') if type(p) == 'table' then for i = 1, #p do t[#t + 1] = p[i] end end t[#t + 1] = 'Vehicle.phoenix_aston_valkyrie' return t end)(),
```

```powershell
powershell -ExecutionPolicy Bypass -File .\compat\xaires_car_manager\repatch.ps1
```

Two things it fixes, both of which were ours, not the manager's:

* **v2 left a double comma.** The regex replaced only `records = rec('xaires_aston_valkyrie')`
  and the line's own trailing comma stayed, so the file ended in `end)(),,` — a **Lua
  syntax error**, meaning the manager did not load at all. v3 rewrites the whole line and
  aborts if `),,` would appear.
* **v1/v2 wrote the wrong kind of id.** `carOf()` hashes each string with
  `TweakDBID.new()` and compares it to `veh:GetRecordID()`, which is the TweakDBID of the
  full name `Vehicle.phoenix_aston_valkyrie`. `rec()` returns full names (that is why the
  stock car resolves); a bare `phoenix_aston_valkyrie` hashes to a different key. v3 adds
  both forms — an extra unused key is harmless.

Running it any number of times is safe. It keeps your current file as `init.lua.prev`,
prints the patched line, a `double-comma check : clean`, and the body of `rec()`.

### v1 — 2026-11-23 (superseded; what the file held when the stock Aston painted and the Phoenix did not)

```lua
records = (function() local t = rec('xaires_aston_valkyrie') t[#t+1] = 'phoenix_aston_valkyrie' return t end)(),
```

### v2 — 2026-11-24 (broken, superseded)

Same as v1 but built through `rec('phoenix_aston_valkyrie')`; shipped with the double
comma above, so it never loaded.

## How to apply — option A: run the script (recommended)

```powershell
cd $HOME\f1-cyberpunk-mod
git pull
powershell -ExecutionPolicy Bypass -File .\compat\xaires_car_manager\repatch.ps1
```

It rewrites the **whole** `records` line from the v3 text above, keeps your current file
as `init.lua.prev`, refuses to write anything containing `),,`, and prints
`double-comma check : clean` plus the body of `rec()`. Running it twice is harmless.

## Undo (or "put it back so the manager at least works")

```powershell
$d = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager"
Copy-Item "$d\init.lua.orig" "$d\init.lua" -Force
```

Restart the game. `init.lua.orig` is the untouched file, so this always gets a working
manager back — it just will not paint the Phoenix.

Verified against manager **1.0.10** (`local VER = '1.0.10'`, 1,065 lines). If a manager
update changes the table, `repatch.ps1` says `could not find the records = ... line` and
writes nothing.

## How to apply — option B: Notepad++ (manual)

1. **Back up first** — PowerShell:

   ```powershell
   $f = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager\init.lua"
   Copy-Item $f "$f.orig" -Force
   ```

2. Open `init.lua` in **Notepad++** (right-click ▸ Edit with Notepad++). Do **not** use
   `Set-Content`/`Out-File` in PowerShell here: the file is UTF-8 with Turkish text, and
   the default encodings will mangle it.
3. **Ctrl+H** → Find: `records = rec('xaires_aston_valkyrie')` (leave the comma on the
   line alone) → Replace with the **v3 line above, minus its trailing comma** (the file
   already has one; adding a second makes `,,` and kills the whole file) → **Replace**
   (once) → **Ctrl+S**.
4. Verify:

   ```powershell
   Select-String -Path $f -Pattern "phoenix_aston_valkyrie" | Select-Object LineNumber, Line
   ```

   Exactly one hit, on line 225.
5. Full restart of the game (CET Lua is loaded at boot).

## Using it

Sit in the **Phoenix**, open CET ▸ **Xaires's Car Manager**. The Valkyrie section now
recognises the car:

| Slot | Pick |
|---|---|
| **Livery / paint** | Rosso Fiorano (manufacturer colours) or the closest basic red |
| **Second colour** | a bronze from the manufacturer/basic palette |
| Rims | whatever you like; unchanged from stock behaviour |

Note: the manager stores one choice per car entry (`amv`), so the palette you pick is
shared between the stock Valkyrie and the Phoenix. Change it while sitting in the
Phoenix and both follow.

## Caveats

* **A manager update overwrites `init.lua`** — re-apply the one-liner after updating.
  That is why the patch lives here as text and is *not* shipped inside the mod zip: it
  edits someone else's file, and a silent overwrite would be worse than a manual step.
* If a future manager version adds `phoenix_*` itself, delete this patch — the stock
  line plus theirs is enough.
* Nothing here touches physics, ids, audio or the archives. Revert = restore the
  `.orig` backup.
