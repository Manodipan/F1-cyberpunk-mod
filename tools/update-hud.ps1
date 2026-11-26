#Requires -Version 5.1
<#
.SYNOPSIS
    Update the speedometer HUD and prove, by hash, exactly which file the game will load.

.DESCRIPTION
    Does four things in order and stops at the first problem:

        1. pulls the branch (fails loudly rather than installing a stale tree)
        2. prints the build stamp and the expected hash from the repo's .sha256 file
        3. installs init.lua into CET's mods folder
        4. re-reads the installed file and prints its hash, checked against the expected one

    If step 4 does not match, the install is not to be trusted and this exits non-zero.

.PARAMETER GameRoot
    Cyberpunk 2077 install folder (the one containing r6\ and bin\).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\update-hud.ps1
#>
[CmdletBinding()]
param(
    [string]$GameRoot = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Repo = "$HOME\f1-cyberpunk-mod"
)

$ErrorActionPreference = 'Stop'

function Write-Step($text) { Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok($text)   { Write-Host "   $text" -ForegroundColor Green }
function Write-Bad($text)  { Write-Host "   $text" -ForegroundColor Red }

Write-Step "repo"
if (-not (Test-Path $Repo)) { Write-Bad "not found: $Repo"; exit 1 }
Push-Location $Repo
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    Write-Ok "branch: $branch"

    Write-Step "pull"
    git pull --rebase
    if ($LASTEXITCODE -ne 0) {
        Write-Bad "git pull failed - nothing was installed"
        exit 1
    }
    $head = (git log --oneline -1)
    Write-Ok "on commit: $head"

    $src  = Join-Path $Repo 'Phoenix_true_speedometer\probe\init.lua'
    $stamp = "$src.sha256"
    if (-not (Test-Path $src)) { Write-Bad "missing $src - is the branch up to date?"; exit 1 }

    Write-Step "the file"
    $srcHash = (Get-FileHash $src -Algorithm SHA256).Hash
    $lines   = (Get-Content $src).Count
    $build   = (Select-String -Path $src -Pattern 'local BUILD = ' -SimpleMatch | Select-Object -First 1).Line
    Write-Ok "path : $src"
    Write-Ok "lines: $lines"
    Write-Ok "build: $($build.Trim())"
    Write-Ok "hash : $srcHash"

    $expected = $null
    if (Test-Path $stamp) {
        $expected = (Get-Content $stamp -Raw).Trim().ToUpper()
        Write-Ok "stamp: $expected"
        if ($srcHash -ne $expected) {
            Write-Bad "the repo file does not match its own .sha256 stamp"
            Write-Bad "this tree is inconsistent - do not install it"
            exit 1
        }
        Write-Ok "repo file VERIFIED against its stamp"
    } else {
        Write-Host "   no .sha256 stamp - cannot verify (continuing)" -ForegroundColor Yellow
    }

    Write-Step "install"
    $cetMods = Join-Path $GameRoot 'bin\x64\plugins\cyber_engine_tweaks\mods'
    if (-not (Test-Path $cetMods)) {
        Write-Bad "CET mods folder not found: $cetMods"
        Write-Bad 'pass -GameRoot "X:\path\to\Cyberpunk 2077"'
        exit 1
    }
    $dest = Join-Path $cetMods 'phoenix_true_speedometer'
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item $src (Join-Path $dest 'init.lua') -Force
    Write-Ok "wrote $(Join-Path $dest 'init.lua')"

    # the old separate probe folder is retired; leaving it would draw twice
    $oldProbe = Join-Path $cetMods 'phoenix_probe'
    if (Test-Path $oldProbe) {
        Remove-Item $oldProbe -Recurse -Force
        Write-Ok "removed the old phoenix_probe folder"
    }

    Write-Step "verify the installed file"
    $instHash = (Get-FileHash (Join-Path $dest 'init.lua') -Algorithm SHA256).Hash
    Write-Ok "installed hash: $instHash"
    if ($instHash -ne $srcHash) {
        Write-Bad "installed file differs from the repo file - the copy did not take"
        exit 1
    }
    if ($expected -and $instHash -ne $expected) {
        Write-Bad "installed file differs from the recorded build hash"
        exit 1
    }
    Write-Ok "VERIFIED: the game will load exactly the build above"

    Write-Step "what to expect in game"
    Write-Ok "console (~) or cyber_engine_tweaks.log:"
    Write-Ok "  [PhoenixSpeed] init.lua executed ($($build -replace '.*\"(.*)\".*','$1'))"
    Write-Ok "with the overlay open, the window shows: BUILD <stamp>  frames=N"
    Write-Ok "position is shown as: Position: free|top|bottom   (only free can be dragged)"
} finally {
    Pop-Location
}
