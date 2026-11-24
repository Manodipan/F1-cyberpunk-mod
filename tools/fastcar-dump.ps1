# Rank every vehicle tweak installed in the game by top-speed ceiling, and dump the
# handful of numbers that decide speed and stability.
#
# Why: a car that reaches 572 km/h is proof the game will go past the vanilla gear
# ceiling, and its airResistanceFactor / steering / damping values are what "stable
# enough at 500" looks like in practice. Reading those numbers beats guessing at ours.
#
#   powershell -ExecutionPolicy Bypass -File .\tools\fastcar-dump.ps1
#   powershell -ExecutionPolicy Bypass -File .\tools\fastcar-dump.ps1 -Tweaks "G:\...\r6\tweaks\some_mod"
#
# Writes .\fastcar.txt next to the clone root and opens it. Paste the whole file.

param(
    [string]$Game = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Tweaks = "",
    [string]$Out = ""
)

$ErrorActionPreference = "Continue"

if (-not $Tweaks) { $Tweaks = Join-Path $Game "r6\tweaks" }
if (-not $Out)    { $Out = Join-Path (Split-Path -Parent $PSScriptRoot) "fastcar.txt" }

# the fields that decide how fast a car goes and whether it stays on the road
$keys = @(
    "airResistanceFactor", "engineMaxTorque", "maxRPM", "total_mass", "chassis_mass",
    "turningRollFactor", "wheelTurnMaxAddPerSecond", "turnUpdateMaxSpeedThreshold",
    "turnUpdateMaxSpeedTurnMul", "maxAngularSpeedRad", "driftLimit",
    "maxSpeedFactorGround", "maxSpeedFactorAir", "minLatFrictionCoef",
    "frictionMulLateral", "frictionMulLongitudinal", "springStiffness", "springDamping",
    "swaybarStiffness", "center_of_mass_offset"
)

$out = New-Object System.Collections.Generic.List[string]
function Section($t) { $out.Add(""); $out.Add("================ $t ================") }

Section "WHERE"
$out.Add("tweaks : $Tweaks")
$out.Add("date   : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
if (-not (Test-Path $Tweaks)) { $out.Add("!! path not found"); $out | Out-File $Out -Encoding utf8; Start-Process notepad.exe $Out; exit 1 }

$files = Get-ChildItem -Path $Tweaks -Filter *.yaml -Recurse -ErrorAction SilentlyContinue
$out.Add("yaml files : $($files.Count)")

# ---- 1. every vehicle file ranked by its highest gear maxSpeed -------------------
$rows = @()
foreach ($f in $files) {
    $t = [IO.File]::ReadAllText($f.FullName)
    if ($t -notmatch "airResistanceFactor|gears\s*:") { continue }
    $speeds = [regex]::Matches($t, "(?m)^\s*maxSpeed\s*:\s*([0-9]+(?:\.[0-9]+)?)") |
              ForEach-Object { [double]$_.Groups[1].Value }
    if (-not $speeds -or $speeds.Count -eq 0) { continue }
    $top = ($speeds | Measure-Object -Maximum).Maximum
    $rows += [pscustomobject]@{
        kmh      = [math]::Round($top * 3.6)
        ms       = $top
        gears    = $speeds.Count
        file     = $f.FullName.Replace($Tweaks, "").TrimStart("\")
    }
}

Section "RANKED BY TOP GEAR (km/h = maxSpeed m/s x 3.6)"
if ($rows.Count -eq 0) {
    $out.Add("(no vehicle yaml with gear maxSpeed found here)")
} else {
    foreach ($r in ($rows | Sort-Object kmh -Descending)) {
        $out.Add(("{0,5} km/h  ({1,6} m/s)  {2,2} gears   {3}" -f $r.kmh, $r.ms, $r.gears, $r.file))
    }
}

# ---- 2. the interesting numbers for anything that claims > 400 km/h -------------
Section "FIELDS FOR THE FAST ONES (> 400 km/h)"
foreach ($r in ($rows | Where-Object { $_.kmh -gt 400 } | Sort-Object kmh -Descending)) {
    $path = Join-Path $Tweaks $r.file
    $out.Add("")
    $out.Add("--- $($r.file)   top $($r.kmh) km/h, $($r.gears) gears")
    $all = Get-Content $path
    for ($i = 0; $i -lt $all.Count; $i++) {
        foreach ($k in $keys) {
            if ($all[$i] -match ("^\s*" + [regex]::Escape($k) + "\s*:")) {
                $out.Add(("{0,5}: {1}" -f ($i + 1), $all[$i].Trim()))
                break
            }
        }
        if ($all[$i] -match "^\s*maxSpeed\s*:") {
            $out.Add(("{0,5}: {1}" -f ($i + 1), $all[$i].Trim()))
        }
    }
}

Section "HOW TO READ THIS"
$out.Add("Ours is phoenix\phoenix_aston_valkyrie.yaml and must show 138.89 m/s (500 km/h).")
$out.Add("If the fast car's top gear is bigger and its airResistanceFactor is lower,")
$out.Add("those two numbers are the whole difference. Steering / damping / friction")
$out.Add("values show what 'stable at 500' looks like next to our 94 / 0.33 / 1.60-2.00.")

$out | Out-File -FilePath $Out -Encoding utf8
Write-Host ""
Write-Host "written: $Out"
Write-Host "lines  : $($out.Count)"
Start-Process notepad.exe $Out
