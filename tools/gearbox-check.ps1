# Why does the Phoenix stop at ~330 km/h?
#
# 330 km/h = 91.7 m/s = the STOCK Valkyrie's gear-7 maxSpeed. Our port replaced that
# record with 138.89 m/s (500 km/h), so a hard plateau on 91.7 means the game is still
# reading the old gear set — not that the car is out of power (with 2000 hp and drag 0.90
# the terminal speed would be well past 500).
#
# This writes ONE file with everything needed to tell those apart:
#   * the INSTALLED tweak (game folder, not the repo) — the actual gear-7 value
#   * whether the gears: !remove / !append block is intact
#   * TweakXL / redscript / CET log lines mentioning phoenix or errors
#
#   powershell -ExecutionPolicy Bypass -File .\tools\gearbox-check.ps1
#
# Writes .\gearbox_check.txt next to the clone root and opens it in Notepad.

param(
    [string]$Game = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Out  = ""
)

$ErrorActionPreference = "Continue"

if (-not $Out) { $Out = Join-Path (Split-Path -Parent $PSScriptRoot) "gearbox_check.txt" }

$yaml = Join-Path $Game "r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml"
$stockYaml = Join-Path $Game "r6\tweaks\xaires\aston_valkyrie.yaml"

$logCandidates = @(
    (Join-Path $Game "red4ext\logs\TweakXL.log"),
    (Join-Path $Game "red4ext\logs\tweakxl.log"),
    (Join-Path $Game "red4ext\logs\red4ext.log"),
    (Join-Path $Game "red4ext\logs\ArchiveXL.log"),
    (Join-Path $Game "r6\logs\tweakxl.log"),
    (Join-Path $Game "r6\logs\redscript_rCURRENT.log"),
    (Join-Path $Game "bin\x64\plugins\cyber_engine_tweaks\cyber_engine_tweaks.log")
)

$lines = New-Object System.Collections.Generic.List[string]
function Section($t) { $lines.Add(""); $lines.Add("================ $t ================") }

Section "WHERE"
$lines.Add("game : $Game")
$lines.Add("yaml : $yaml")
$lines.Add("date : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))

Section "IS OUR TWEAK THE ONE INSTALLED?"
if (-not (Test-Path $yaml)) {
    $lines.Add("!! NOT FOUND - the phoenix tweak is not in the game folder.")
    $lines.Add("   Whatever the car is doing, it is not doing it with our YAML.")
} else {
    $fi = Get-Item $yaml
    $lines.Add("size : $($fi.Length) bytes")
    $lines.Add("date : $($fi.LastWriteTime)")
    $txt = [IO.File]::ReadAllText($yaml)
    $hits = ([regex]::Matches($txt, "138\.89")).Count
    $lines.Add("occurrences of 138.89 (the 500 km/h ceiling) : $hits")
    $removes = ([regex]::Matches($txt, "!\s*remove")).Count
    $appends = ([regex]::Matches($txt, "!\s*append")).Count
    $lines.Add("gears block : $removes !remove, $appends !append")
    if ($hits -eq 0) { $lines.Add("!! the installed file has NO 138.89 - it is the old gear set") }
    if ($appends -lt 8) { $lines.Add("!! fewer than 8 appended gears - the block is damaged") }
}

Section "GEAR 6 / GEAR 7 AS INSTALLED"
if (Test-Path $yaml) {
    $all = Get-Content $yaml
    $idx = @()
    for ($i = 0; $i -lt $all.Count; $i++) {
        if ($all[$i] -match "phoenix_amv_gear_[67]\s*:") { $idx += $i }
    }
    if ($idx.Count -eq 0) { $lines.Add("!! no Vehicle.phoenix_amv_gear_6 / _7 records in the installed file") }
    foreach ($i in $idx) {
        for ($j = $i; $j -lt $i + 8 -and $j -lt $all.Count; $j++) { $lines.Add(("{0,4}: {1}" -f ($j + 1), $all[$j])) }
        $lines.Add("")
    }
}

Section "STOCK VALKYRIE FOR COMPARISON (its gear 7 is the 91.7 m/s we suspect)"
if (Test-Path $stockYaml) {
    $s = Get-Content $stockYaml
    $found = $false
    for ($i = 0; $i -lt $s.Count; $i++) {
        if ($s[$i] -match "gear_?7\s*:") {
            $found = $true
            for ($j = $i; $j -lt $i + 7 -and $j -lt $s.Count; $j++) { $lines.Add(("{0,4}: {1}" -f ($j + 1), $s[$j])) }
        }
    }
    if (-not $found) { $lines.Add("(no gear_7 record found by name)") }
} else {
    $lines.Add("(stock yaml not installed - fine, the Phoenix does not need it)")
}

Section "STEERING VALUES AS INSTALLED (did the stability tweak land?)"
if (Test-Path $yaml) {
    $h = Select-String -Path $yaml -Pattern "wheelTurnMaxAddPerSecond|turnUpdateMaxSpeedThreshold|turnUpdateMaxSpeedTurnMul|airResistanceFactor"
    foreach ($x in $h) { $lines.Add(("  " + $x.Line.Trim())) }
}

Section "LOGS (phoenix / gear / error lines, last 25 per file)"
foreach ($log in $logCandidates) {
    $lines.Add("--- $log")
    if (Test-Path $log) {
        $hits = Select-String -Path $log -Pattern "phoenix|gear|rror|ambiguous|Ambiguous" -ErrorAction SilentlyContinue |
                Select-Object -Last 25
        if (-not $hits) { $lines.Add("(no matching lines)") }
        foreach ($h in $hits) { $lines.Add($h.Line.Trim()) }
    } else {
        $lines.Add("(missing)")
    }
}

Section "HOW TO READ THIS"
$lines.Add("1. 'NOT FOUND' or 'NO 138.89'  -> the installed tweak is stale; reinstall the mod.")
$lines.Add("2. file is fine, but the TweakXL log complains about gears/phoenix")
$lines.Add("   -> the !append did not take; that is the 330 km/h wall.")
$lines.Add("3. everything clean -> the wall is drag after all, and airResistanceFactor 0.90")
$lines.Add("   comes down until the car reaches 138.89 m/s.")
$lines.Add("")
$lines.Add("Decide it in game either way: at the plateau, are the rev lights maxed")
$lines.Add("(engine pinned = gear/limiter) or mid-scale (engine still has headroom = drag)?")

$a = @($lines)
$a | Out-File -FilePath $Out -Encoding utf8
Write-Host ""
Write-Host "written: $Out"
Write-Host "lines  : $($a.Count)"
Start-Process notepad.exe $Out
