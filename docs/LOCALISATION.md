# Localisation — distinct Phoenix name (PORT.md §6)

Status: **the only open blocker to a fully distinct car.** Everything else is built.

## What the real mod tells us

`main` shipped the answer to §6's first question. `aston_valkyrie.archive.xl`:

```yaml
localization:
  onscreens:
    en-us: xaires\aston_valkyrie\aston_valkyrie.json
    tr-tr: xaires\aston_valkyrie\aston_valkyrie_tr.json
```

So the display strings live in two JSON files **inside** the archive, at
`xaires\aston_valkyrie\aston_valkyrie.json` (en-us) and `…_tr.json` (tr-tr), and the
stock keys are `xaires_aston_valkyrie_name` and `xaires_aston_valkyrie_info`
(referenced from the YAML as `displayName: xaires_aston_valkyrie_name` and
`info: LocKey#xaires_aston_valkyrie_info`).

While this is unresolved both cars show the stock name; the scanner footer still
tells them apart by horsepower (2000 vs 680).

## The change

Add to **`xaires\aston_valkyrie\aston_valkyrie.json`** inside
`phoenix_aston_valkyrie.archive`:

```json
{
  "phoenix_aston_valkyrie_name": "Aston Martin Valkyrie F1 CHEAT",
  "phoenix_aston_valkyrie_info": "Workshop-built LMH Valkyrie on a 2000 hp F1-spec drivetrain. 500 km/h gearing, ground-effect downforce. Not road legal anywhere."
}
```

(keep the existing keys — the stock car still uses them). Add a Turkish pair to
`aston_valkyrie_tr.json` if you care about the tr-tr build; otherwise tr-tr keeps
the stock name.

Then repack the archive (WolvenKit: open `phoenix_aston_valkyrie.archive`, add the
edited JSON, save — contents otherwise unchanged) and flip two lines in the
reference file:

```bash
sed -i 's/displayName: xaires_aston_valkyrie_name/displayName: phoenix_aston_valkyrie_name/' \
    reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml
```

Careful: that reference file is a *copy of stock*; the cleanest way is to make the
change in a local copy, then port it:

```bash
cp reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml /tmp/aston_valkyrie.yaml
# edit /tmp/aston_valkyrie.yaml: displayName -> phoenix_aston_valkyrie_name
#                              info -> LocKey#phoenix_aston_valkyrie_info
python3 tools/port_to_phoenix.py --from stock /tmp/aston_valkyrie.yaml \
    --out Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml
```

Both keys are in the tool's `PROTECT` list, so they are **not** auto-renamed: the
Phoenix entries must exist in the language file before the YAML points at them
(otherwise the summon UI falls back to `TEST` — proven in PORT.md §6).

## Alternative without WolvenKit

Two other routes, both needing a Windows tool that writes `.archive` files:

* **Separate small archive** with only the localisation JSON, plus a second `.xl`
  declaring `localization.onscreens.en-us: phoenix\aston_valkyrie\aston_valkyrie.json`.
  ArchiveXL merges archives, so the texture archive can stay byte-identical to stock.
* **Script-side rename**: a redscript/CET hook that rewrites the onscreen entry at
  runtime (`LocalizationHelper`?). Fragile, version-dependent, not recommended.

If you want me to attempt a pure-Python archive writer, say so — there is a
reference implementation (`jcoetzee/cp2077-ev-conversion`, `tools/rdar.py`) that
reads/writes RDAR archives, but an archive we cannot test in-game is a crash risk,
so I'd rather not ship one blind.
