#Requires -Version 5.1
<#
.SYNOPSIS
    Remove this mod from Cyberpunk 2077 (a reversible uninstall: it backs the files up first).

.DESCRIPTION
    Deletes exactly the things update.ps1 installs, and nothing else:

        r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml
        r6\scripts\phoenix_aston_valkyrie\  (4 x .reds)

    Everything else in the game folder is left alone - including Auto Drive Enhanced, which
    this repo only carries a read-only copy of for reference.

    Because the tweak YAML only overrides specific fields (mass, drag, torque, gear 7), removing
    it returns the car to stock physics; there is no "stock restore" step to run afterwards.

    The removed files are copied to a timestamped backup folder under your home directory, so
    reinstalling by hand is a Copy-Item away.

.PARAMETER GameRoot
    Cyberpunk 2077 install folder (the one containing r6\).

.PARAMETER KeepScripts
    Remove only the tweak YAML (the physics), and leave the four .reds in place. That keeps the
    dashboard working - gear, rev lights and the true physics-speed readout - on a stock car.
    The scripts do not read the YAML, so this is a valid mix.

.PARAMETER WithSpeedometer
    Also remove the Phoenix True Speedometer HUD (bin\x64\plugins\cyber_engine_tweaks\mods\
    phoenix_true_speedometer\). Off by default: uninstalling the car must not take the speedometer
    with it.

.PARAMETER Purge
    Do not keep a backup. Cannot be undone.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\uninstall.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\uninstall.ps1 -Purge
#>
[CmdletBinding()]
param(
    [string]$GameRoot = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [switch]$KeepScripts,
    [switch]$WithSpeedometer,
    [switch]$Purge
)

$ErrorActionPreference = 'Stop'

function Write-Step($text) { Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "   $text" -ForegroundColor Green }
function Write-Warn2($text) { Write-Host "   $text" -ForegroundColor Yellow }
function Write-Bad($text) { Write-Host "   $text" -ForegroundColor Red }

if (-not (Test-Path (Join-Path $GameRoot 'r6'))) {
    Write-Bad "no r6 folder in: $GameRoot"
    Write-Warn2 "pass the game folder with -GameRoot `"D:\Games\Cyberpunk 2077`"  (quote it: the path has spaces)"
    exit 1
}

$yaml      = Join-Path $GameRoot 'r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml'
$redsDir   = Join-Path $GameRoot 'r6\scripts\phoenix_aston_valkyrie'
$speedoDir = Join-Path $GameRoot 'r6\scripts\phoenix_true_speedometer'          # retired redscript build
$speedoLuaDir = Join-Path $GameRoot 'bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer'

$found = @()
if (Test-Path $yaml)    { $found += Get-Item $yaml }
if ((Test-Path $redsDir) -and -not $KeepScripts) { $found += Get-ChildItem $redsDir -Filter '*.reds' -File }
if ((Test-Path $speedoDir) -and -not $KeepScripts) { $found += Get-ChildItem $speedoDir -Filter '*.reds' -File }
if ((Test-Path $speedoLuaDir) -and $WithSpeedometer) { $found += Get-ChildItem $speedoLuaDir -Filter '*.lua' -File }

if ($found.Count -eq 0) {
    Write-Step "nothing to remove"
    Write-Ok "the car is not installed in $GameRoot"
    if ((Test-Path $speedoLuaDir) -and -not $WithSpeedometer) {
        Write-Ok "the speedometer HUD is installed and stays  (add -WithSpeedometer to remove it)"
    }
    exit 0
}

Write-Step "found $($found.Count) file(s) installed"
foreach ($f in $found) { Write-Ok $f.Name }

# ---------------------------------------------------------------- back up
if (-not $Purge) {
    $backup = Join-Path $HOME ("phoenix-uninstall-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path (Join-Path $backup 'tweaks') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $backup 'scripts') -Force | Out-Null
    if (Test-Path $yaml)    { Copy-Item $yaml (Join-Path $backup 'tweaks') -Force }
    if (Test-Path $redsDir) { Copy-Item (Join-Path $redsDir '*') (Join-Path $backup 'scripts') -Force }
    if (Test-Path $speedoDir) { Copy-Item (Join-Path $speedoDir '*') (Join-Path $backup 'scripts') -Force }
    if ((Test-Path $speedoLuaDir) -and $WithSpeedometer) {
        New-Item -ItemType Directory -Path (Join-Path $backup 'cet') -Force | Out-Null
        Copy-Item (Join-Path $speedoLuaDir '*') (Join-Path $backup 'cet') -Force
    }
    Write-Step "backed up to $backup"
}

# ---------------------------------------------------------------- remove
Write-Step "removing"
if (Test-Path $yaml) {
    Remove-Item $yaml -Force
    Write-Ok "deleted r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml"
}
if (Test-Path $speedoLuaDir) {
    if ($WithSpeedometer) {
        Remove-Item $speedoLuaDir -Recurse -Force
        Write-Ok "deleted cyber_engine_tweaks\mods\phoenix_true_speedometer\"
    } else {
        Write-Ok "kept the speedometer HUD  (add -WithSpeedometer to remove it too)"
    }
}
if (Test-Path $speedoDir) {
    if ($KeepScripts) {
        Write-Ok "kept r6\scripts\phoenix_true_speedometer\  (speedometer stays)"
    } else {
        Remove-Item $speedoDir -Recurse -Force
        Write-Ok "deleted r6\scripts\phoenix_true_speedometer\"
    }
}
if (Test-Path $redsDir) {
    if ($KeepScripts) {
        Write-Ok "kept r6\scripts\phoenix_aston_valkyrie\  (dashboard + true speed readout stay)"
    } else {
        # the folder is ours alone; removing only the .reds would leave an empty folder the game scans
        Remove-Item $redsDir -Recurse -Force
        Write-Ok "deleted r6\scripts\phoenix_aston_valkyrie\"
    }
}

# ---------------------------------------------------------------- verify
Write-Step "verify"
$left = @()
if (Test-Path $yaml)    { $left += $yaml }
if ((Test-Path $redsDir) -and -not $KeepScripts) { $left += $redsDir }
if ($left.Count -eq 0) {
    Write-Ok "gone - nothing of ours is left in the game folder"
} else {
    Write-Bad "still present: $($left -join ', ')"
    Write-Warn2 "close the game and run it again"
    exit 1
}

Write-Step "untouched"
Write-Ok "r6\scripts\auto_drive_enhanced\  (ADE - never ours to modify)"
Write-Ok "every other mod, and every other tweak file"

Write-Host ""
Write-Step "next"
Write-Warn2 "start the game fresh: TweakXL reads YAML at boot, CET reload will not do it"
Write-Warn2 "expect the stock car and no build stamp in the scanner"
if ($KeepScripts) { Write-Warn2 "dashboard stays: gear, rev lights and true m/s on the wheel screen" }
if (-not $Purge) { Write-Warn2 "reinstall: powershell -ExecutionPolicy Bypass -File .\tools\update.ps1" }
