#Requires -Version 5.1
<#
.SYNOPSIS
    Install ONLY the dashboard scripts - gear, rev lights and true physics-speed readout - with no
    physics changes at all.

.DESCRIPTION
    Copies the four .reds and nothing else. The tweak YAML (mass, drag, torque, gear 7) is not
    installed, so the car stays completely stock while the wheel screen keeps working.

    The scripts read the vehicle record, not the tweak file, so this is a valid mix: the dash shows
    the real body velocity in km/h, computed from the physics, instead of the game's derived dial.

    This is the counterpart to tools\uninstall.ps1 -KeepScripts (which keeps scripts that are
    already installed); this one puts them back if they were already removed.

.PARAMETER GameRoot
    Cyberpunk 2077 install folder (the one containing r6\).

.PARAMETER Repo
    This repository's clone folder.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\install-dash.ps1
#>
[CmdletBinding()]
param(
    [string]$GameRoot = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Repo = "$HOME\f1-cyberpunk-mod"
)

$ErrorActionPreference = 'Stop'

function Write-Step($text) { Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "   $text" -ForegroundColor Green }
function Write-Warn2($text) { Write-Host "   $text" -ForegroundColor Yellow }
function Write-Bad($text) { Write-Host "   $text" -ForegroundColor Red }

$src  = Join-Path $Repo 'Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie'
$dest = Join-Path $GameRoot 'r6\scripts\phoenix_aston_valkyrie'

if (-not (Test-Path (Join-Path $GameRoot 'r6'))) {
    Write-Bad "no r6 folder in: $GameRoot"
    Write-Warn2 "pass the game folder with -GameRoot `"D:\Games\Cyberpunk 2077`"  (quote it: the path has spaces)"
    exit 1
}
if (-not (Test-Path $src)) {
    Write-Bad "scripts not found in the repo: $src"
    Write-Warn2 "pass the clone folder with -Repo `"C:\path\to\f1-cyberpunk-mod`""
    exit 1
}

# ---------------------------------------------------------------- the YAML must be ABSENT
$yaml = Join-Path $GameRoot 'r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml'
if (Test-Path $yaml) {
    Write-Step "note"
    Write-Warn2 "the physics tweak is still installed at r6\tweaks\phoenix\"
    Write-Warn2 "this script does not remove it - run tools\uninstall.ps1 for a stock car"
}

# ---------------------------------------------------------------- copy
Write-Step "installing dashboard scripts only"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item (Join-Path $src '*.reds') $dest -Force
Write-Ok "4 x .reds -> r6\scripts\phoenix_aston_valkyrie\"

# ---------------------------------------------------------------- verify by hash
Write-Step "verify"
$bad = 0
foreach ($f in Get-ChildItem (Join-Path $src '*.reds')) {
    $to = Join-Path $dest $f.Name
    if (-not (Test-Path $to)) { Write-Bad "missing: $($f.Name)"; $bad++; continue }
    $a = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
    $b = (Get-FileHash $to -Algorithm SHA256).Hash
    if ($a -eq $b) { Write-Ok "$($f.Name)  ok" } else { Write-Bad "$($f.Name)  hash differs"; $bad++ }
}
if ($bad -gt 0) { exit 1 }

Write-Step "physics"
if (Test-Path $yaml) { Write-Warn2 "tweak YAML present - the car is NOT stock" }
else { Write-Ok "no tweak YAML: the car is stock, only the dashboard is ours" }

Write-Host ""
Write-Step "next"
Write-Warn2 "start the game fresh - redscript compiles at boot, a CET reload will not do it"
Write-Ok "wheel screen: gear, rev lights, true speed in km/h from the vehicle body"
