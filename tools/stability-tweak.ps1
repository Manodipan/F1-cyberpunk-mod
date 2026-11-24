# High-speed steering profile — optional local experiment (see docs/TOPSPEED-TEST.md)
#
# The shipped car keeps the stock steering numbers (94 / 26 / 0.33) on purpose: they are
# what the Valkyrie LMH was tuned for at 330 km/h. At 500 km/h the same wheel angle makes
# roughly twice the lateral acceleration, which is what "slight nudges make it wobble"
# feels like: the tyres bite, the body rolls, the driver corrects, and the correction is
# just as oversized as the original input.
#
# This script does NOT change the repo deliverable. It edits only the copy installed in
# the game, keeps a .orig backup, and is reversible:
#
#   powershell -ExecutionPolicy Bypass -File .\tools\stability-tweak.ps1
#   powershell -ExecutionPolicy Bypass -File .\tools\stability-tweak.ps1 -Revert
#
# Restart the game afterwards (TweakXL reads YAML at boot).

param(
    [string]$Game = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [switch]$Revert
)

$ErrorActionPreference = "Stop"

$yaml = Join-Path $Game "r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml"
$orig = "$yaml.orig"
$utf8 = New-Object System.Text.UTF8Encoding($false)

Write-Host ""
Write-Host "file: $yaml"
if (-not (Test-Path $yaml)) { Write-Host "!! not found - is the mod installed in that game folder?"; exit 1 }

if ($Revert) {
    if (-not (Test-Path $orig)) { Write-Host "!! no backup ($orig) - nothing to revert to"; exit 1 }
    Copy-Item $orig $yaml -Force
    Write-Host "reverted from the .orig backup"
    Select-String -Path $yaml -Pattern "wheelTurnMaxAddPerSecond|turnUpdateMaxSpeedTurnMul|turnUpdateMaxSpeedThreshold" |
        ForEach-Object { Write-Host ("  " + $_.Line.Trim()) }
    exit 0
}

if (-not (Test-Path $orig)) { Copy-Item $yaml $orig -Force; Write-Host "backup written: $orig" }

$text = [System.IO.File]::ReadAllText($yaml)

# stock -> high-speed stability. Applied once each; running it twice is harmless
# because the patterns only match the stock values.
$edits = @(
    @{ from = 'wheelTurnMaxAddPerSecond: 94';    to = 'wheelTurnMaxAddPerSecond: 64';    why = 'steering builds up slower' },
    @{ from = 'turnUpdateMaxSpeedThreshold: 26'; to = 'turnUpdateMaxSpeedThreshold: 30'; why = 'reduction starts a little later (108 km/h)' },
    @{ from = 'turnUpdateMaxSpeedTurnMul: 0.33'; to = 'turnUpdateMaxSpeedTurnMul: 0.12'; why = 'above 30 m/s: 12% authority instead of 33%' }
)

$changed = 0
foreach ($e in $edits) {
    if ($text.Contains($e.from)) {
        $text = $text.Replace($e.from, $e.to)
        $changed++
        Write-Host ("  {0,-34} -> {1}" -f $e.from, $e.to.Split(':')[1].Trim())
    } elseif ($text.Contains($e.to)) {
        Write-Host ("  already applied: " + $e.to)
    } else {
        Write-Host ("  !! neither stock nor patched form found: " + $e.from)
    }
}

if ($changed -eq 0) { Write-Host ""; Write-Host "nothing written (already patched, or the YAML changed shape)"; exit 0 }

[System.IO.File]::WriteAllText($yaml, $text, $utf8)

Write-Host ""
Write-Host "STEERING PATCHED (local only - the repo copy is untouched)"
Select-String -Path $yaml -Pattern "wheelTurnMaxAddPerSecond|turnUpdateMaxSpeedTurnMul|turnUpdateMaxSpeedThreshold" |
    ForEach-Object { Write-Host ("  " + $_.Line.Trim()) }
Write-Host ""
Write-Host "Restart the game, then re-run the straight-line test."
Write-Host "Undo:  powershell -ExecutionPolicy Bypass -File .\tools\stability-tweak.ps1 -Revert"
