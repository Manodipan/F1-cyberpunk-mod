#Requires -Version 5.1
<#
.SYNOPSIS
    One-shot check of the Phoenix True Speedometer HUD: is it installed, did CET load it, what did
    CET say about it.

.DESCRIPTION
    Answers, in order:

        1. Where the game and CET are, and whether the CET mods folder exists
        2. Whether the HUD's init.lua is installed, and whether it matches the repo copy
        3. What the other CET mods are (so a conflict is visible)
        4. Every line in CET's log that mentions this mod, plus any scripting errors

    Nothing is written or deleted; it only reads.

.PARAMETER GameRoot
    Cyberpunk 2077 install folder (the one containing r6\ and bin\).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\tools\check-hud.ps1

.EXAMPLE
    .\tools\check-hud.ps1 -GameRoot "D:\Steam\steamapps\common\Cyberpunk 2077"
#>
[CmdletBinding()]
param(
    [string]$GameRoot = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty"
)

$ErrorActionPreference = 'Continue'
$Repo = Split-Path $PSScriptRoot -Parent

function Write-Step($text) { Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok($text)   { Write-Host "   $text" -ForegroundColor Green }
function Write-Warn2($text){ Write-Host "   $text" -ForegroundColor Yellow }
function Write-Bad($text)  { Write-Host "   $text" -ForegroundColor Red }

Write-Step "game folder"
if (-not (Test-Path $GameRoot)) {
    Write-Bad "not found: $GameRoot"
    Write-Warn2 'pass it with -GameRoot "X:\path\to\Cyberpunk 2077"'
    exit 1
}
Write-Ok $GameRoot

$cetRoot  = Join-Path $GameRoot 'bin\x64\plugins\cyber_engine_tweaks'
$cetMods  = Join-Path $cetRoot 'mods'
$cetLog   = Join-Path $cetRoot 'cyber_engine_tweaks.log'
$installed = Join-Path $cetMods 'phoenix_true_speedometer\init.lua'
$repoFile  = Join-Path $Repo 'Phoenix_true_speedometer\probe\init.lua'

Write-Step "cyber engine tweaks"
if (Test-Path $cetRoot) { Write-Ok $cetRoot } else { Write-Bad "CET is not installed at $cetRoot"; exit 1 }
if (Test-Path $cetMods) { Write-Ok "mods folder present" } else { Write-Bad "no mods folder - start the game once with CET"; exit 1 }

Write-Step "the HUD"
if (Test-Path $installed) {
    $a = (Get-FileHash $installed -Algorithm SHA256).Hash
    $size = (Get-Item $installed).Length
    Write-Ok "installed: $installed ($size bytes)"
    Write-Ok "installed hash: $a"
    if (Test-Path $repoFile) {
        $b = (Get-FileHash $repoFile -Algorithm SHA256).Hash
        Write-Ok "repo hash     : $b"
        if ($a -eq $b) { Write-Ok "match - the installed file is the one in the repo" }
        else { Write-Warn2 "MISMATCH - run .\tools\update.ps1 again (or the repo is on another commit)" }
    }
} else {
    Write-Bad "NOT INSTALLED at $installed"
    Write-Warn2 "run .\tools\update.ps1 and look for the line:"
    Write-Warn2 "  init.lua -> bin\x64\plugins\cyber_engine_tweaks\mods\phoenix_true_speedometer\"
}

Write-Step "other CET mods"
Get-ChildItem $cetMods -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $hasInit = Test-Path (Join-Path $_.FullName 'init.lua')
    $label = if ($hasInit) { '' } else { '  (no init.lua)' }
    Write-Ok ($_.Name + $label)
}

Write-Step "settings.ini"
$ini = Join-Path $cetMods 'phoenix_true_speedometer\unit.txt'
if (Test-Path $ini) {
    Get-Content $ini | ForEach-Object { Write-Ok $_ }
    Write-Ok ("chosen unit: " + (Get-Content $ini -First 1))
} else {
    Write-Warn2 "no settings.ini - the mod has never run (this is written on first load)"
}

Write-Step "CET log"
if (Test-Path $cetLog) {
    $lines = Get-Content $cetLog
    Write-Ok ("{0} lines, last written {1}" -f $lines.Count, (Get-Item $cetLog).LastWriteTime)
    $hits = $lines | Select-String -Pattern 'PhoenixSpeed|phoenix_true_speedometer|scripting' |
            Select-Object -Last 40
    if ($hits) {
        Write-Step "lines about this mod / scripting"
        $hits | ForEach-Object { Write-Host ("   " + $_.Line) }
    } else {
        Write-Warn2 "nothing about the mod in the log yet"
    }
    Write-Step "last 15 lines of the log"
    $lines | Select-Object -Last 15 | ForEach-Object { Write-Host ("   " + $_) }
} else {
    Write-Warn2 "no log at $cetLog - has the game been launched since CET was installed?"
}

Write-Step "what to look for"
Write-Ok "1. this line on load, in the console (~) or the log:"
Write-Ok "     [PhoenixSpeed] init.lua executed"
Write-Ok "2. two seconds into the game:"
Write-Ok "     [PhoenixSpeed] 2 s in: vehicle=... speed=... unit=..."
Write-Ok "no line 1 = the file is not being loaded; line 1 but no line 2 = onDraw is not running."
Write-Ok "the window should be visible from the main menu, showing '-- km/h' with no vehicle."
