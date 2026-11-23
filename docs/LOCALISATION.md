# Localisation — distinct Phoenix name (PORT.md §6)

Current state: the Phoenix car reuses the **stock** name LocKey, so the scanner
says "Aston Martin Valkyrie" for both cars. They are still distinguishable by
horsepower (2000 vs 680) in the footer. This file is the exact work left.

## Why it can't be done here

* A plain-string `displayName` is proven to fail — the summon UI falls back to
  `TEST` (PORT.md §6). The value must be a LocKey that exists in a language file.
* The stock language file lives **inside** `aston_valkyrie.archive`
  (likely `base\languages\en-us.json` or a mod-local `.json` next to the `.xl`).
  Extracting/repacking it needs WolvenKit on Windows; a text search of the
  `.archive` only finds compressed `.xbm` UI paths.

## What I need from you (2 files)

1. `aston_valkyrie.archive.xl` — small text file, paste as `.txt`.
2. One of:
   * the archive's file list (WolvenKit "Archive" tab, save as `.txt`), plus
   * the extracted language file contents (WolvenKit → open
     `base\languages\en-us.json` → copy).

## The entries to add

```json
{
  "phoenix_aston_valkyrie_name": "Aston Martin Valkyrie F1 CHEAT",
  "phoenix_aston_valkyrie_info": "Workshop-built Valkyrie on a 2000 hp F1-spec drivetrain. 500 km/h gearing, ground-effect downforce. Not road legal anywhere."
}
```

Add them to the same file the stock `xaires_aston_valkyrie_name` / `_info` live in,
then repackage. Two acceptable routes:

* **Modify the copied archive** (`phoenix_aston_valkyrie.archive`) — simplest,
  no new files.
* **New small lang `.archive`** — ArchiveXL merges all archives, so a second tiny
  archive with just the language entries works too and keeps the texture archive
  byte-identical to stock.

Never edit the `.archive` as text.

## Then flip the YAML (2 lines)

In `reference/aston_valkyrie_f1.yaml` / the Phoenix YAML, `displayName` keeps no
prefix and `info` keeps the `LocKey#` prefix:

```yaml
  displayName: phoenix_aston_valkyrie_name
  info: LocKey#phoenix_aston_valkyrie_info
```

Currently the files have:

```yaml
  displayName: xaires_aston_valkyrie_name
  info: LocKey#xaires_aston_valkyrie_info
```

One command, once the entries exist:

```bash
sed -i 's/^  displayName: xaires_aston_valkyrie_name/  displayName: phoenix_aston_valkyrie_name/' \
       reference/aston_valkyrie_f1.yaml
sed -i 's/^  info: LocKey#xaires_aston_valkyrie_info/  info: LocKey#phoenix_aston_valkyrie_info/' \
       reference/aston_valkyrie_f1.yaml
python3 tools/port_to_phoenix.py --from f1 reference/aston_valkyrie_f1.yaml \
    --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
```

The port tool already keeps those two LocKeys protected on purpose
(`PROTECT` in `tools/port_to_phoenix.py`) — they are the *stock* keys, so they must
not be auto-renamed before the Phoenix entries actually exist.
