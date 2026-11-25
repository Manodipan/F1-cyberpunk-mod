#Requires -Version 5.1
<#
.SYNOPSIS
    Pull the latest Phoenix build and install it into Cyberpunk 2077, then verify.

.DESCRIPTION
    One command, every update:
      0. clears a rebase/merge that a previous conflicting pull left half-done, and falls back to
         a clean sync when the pull still fails (only if there are no local commits),
      1. drops local edits to the GENERATED files (they are rebuilt, so they would
         otherwise conflict on every pull and cost you a rebase),
      2. pulls this branch,
      3. copies the tweak YAML and the four redscript files into the game,
      4. compares hashes so you can see the install matches the repo byte for byte,
      5. prints the commit you are on.

    It never restarts the game: TweakXL reads YAML at boot, so close the game, run this,
    then start it. (CET "reload all mods" is not enough for tweak changes.)

.PARAMETER GameRoot
    Cyberpunk 2077 install folder (the one containing r6\).

.PARAMETER Repo
    This repository's clone folder.

.PARAMETER NoPull
    Install what you already have, without pulling.

.PARAMETER NoCopy
    Pull and verify only; do not touch the game folder.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\update.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\update.ps1 -GameRoot "D:\Games\Cyberpunk 2077"
#>
[CmdletBinding()]
param(
    [string]$GameRoot = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Repo = "$HOME\f1-cyberpunk-mod",
    [switch]$NoPull,
    [switch]$NoCopy
)

$ErrorActionPreference = 'Stop'

function Write-Step($text) { Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "   $text" -ForegroundColor Green }
function Write-Warn2($text) { Write-Host "   $text" -ForegroundColor Yellow }
function Write-Bad($text) { Write-Host "   $text" -ForegroundColor Red }

if (-not (Test-Path $Repo)) {
    Write-Bad "repo not found: $Repo"
    Write-Warn2 "pass the clone folder with -Repo `"C:\path\to\f1-cyberpunk-mod`""
    exit 1
}

Push-Location $Repo
try {
    # ------------------------------------------- clear any half-finished git operation
    # A pull that stopped on a conflict leaves the repo unable to pull again ("you have
    # unmerged files"). That is not a state worth preserving here: this branch is written by
    # the agent, and the only tracked files that ever change locally are the generated ones.
    $gitDir = Join-Path $Repo '.git'
    if ((Test-Path (Join-Path $gitDir 'rebase-merge')) -or
        (Test-Path (Join-Path $gitDir 'rebase-apply'))) {
        Write-Warn2 "a rebase was left half-done; aborting it"
        git rebase --abort 2>$null | Out-Null
    }
    if (Test-Path (Join-Path $gitDir 'MERGE_HEAD')) {
        Write-Warn2 "a merge was left half-done; aborting it"
        git merge --abort 2>$null | Out-Null
    }
    $unmerged = git diff --name-only --diff-filter=U 2>$null
    if ($unmerged) {
        Write-Warn2 "unmerged files still present; resetting the work tree to HEAD"
        git reset --hard HEAD | Out-Null
    }

    # ------------------------------------------------- generated files: never merge them
    Write-Step "clearing generated files (they are rebuilt, not merged)"
    foreach ($generated in @('reference/vehicles/INDEX.md', 'docs/VEHICLE-COMPARISON.md',
                             'docs/TOPSPEED-DESIGN.md')) {
        if (git ls-files --error-unmatch $generated 2>$null) {
            git checkout -- $generated 2>$null | Out-Null
            Write-Ok $generated
        }
    }

    # ------------------------------------------------------------------------- pull
    if (-not $NoPull) {
        Write-Step "git pull --rebase"
        git pull --rebase 2>&1 | ForEach-Object { Write-Host "   $_" }
        if ($LASTEXITCODE -ne 0) {
            # Second attempt: sync straight to the remote, but only if there is nothing of the
            # user's own to lose (no local commits). Local commits are never discarded here.
            $branch = (git rev-parse --abbrev-ref HEAD).Trim()
            Write-Warn2 "pull failed; checking whether a clean sync is safe"
            git fetch origin 2>$null | Out-Null
            $localCommits = 0
            if ($branch) {
                $localCommits = [int](git rev-list --count "origin/$branch..HEAD" 2>$null)
            }
            if ($branch -and $localCommits -eq 0) {
                Write-Warn2 "no local commits to lose - syncing to origin/$branch"
                git reset --hard "origin/$branch" 2>&1 | ForEach-Object { Write-Host "   $_" }
                if ($LASTEXITCODE -ne 0) {
                    Write-Bad "could not sync. Run these two lines and re-run the script:"
                    Write-Warn2 "  git rebase --abort"
                    Write-Warn2 "  git reset --hard origin/$branch"
                    exit 1
                }
                Write-Ok "synced to $branch"
            } else {
                Write-Bad "pull failed and you have $localCommits local commit(s) - not discarding them."
                Write-Warn2 "to keep them:   git branch backup-local-corpus HEAD"
                Write-Warn2 "to discard them: git reset --hard origin/$branch"
                exit 1
            }
        }
    } else {
        Write-Step "skipping pull (-NoPull)"
    }

    # regenerate the comparison table so the docs match the files on disk
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python tools/compare_vehicles.py --out docs/VEHICLE-COMPARISON.md 2>$null | Out-Null
    }

    $head = (git log --oneline -1)
    Write-Step "on commit: $head"

    # ------------------------------------------------------------------------- copy
    $yaml = Join-Path $Repo 'Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml'
    $reds = Join-Path $Repo 'Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie'
    $destYamlDir = Join-Path $GameRoot 'r6\tweaks\phoenix'
    $destRedsDir = Join-Path $GameRoot 'r6\scripts\phoenix_aston_valkyrie'

    $pairs = @()
    if (-not $NoCopy) {
        if (-not (Test-Path (Join-Path $GameRoot 'r6'))) {
            Write-Bad "game folder not found or wrong: $GameRoot"
            Write-Warn2 "pass it with -GameRoot `"X:\...\Cyberpunk 2077 Phantom Liberty`""
            exit 1
        }
        Write-Step "installing into $GameRoot"
        New-Item -ItemType Directory -Force -Path $destYamlDir, $destRedsDir | Out-Null
        Copy-Item $yaml $destYamlDir -Force
        Copy-Item (Join-Path $reds '*') $destRedsDir -Force
        Write-Ok "phoenix_aston_valkyrie.yaml -> r6\tweaks\phoenix\"
        Write-Ok "4 x .reds              -> r6\scripts\phoenix_aston_valkyrie\"

        # standalone speedometer: its own folder, own Mod Settings tab, no car required
        $speedo = Join-Path $Repo 'Phoenix_true_speedometer\r6\scripts\phoenix_true_speedometer'
        if (Test-Path $speedo) {
            $destSpeedo = Join-Path $GameRoot 'r6\scripts\phoenix_true_speedometer'
            New-Item -ItemType Directory -Force -Path $destSpeedo | Out-Null
            Copy-Item (Join-Path $speedo '*.reds') $destSpeedo -Force
            Write-Ok "phoenix_true_speedometer.reds -> r6\scripts\phoenix_true_speedometer\"
            foreach ($f in Get-ChildItem $speedo -Filter *.reds) {
                $pairs += ,@($f.FullName, (Join-Path $destSpeedo $f.Name))
            }
        }

        $pairs += ,@($yaml, (Join-Path $destYamlDir 'phoenix_aston_valkyrie.yaml'))
        foreach ($f in Get-ChildItem $reds -Filter *.reds) {
            $pairs += ,@($f.FullName, (Join-Path $destRedsDir $f.Name))
        }
    }

    # --------------------------------------------------------------------- verify
    if ($pairs.Count -gt 0) {
        Write-Step "verifying (repo vs installed)"
        $bad = 0
        foreach ($pair in $pairs) {
            $name = Split-Path $pair[0] -Leaf
            if (-not (Test-Path $pair[1])) { Write-Bad "$name : missing in game folder"; $bad++; continue }
            $a = (Get-FileHash $pair[0] -Algorithm SHA256).Hash
            $b = (Get-FileHash $pair[1] -Algorithm SHA256).Hash
            if ($a -eq $b) { Write-Ok "$name  identical" } else { Write-Bad "$name  DIFFERS"; $bad++ }
        }
        if ($bad -gt 0) { Write-Bad "$bad file(s) did not install cleanly"; exit 1 }
    }

    # ----------------------------------------------------- what this build actually is
    $engineLine = Select-String -Path $yaml -Pattern 'vehEngineData: Vehicle\.phoenix_amv_engine' -Quiet
    $gearLine   = Select-String -Path $yaml -Pattern 'gears: \[ Vehicle\.phoenix_amv_gear_r' -Quiet
    Write-Step "build check"
    if ($engineLine) { Write-Ok "physics attached by named record (engine)" } else { Write-Warn2 "engine block is still inline" }
    if ($gearLine)   { Write-Ok "gearbox is one explicit list" } else { Write-Warn2 "gearbox shape unexpected" }

    # ------------------------------------------------------------ build stamp
    # The scanner reads VehicleUIData.horsepower, which carries 900000 + BUILD. After a restart the
    # scanner must show this number; if it does not, the game is reading something else.
    $stamp = (Select-String -Path $yaml -Pattern 'horsepower:\s*(\d+)' | Select-Object -First 1)
    Write-Step "build stamp"
    if ($stamp) {
        $code = $stamp.Matches[0].Groups[1].Value
        Write-Host "  scanner will read: " -NoNewline
        Write-Host $code -ForegroundColor Cyan -NoNewline
        Write-Host ("  (build {0})" -f ([int]$code - 900000))
        Write-Warn2 "if the scanner shows a different number after restarting, the game is reading another file"
    } else {
        Write-Warn2 "no build stamp found in the YAML"
    }

    Write-Host ""
    Write-Host "Done. Start the game (TweakXL reads YAML at boot - a restart is required)." -ForegroundColor Green
    Write-Host "CET 'reload all mods' does NOT re-read tweak YAML - verified 2026-11-24." -ForegroundColor Yellow
} finally {
    Pop-Location
}
