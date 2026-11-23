# WolvenKit, once, to get the name right

You do not need WolvenKit for anything else in this mod. You need it exactly once: to
put two text strings into an `.archive`, because that is the only place the game reads
vehicle names from. Everything else (physics, IDs, scripts, packaging) is done.

Time: ~25 minutes, of which 15 is downloading.

---

## 0. What WolvenKit is

WolvenKit is the community's modding toolkit for Cyberpunk 2077 (open source, on
GitHub). It is the only practical way to open, edit and rebuild `.archive` files —
the containers that hold the car's model, its textures, the dashboard widgets and the
**onscreen text** (names/descriptions).

Why text needs a toolkit at all: a "string" in this game is a CR2W `JsonResource`
record inside an archive, not a text file lying next to the mod. Notepad cannot make
one, which is why the YAML could be renamed a thousand times and the label never
changed (`docs/LOCALISATION.md` has the evidence).

**Plan: we build a second, tiny archive called `phoenix_strings.archive`.** The 11.6 MB
texture archive stays exactly as it is — you will not open it, so you cannot break it.

---

## 1. Install (download two things)

> **Game version matters here: this mod targets Cyberpunk 2077 2.5.** WolvenKit
> **9.1.1 does not support 2.5** — its own release notes say *"WKit >= 10.x with 2.5"*.
> The first WolvenKit build with 2.5 support is **10.0.0-beta.1** (2026-10-24, notes:
> *"Early support for game version 2.5"*). Install that, not 9.x.

1. **.NET Desktop Runtime 10 (x64)** — required by WolvenKit 10 and 9 alike:
   <https://dotnet.microsoft.com/download/dotnet/10.0> → *.NET Desktop Runtime 10.x* →
   **Windows x64** → download → run → Install.
2. **WolvenKit 10.0.0-beta.1** — <https://github.com/WolvenKit/WolvenKit/releases> →
   pick the `10.0.0-beta.1` entry (it is marked *Pre-release*, so scroll past the
   9.1.1 that GitHub shows first) → `WolvenKitSetup-10.0.0-beta.1.exe` (≈114 MB) → run →
   Install.
   *Portable alternative:* `WolvenKit-10.0.0-beta.1.zip`, extract anywhere, run
   `WolvenKit.exe`.
   *If the beta misbehaves on 2.5, the newer nightlies live in
   `WolvenKit/WolvenKit-nightly-releases` — latest at the time of writing is
   `10.0.0-beta.2-nightly.2026-11-22`, installer
   `WolvenKit.NightlySetup-10.0.0-beta.2-nightly.2026-11-22.exe`.*
3. Windows may warn "unknown publisher": **More info ▸ Run anyway**. It is a signed
   community app, not malware.
4. First launch asks for the game: point it at
   `G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty\bin\x64\Cyberpunk2077.exe`.

Sanity check: after this, the title bar (or *Help ▸ About*) shows a version starting
with **10.0**. If it says 9.x, the 2.5 support is not there — the app will warn that
the game version is unsupported.

---

## 2. Create the project (7 clicks)

1. **File ▸ New Project**
2. **Project name**: `phoenix_strings`
3. **Creation location**: anywhere that is **not inside the game folder** —
   `C:\Users\mahak\WolvenKit` or, say, `G:\Cyberpunk2077\Modding` (a sibling of
   `G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty`, which is fine)
4. **Mod name**: `phoenix_strings` ← this is the name of the archive you will get
5. Author: `mahak` (optional), version: `1.0` (optional)
6. **Finish**

You now see the project explorer with `source\archive`, `source\raw`, `source\resources`.
Anything under `source\archive` gets packed; its folder structure becomes the path
*inside* the archive.

---

## 3. Add the two strings

1. **File ▸ New File** (or right-click `source\archive` ▸ *New File*).
2. Pick the category **CR2W Files**, then the **JSON resource** entry — it is the
   option whose type is `JsonResource` (older guides call it "the json option about
   halfway down the CR2W Files list"; in 9.x the list is searchable — type `json`).
3. Name it **`en-us.json`** → **Create**. It opens in the built-in editor.
4. In the project tree, make the folder path match what our `.xl` expects: right-click
   `source\archive` ▸ **New Folder** → `phoenix`, then right-click `phoenix` ▸ **New
   Folder** → `aston_valkyrie`, then drag `en-us.json` into it.
   Final path on disk:
   `<Creation location>\phoenix_strings\source\archive\phoenix\aston_valkyrie\en-us.json`
   That path — `phoenix\aston_valkyrie\en-us.json` — is exactly the string in
   `Phoenix_aston_cheats\archive\pc\mod\phoenix_aston_valkyrie.archive.xl`. If you put
   the file somewhere else, the name will silently not appear.
5. Replace the `entries` list. **The easiest editor is Notepad, not WolvenKit's** —
   the project files are ordinary files on disk
   (`<Creation location>\phoenix_strings\source\archive\phoenix\aston_valkyrie\en-us.json`):
   right-click the file in Explorer ▸ *Open with* ▸ *Notepad*, then follow 5a–5c.
   (If WolvenKit shows the file as editable text in the middle pane, you can type there
   instead — same result. If it shows a property *tree* (`RootChunk` / `root` /
   `HandleId`), do not fight it: use Notepad.)

   **5a.** Find the line `"entries"`. It looks like `"entries": []` in a fresh file.
   Select from `"entries"` all the way to the matching closing `]` and replace that
   selection with the block below.
   Paste **only** the entries — let the header stay as WolvenKit wrote it:

```json
"entries": [
  {
    "$type": "localizationPersistenceOnScreenEntry",
    "femaleVariant": "Phoenix AMV LMH",
    "maleVariant": "",
    "primaryKey": "0",
    "secondaryKey": "phoenix_aston_valkyrie_name"
  },
  {
    "$type": "localizationPersistenceOnScreenEntry",
    "femaleVariant": "Aston Martin Valkyrie LMH, rebuilt as the Phoenix F1 prototype: 2000 hp, 500 km/h, 7-speed sequential, rear-wheel drive.",
    "maleVariant": "",
    "primaryKey": "0",
    "secondaryKey": "phoenix_aston_valkyrie_info"
  }
]
```

   **5b.** The two `secondaryKey` values must match the YAML byte for byte — they are
   what `displayName: phoenix_aston_valkyrie_name` and
   `info: LocKey#phoenix_aston_valkyrie_info` look up.
   Sanity checks in the file: it must contain `"$type": "JsonResource"` somewhere near
   the top (otherwise the file type is wrong) and the closing `]` of `entries` must be
   followed by `}` on the next line — a missing bracket makes WolvenKit fail at pack
   time with a JSON error.
   **5c.** Save (**Ctrl+S**). In WolvenKit, close the file's tab (the **×**) and
   double-click the file again to confirm your text is what is now in the project;
   then continue.

> If the editor shows a red error, or the file type you created is not `JsonResource`,
> stop and send a screenshot: creating the wrong type is the one step that leads to a
> silent no-op.

---

## 4. Pack

1. Toolbar → **Pack** (*Pack Mod* / *Pack Project* — the hammer/pak icon).
2. Wait for the log line that packing finished.
3. Output: `<Creation location>\phoenix_strings\packed\archive\pc\mod\phoenix_strings.archive`
   (e.g. `G:\Cyberpunk2077\Modding\phoenix_strings\packed\archive\pc\mod\phoenix_strings.archive`)

---

## 5. Verify before touching the game

PowerShell, in the repo folder:

```powershell
cd $HOME\f1-cyberpunk-mod
python .\tools\inspect_archive.py "G:\Cyberpunk2077\Modding\phoenix_strings\packed\archive\pc\mod\phoenix_strings.archive" --json-only --expect 'phoenix\aston_valkyrie\en-us.json'
```

* `OK: phoenix\aston_valkyrie\en-us.json is in the archive` → continue.
* `MISSING: …` with `same file name, different folder: <path>` → your file landed at
  `<path>`. Either move it in WolvenKit, or send me that line and I will change the
  one path in the `.xl`. Do not guess.
* `not a .archive` → you pointed at the project folder instead of `packed`.

(No Python? Install it from the Microsoft Store, or use `py -3` instead of `python`.)

---

## 6. Install it

```powershell
$GAME = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
$WK   = "G:\Cyberpunk2077\Modding\phoenix_strings\packed\archive\pc\mod\phoenix_strings.archive"

Copy-Item $WK "$GAME\archive\pc\mod\" -Force          # into the game
Copy-Item $WK ".\Phoenix_aston_cheats\archive\pc\mod\" -Force   # into the repo, so the zip keeps up
make all                                              # repo gates still green (optional)
```

Full restart of the game (not a CET reload). Summon the car: the card should read
**Phoenix AMV LMH**, and the scanner footer **2000 hp**.

---

## 7. If the card does not change

| Symptom | Cause | Fix |
|---|---|---|
| still `PHOENIX_ASTON_VALKYRIE` | strings archive not read at all | confirm `phoenix_strings.archive` is in `<game>\archive\pc\mod\`; check `r6\logs\archivexl.log` |
| still the record name, but the archive is installed | path inside the archive ≠ the `.xl` line | run step 5, then tell me the real path |
| `TEST` or a raw `LocKey#…` | the `en-us.json` was packed as plain text, not CR2W | re-create it as a `JsonResource` (step 3.2) and re-pack |
| name appears, info text empty | only the `_name` entry made it | both entries are needed |

Logs worth reading: `r6\logs\archivexl.log`, `r6\logs\cyber_engine_tweaks.log`.

---

## 8. Notes specific to game 2.5

* WolvenKit 10 is a beta: if it shows a *game version* warning, accept it — 2.5 support
  is exactly what the 10.x line added.
* The mod itself needs **no changes** for 2.5: it is a renamed copy of a working mod
  plus a TweakXL file, and TweakXL/ArchiveXL on your install already read it.
* Archive files written by WolvenKit 10 are 2.5-compatible; do not mix a 9.x-packed
  archive with the 2.5 game.

## 9. What you can now safely ignore

* **Never** edit `phoenix_aston_valkyrie.archive` (the big one) — it is a working
  texture archive and nothing in this guide touches it.
* Do not rename `phoenix_strings.archive` to `phoenix_aston_valkyrie.archive`: that
  would replace the model archive with a 2 KB string archive and the car would vanish.
* Uninstalling the pretty name later = delete `phoenix_strings.archive`; the car keeps
  working under its record-name label.
