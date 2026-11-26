# Localisation — what the label under a car actually is

Status: the **name is already distinct**; the *pretty* name ("Phoenix AMV LMH") needs
one packed file. This page explains why, with the evidence, so nobody chases the
wrong bug again.

## Finding: the stock mod ships no strings at all

`phoenix_aston_valkyrie.archive` is a byte copy of `aston_valkyrie.archive`, so this
applies to both:

```bash
python3 - <<'PY'
data = open("Phoenix_aston_cheats/archive/pc/mod/phoenix_aston_valkyrie.archive", "rb").read()
for pat in (b"xaires_aston_valkyrie_name", b"xaires_aston_valkyrie_info",
            b"localization", b".json", b"Aston", b"Valkyrie"):
    print(pat.decode(), data.count(pat))
PY
# xaires_aston_valkyrie_name 0
# xaires_aston_valkyrie_info 0
# localization 0
# .json 0
# Aston 0
# Valkyrie 0
```

The archive contains the model, the UI atlases and the widgets — **no onscreen
text**. The stock `.xl` nevertheless declares

```yaml
localization:
  onscreens:
    en-us: xaires\aston_valkyrie\aston_valkyrie.json
    tr-tr: xaires\aston_valkyrie\aston_valkyrie_tr.json
```

and those two files do not exist inside the archive: a dangling reference. That is
the original mod's bug, inherited by the copy, and the reason the summon card shows
`XAIRES_ASTON_VALKYRIE` instead of "Aston Martin Valkyrie".

## How the game labels a car with no string

`displayName` is a `gamedataLocKeyWrapper` — a 64-bit hash, not text. Resolution:

| `displayName` value | What the UI shows |
|---|---|
| LocKey that exists in an onscreen file | that text, e.g. "Aston Martin Valkyrie" |
| LocKey that does not exist (our case today) | **the TweakDB record name, uppercased** |
| plain string (`displayName: Phoenix`) | `TEST` — proven, see PORT.md §6 |

The proof that it is the *record* name and not the LocKey: the card reads
`XAIRES_ASTON_VALKYRIE`, while the LocKey is `xaires_aston_valkyrie_name`
(the `_name` suffix would have shown up).

So the visible label follows the **TweakDBID**, which is exactly what the port
renamed:

| Car | Record | Card today |
|---|---|---|
| stock | `Vehicle.xaires_aston_valkyrie` | `XAIRES_ASTON_VALKYRIE` · 2023 · 680 hp |
| Phoenix | `Vehicle.phoenix_aston_valkyrie` | `PHOENIX_ASTON_VALKYRIE` · 2023 · 2000 hp |

Two different labels, two different horsepower figures. Nothing to fix for
identification; what is missing is only the polish.

## What this repo ships towards the pretty name

| File | Role |
|---|---|
| `tools/localization/en-us.json` | CR2W `JsonResource` with the two onscreen entries, ready to pack |
| `Phoenix_aston_valkyrie.archive.xl` → `archive/pc/mod/phoenix_aston_valkyrie.archive.xl` | registers it as `phoenix\aston_valkyrie\en-us.json` |
| tweak file | asks for `phoenix_aston_valkyrie_name` / `LocKey#phoenix_aston_valkyrie_info` |

Entry contents:

| secondaryKey | femaleVariant |
|---|---|
| `phoenix_aston_valkyrie_name` | Phoenix AMV LMH |
| `phoenix_aston_valkyrie_info` | Aston Martin Valkyrie LMH, rebuilt as the Phoenix F1 prototype: 2000 hp, 500 km/h, 7-speed sequential, rear-wheel drive. |

`make test` (41 tests) keeps the JSON, the `.xl` and the YAML in agreement:
`test_localisation_source_matches_the_yaml` fails if a key drifts.

## Packing it (WolvenKit, one file, ~2 minutes)

> Game **2.5**: use WolvenKit **10.x** (`10.0.0-beta.1` or newer) — 9.1.1 explicitly
> does not support 2.5. Details in [`WOLVENKIT.md`](WOLVENKIT.md) §1.

Click-by-click for a first-time user, screenshots-what-to-look-for included:
[`docs/WOLVENKIT.md`](WOLVENKIT.md). Short version below.

1. WolvenKit → **File ▸ New Project** → name it `phoenix_aston_valkyrie`.
2. `Source/archive` → right-click → **Add existing file…** → pick the real
   `Phoenix_aston_valkyrie/archive/pc/mod/phoenix_aston_valkyrie.archive`.
3. In the project tree, right-click the archive's `xaires\aston_valkyrie` folder →
   **Add file** → choose `tools/localization/en-us.json`, then rename it to
   `en-us.json` **and move it** so the path is `phoenix\aston_valkyrie\en-us.json`
   (that string is what the `.xl` points at; a different path silently does nothing).
4. Right-click it → **Convert to CR2W** (it must be a `JsonResource`, not text).
5. Toolbar → **Pack** → the result is `packed/archive/pc/mod/phoenix_strings.archive`.
   Ship it **next to** the texture archive (do not overwrite that one):
   `Phoenix_aston_cheats/archive/pc/mod/phoenix_strings.archive`.
6. `make check-strings` — proves the archive really contains
   `phoenix\aston_valkyrie\en-us.json`, the path the `.xl` names.
7. Reinstall and **restart the game** — the card reads `Phoenix AMV LMH`.

If WolvenKit's JSON template version differs from `WKitJsonVersion 0.0.8`, create a
new JSON resource inside WolvenKit instead of importing ours, and paste only the
`entries` array from `tools/localization/en-us.json`.

## Why not do it in the repo automatically

The strings live in a CR2W `JsonResource` **inside** an archive. Writing CR2W plus a
valid RDAR archive from scratch and shipping it untested is how mods get a
crash-on-boot reputation; a Python archive writer we cannot validate in-game is not
worth the risk. Everything up to the packing step is versioned here, so the manual
step is one file and one Pack click.

## Fallbacks, if you would rather not pack

* **Keep the fallback label.** `PHOENIX_ASTON_VALKYRIE` + 2000 hp is already
  unambiguous; you lose nothing functionally.
* **Rename the record** (`Vehicle.phoenix_amv_lmh` → card `PHOENIX_AMV_LMH`). Costs a
  rename across the YAML, scripts, docs and tests for a cosmetic string.
* **Reuse an unused vanilla LocKey** — every candidate belongs to another vehicle,
  so the card would lie. Not recommended.
