# Packaging — make the folder look like a normal CP2077 mod

## The norm

A Cyberpunk 2077 "legacy" mod (ArchiveXL + TweakXL + redscript, i.e. what Vortex
deploys) is a **mirror of the game root**: every top-level folder in the mod is a
folder that already exists in `...\Cyberpunk 2077\`. The manager just overlays the
tree. That means:

* no README, notes, `.py`, `.zip` or `__pycache__` inside the payload — they would be
  copied into the game folder;
* archives go to `archive\pc\mod\`, each `.archive` with a same-named `.archive.xl`;
* tweaks go to `r6\tweaks\<author>\<file>.yaml` (one folder per mod, as the stock mod
  does with `r6\tweaks\xaires\`);
* redscript goes to `r6\scripts\<mod folder>\*.reds`;
* file names lowercase, no spaces.

This mod is **not** a REDmod, so it has no `info.json` and no `mods\` folder. It also
has no CET mod, so no `bin\x64\plugins\cyber_engine_tweaks\`.

## Our tree

```
Phoenix_aston_cheats/                        ->  ...\Cyberpunk 2077\
  archive/pc/mod/phoenix_aston_valkyrie.archive      archive\pc\mod\
  archive/pc/mod/phoenix_aston_valkyrie.archive.xl   archive\pc\mod\
  r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml      r6\tweaks\phoenix\
  r6/scripts/phoenix_aston_valkyrie/*.reds           r6\scripts\phoenix_aston_valkyrie\
```

7 files, 12 MB. Deliberately **absent**:

| Missing | Why |
|---|---|
| `red4ext/plugins/AudioXL/...` | the Phoenix scripts load the stock bank `red4ext/plugins/AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk`. Shipping a second copy would load the same bank twice |
| `bin/x64/plugins/...` | no CET/Lua part — the logic is redscript |
| `info.json` | not a REDmod |
| any `.md`/`.txt` | docs live in `docs/`, and this note is in `docs/ARCHIVE-NOTES.md` |

## Verify it

```bash
make verify-package        # = python3 tools/package.py --check
```

`tools/package.py` fails on: a non-game-root top-level folder, any file at the
payload root, documentation/tooling anywhere in the payload, `__pycache__` /
`.DS_Store` / `.git*`, a tweak or `.reds` outside the `<author>` / `<mod folder>`
depth, an `.archive` without `.archive.xl` (or the reverse), an empty directory.
It warns on: uppercase/non-ASCII names, `red4ext/` being present (duplicate bank),
and files that do not start with the `phoenix` namespace. 15 packaging tests cover
the rules, and `make all` runs the check every time.

## Build the upload

```bash
make package
# -> dist/Phoenix_aston_cheats.zip  (11.4 MB, 7 entries, deterministic)
```

The zip root **is** the game-root mirror, so Vortex detects it as a Cyberpunk 2077
mod with no "Mod type" picker, and manual installers just extract it over the game
folder. `dist/` is gitignored — the payload is tracked, the artefact is built.

For Nexus, name the file `Phoenix_aston_cheats-<version>.zip` and mention in the
description that it must be installed **alongside** the stock Valkyrie LMH (shared
assets and bank), and that the stock mod provides `red4ext/`.

## Pre-upload checklist

- [ ] `make all` green (port → check → 36 tests → layout)
- [ ] `make package` built, zip has exactly 7 entries and no `.md`/`.txt`
- [ ] zip has `phoenix_aston_valkyrie.archive` **and** `.archive.xl`
- [ ] `r6/tweaks/phoenix/` contains one YAML; `r6/scripts/phoenix_aston_valkyrie/` four `.reds`
- [ ] the archive is the byte-identical copy of stock (see `ARCHIVE-NOTES.md`)
