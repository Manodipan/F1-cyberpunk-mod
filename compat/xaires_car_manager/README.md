# Compat patch — make Xaires's Car Manager paint the Phoenix

The manager decides which car it is looking at by matching the mounted vehicle's record
against a per-car list. For the Valkyrie that list is built from one id, so our
`phoenix_aston_valkyrie` record is unknown to it and every slider silently does nothing.

Because the Phoenix shares the stock `.ent` and mesh, the appearance names the manager
switches (`paint_<colour>`, `k_<colour>`, `rim_<colour>`) already exist for our car. One
added id is all that is needed — no art, no new records.

## What the file looks like

`…\bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager\init.lua`, line 225:

```lua
records = rec('xaires_aston_valkyrie'),
```

`rec()` returns the list of record ids for that car. We do not need to know what its
second argument means — we append to whatever it returns.

## The patch (one line)

Replace that line with:

```lua
records = (function() local t = rec('xaires_aston_valkyrie') t[#t+1] = 'phoenix_aston_valkyrie' return t end)(),
```

## How to apply (safest: Notepad++)

1. **Back up first** — PowerShell:

   ```powershell
   $f = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager\init.lua"
   Copy-Item $f "$f.orig" -Force
   ```

2. Open `init.lua` in **Notepad++** (right-click ▸ Edit with Notepad++). Do **not** use
   `Set-Content`/`Out-File` in PowerShell here: the file is UTF-8 with Turkish text, and
   the default encodings will mangle it.
3. **Ctrl+H** → Find: `records = rec('xaires_aston_valkyrie'),`
   Replace with the patched line above → **Replace** (only once!) → **Ctrl+S**.
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
