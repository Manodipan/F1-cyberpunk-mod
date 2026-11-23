# v3 — repair / re-apply the one-line Car Manager patch.
#
# TWO things this fixes.
#
# 1. v2 was written by a regex that replaced only `records = rec('xaires_aston_valkyrie')`
#    and left the line's own trailing comma behind, so init.lua ended up with
#      ... end)(),,
#    which is a Lua SYNTAX ERROR: the whole file fails to load, so the manager does not
#    run at all. That was my bug; this script rewrites the WHOLE line, so the comma
#    cannot double up again.
#
# 2. v2 also assumed rec() returns the same shape of id we could hand-write. It does not
#    have to: carOf() hashes whatever strings are in the list and compares them with the
#    vehicle's GetRecordID(). So the line now carries BOTH forms — whatever rec() gives,
#    plus the literal 'Vehicle.phoenix_aston_valkyrie'. A key nobody matches costs
#    nothing, and one of them is guaranteed to be the real record id.
#
#   powershell -ExecutionPolicy Bypass -File .\compat\xaires_car_manager\repatch.ps1
#
# Safe to run any number of times. Afterwards: CET -> Reload all mods.

param(
    [string]$Game   = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$ModDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $ModDir) {
    $ModDir = Join-Path $Game "bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager"
}

$init = Join-Path $ModDir "init.lua"
$orig = Join-Path $ModDir "init.lua.orig"
$prev = Join-Path $ModDir "init.lua.prev"

$canonical = "records = (function() local t = rec('xaires_aston_valkyrie') local p = rec('phoenix_aston_valkyrie') if type(p) == 'table' then for i = 1, #p do t[#t + 1] = p[i] end end t[#t + 1] = 'Vehicle.phoenix_aston_valkyrie' return t end)(),"

# (?m) so the same patterns work on one line and on the whole file (used for the fallback test)
$reStock   = [regex]'(?m)^\s*records\s*=\s*rec\(\s*''xaires_aston_valkyrie''\s*\),?\s*$'
$rePatched = [regex]'(?m)^\s*records\s*=.*phoenix_aston_valkyrie.*$'

Write-Host ""
Write-Host "folder : $ModDir"

if (-not (Test-Path $ModDir)) { Write-Host "!! that folder does not exist - check the -Game path"; exit 1 }
if (-not (Test-Path $init))   { Write-Host "!! init.lua not found in that folder"; exit 1 }

# Prefer the live file (keeps anything else you changed); .orig is only a fallback source.
$source = $init
$text   = [IO.File]::ReadAllText($source)

if (-not ($reStock.IsMatch($text) -or $rePatched.IsMatch($text))) {
    if (Test-Path $orig) {
        $source = $orig
        $text   = [IO.File]::ReadAllText($source)
        Write-Host "no patch and no stock line in init.lua - rebuilding from init.lua.orig instead"
    }
}

$eol = "`n"
if ($text.Contains("`r`n")) { $eol = "`r`n" }

$lines = @($text -split "\r?\n")
$hits  = 0

for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($reStock.IsMatch($ln) -or $rePatched.IsMatch($ln)) {
        $indent = ""
        if ($ln -match '^(\s*)') { $indent = $matches[1] }
        $lines[$i] = $indent + $canonical
        $hits++
        Write-Host ("rewrote line {0}" -f ($i + 1))
    }
}

if ($hits -eq 0) {
    Write-Host "!! could not find the  records = ...  line for the Aston at all."
    Write-Host "   The manager has probably been updated and the table changed shape."
    exit 1
}
if ($hits -gt 1) {
    Write-Host "!! $hits lines matched - that is unexpected. Nothing was written."
    exit 1
}

$out = $lines -join $eol

# Guard against the exact mistake v2 made.
if ($out -match '\)\),') {
    Write-Host "!! refusing to write: the result would contain a double comma (Lua syntax error)"
    exit 1
}

Copy-Item $init $prev -Force
Write-Host "previous init.lua saved as init.lua.prev"
[IO.File]::WriteAllText($init, $out, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ""
Write-Host "PATCHED v3"
Select-String -Path $init -Pattern "phoenix_aston_valkyrie" |
    ForEach-Object { Write-Host ("  {0}: {1}" -f $_.LineNumber, $_.Line) }

$doubles = @(Select-String -Path $init -Pattern "\)\),")
Write-Host ("double-comma check : " + $(if ($doubles.Count -eq 0) { "clean" } else { "STILL BROKEN" }))

Write-Host ""
Write-Host "rec() - this is what the ids look like before carOf() hashes them:"
$recDef = Select-String -Path $init -Pattern "local function rec" -Context 0, 12
if ($recDef) { $recDef.Context.PostContext | ForEach-Object { Write-Host ("  " + $_) } }

Write-Host ""
Write-Host "Now: CET -> Reload all mods. If the manager does not appear in the CET list at all,"
Write-Host "the file still has an error - open the CET log and paste the last few lines."
Write-Host "Then spawn the Phoenix, pick Rosso Fiorano, and look at the car."
