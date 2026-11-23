# Status — where PORT.md stands

Last touched: 2026-11-23 · branch `arena/fd35b985-f1-cyberpunk-mod`

## Done (in this repo, verified by tests)

| Item | Where |
|---|---|
| §3 physics table encoded once, as data | `tools/port_to_phoenix.py` (`STOCK_TO_F1`, `GEAR7_*`) |
| §4 rename: records, sub-records, UIIcon, module/classes, audio resource, files/folders | `tools/port_to_phoenix.py` (`RENAME`, `rename_path`) |
| §4 "keep shared" guard (assets, `.ent`, bank, events, widget paths, stock LocKeys) | `tools/port_to_phoenix.py` (`PROTECT`) |
| §4 audio-only gear ceiling 91.7 → 138.89 | `GEAR7_FROM/TO`, applied in both port modes |
| Phoenix tweak file, 2000 hp / 3824 Nm / 500 km/h | `Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml` |
| 4 Phoenix redscript files | `Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie/*.reds` |
| Stock reference + interim `_f1` reference | `reference/aston_valkyrie_stock.yaml`, `reference/aston_valkyrie_f1.yaml` |
| Audit gate (`--check`): fails on any leftover `xaires`/`_f1` id or stock physics value | `tools/port_to_phoenix.py --check` |
| 15 regression tests | `tests/test_port.py` (`python3 -m unittest discover -s tests -v`) |
| Docs: install/test, rename map, field confidence, localisation | `docs/` |

## Not done — each one needs your machine or the game

| # | Item | Why it is blocked | What unblocks it |
|---|---|---|---|
| 1 | `phoenix_aston_valkyrie.archive` + `.archive.xl` | binaries, ~100s of MB, copies of the Nexus original | `Phoenix_aston_cheats/archive/pc/mod/README-COPY-ARCHIVE.md` (one PowerShell copy) |
| 2 | redscript bodies | `PORT-BODY-START/END` markers in the generated `.reds`; the audio/Wwise metadata calls are engine-internal and can't be re-derived from the port notes | paste the stock `.reds` into `reference/clone_f1/` and re-run the port (bodies are copied verbatim, only identifiers move) — or run `--from stock`/`--in-place` on the stock staging folder |
| 3 | Distinct name (`phoenix_aston_valkyrie_name` / `_info`) | needs the language file inside the `.archive` (PORT.md §6) | `docs/LOCALISATION.md` |
| 4 | `aston_valkyrie.archive.xl` contents | small text file, only on your install | attach it as `.txt`; the Phoenix `.xl` is renamed from it |
| 5 | `Medium`/`Low` field + inline-index confirmations | need WolvenKit Tweak Browser against the stock file | the 3-step check at the bottom of `docs/YAML-FIELDS.md` |
| 6 | **v2 handling test** (hairpin / top speed / launch) | needs the game | `docs/INSTALL.md` §4 test matrix |

## Deliberate deviations from the port notes

1. **`VC_*` → `PHX_*`** method rename. PORT.md §5 installs both mods together;
   two identical `@addMethod` signatures is a redscript compile error. Revert with
   `--keep-method-names` only if the stock mod is uninstalled.
2. **Value-keyed physics.** The tool maps `(field, stock value) → Phoenix value`
   instead of rewriting whole records, so an unknown field name cannot silently
   shift the wrong number (front vs rear presets are disambiguated by their
   distinct stock values).
3. **`.archive`/`.bnk` in `.gitignore`.** They are Nexus binaries, not source;
   copying and renaming them is a one-command step documented next to the folder.
4. **Gear 1–6 are inherited, not rewritten.** §3 says they are unchanged, so the
   YAML only touches gear 7 — expect a big 6→7 step; if the car bogs on the
   upshift, that is a gear 6 `minSpeed`/`maxSpeed` tune, not a Phoenix physics bug.

## Next three actions

1. Copy + rename the two archive files (5 minutes, no game launch needed).
2. Splice the real script bodies (`reference/clone_f1/` → re-run the port) so the
   dashboard/audio actually run.
3. Launch, run the §4 test matrix, and report top speed + hairpin behaviour for v3.
