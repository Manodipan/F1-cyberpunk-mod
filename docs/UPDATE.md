# Updating the mod

Every update is the same two steps. This page exists so it never has to be worked out
again, and so the instructions in chat can just say *"the update block"*.

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\f1-cyberpunk-mod\tools\update.ps1"
```

That is the whole thing. It pulls, installs into the game, and verifies. **Restart the
game afterwards** — TweakXL reads YAML at boot, so CET's "reload all mods" does not take.

## What the script does

| Step | Why |
|---|---|
| clears `reference/vehicles/INDEX.md` and `docs/VEHICLE-COMPARISON.md` | both are **generated**. If you edited or regenerated them locally, git cannot merge them and the pull stops on a conflict. They are rebuilt from the YAMLs, so dropping local edits loses nothing |
| `git pull --rebase` | your clone sits on the same branch the work lands on |
| copies the tweak YAML to `r6\tweaks\phoenix\` | physics |
| copies the four `.reds` files to `r6\scripts\phoenix_aston_valkyrie\` | audio, virtual gearbox, HUD/LEDs |
| hashes every copied file against the repo | proves the install matches the repo byte for byte, instead of guessing |
| prints the commit and two shape checks | tells you *which* build you are running |

## Options

```powershell
# different install location
... -File .\tools\update.ps1 -GameRoot "D:\Games\Cyberpunk 2077"

# install what you already have (no network)
... -File .\tools\update.ps1 -NoPull

# pull and check only, do not touch the game
... -File .\tools\update.ps1 -NoCopy
```

## If the pull refuses

The script stops rather than guessing, and tells you which case it hit.

**A rebase is in progress** (a previous pull stopped on a conflict):

```powershell
cd $HOME\f1-cyberpunk-mod
git rebase --abort
```

Then run the script again. Nothing is lost: the abort puts you back exactly where you were.

**You committed to this branch locally.** Your commits are yours; the branch also gets
commits from the other side. Keep yours on a side branch, then match the remote:

```powershell
cd $HOME\f1-cyberpunk-mod
git branch backup-local-corpus HEAD          # keeps your work, reachable by name
git fetch origin
git reset --hard origin/arena/fd35b985-f1-cyberpunk-mod
```

`backup-local-corpus` is a normal branch — `git log backup-local-corpus` still shows
whatever was in it, and any file can be copied back out with
`git checkout backup-local-corpus -- <path>`.

## Doing it by hand

If the script is not an option, this is the same thing spelled out:

```powershell
$root = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
cd $HOME\f1-cyberpunk-mod
git checkout -- reference/vehicles/INDEX.md docs/VEHICLE-COMPARISON.md
git pull --rebase
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" "$root\r6\tweaks\phoenix\" -Force
Copy-Item "$HOME\f1-cyberpunk-mod\Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie\*" "$root\r6\scripts\phoenix_aston_valkyrie\" -Force
Select-String -Path "$root\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml" -Pattern "vehEngineData: Vehicle.phoenix_amv_engine"
```

The last line matters: it proves you are on a build that attaches physics by named record.
No output means you are on an older commit.

## After it runs

* The car is in the garage as **Phoenix AMV LMH** (`docs/INSTALL.md` has summon commands).
* Test protocol: [`TOPSPEED-TEST.md`](TOPSPEED-TEST.md) — Auto Drive Enhanced at 100 % so
  the run has no human input.
* What each number does: [`VEHICLE-MODEL.md`](VEHICLE-MODEL.md); the five-car evidence
  behind them: [`VEHICLE-COMPARISON.md`](VEHICLE-COMPARISON.md).
