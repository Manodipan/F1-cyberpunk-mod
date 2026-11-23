# Where the `.archive` goes

`phoenix_aston_valkyrie.archive` and `phoenix_aston_valkyrie.archive.xl` **are not
in this repo** — they are binary copies of the Nexus original and are stored with
the mod, not in Git (see `../../../../.gitignore`).

Do this once, on the machine that has the unpacked stock mod (PORT.md §4 Step 1–2):

```powershell
$stock  = "C:\path\to\aston_valkyrie"          # unpacked Nexus mod
$phoenix = "C:\path\to\Phoenix_aston_cheats"   # this folder

New-Item -ItemType Directory -Force "$phoenix\archive\pc\mod"
Copy-Item "$stock\archive\pc\mod\aston_valkyrie.archive"    "$phoenix\archive\pc\mod\phoenix_aston_valkyrie.archive"
Copy-Item "$stock\archive\pc\mod\aston_valkyrie.archive.xl" "$phoenix\archive\pc\mod\phoenix_aston_valkyrie.archive.xl"
```

Rules:

* **Contents stay untouched.** Same `.ent`, same livery, same texture core, same
  language file. Only the two file names change, so the game loads the same
  assets under a second archive name.
* **Do not duplicate `red4ext\plugins\AudioXL\`.** The Phoenix build shares the
  stock bank (`sounds\XairesAMV_Wwise\xaires_amv.bnk`), so that folder is
  deliberately absent from this tree. Two copies of the same bank = duplicate
  AudioXL load.
* **Never edit the `.archive` binary as text**, and never hand-edit files inside
  the game folder — Vortex overwrites them (PORT.md §5.1). Edit the staging copy.

Language file note: the stock `aston_valkyrie.archive.xl` (small text file) and
the archive's language entries are still needed for PORT.md §6 — see
`docs/LOCALISATION.md`.
