# v2 of the one-line Car Manager patch.
#
# WHY: v1 appended a hand-built string ('phoenix_aston_valkyrie') to the record list.
# On the test machine that made the manager paint the *stock* Aston and leave the
# Phoenix alone, which is what you see if the ids in that list are not plain record
# names (if rec() prefixes 'Vehicle.' or resolves through TweakDB, a hand-written
# string never matches GetRecordID()). v2 asks rec() for our id too, so whatever
# transformation it applies is applied to both cars.
#
# Rebuilds init.lua from the pristine init.lua.orig (the copy made before v1), so it
# works whether or not v1 is currently applied, and is safe to run twice.
#
#   powershell -ExecutionPolicy Bypass -File .\compat\xaires_car_manager\repatch.ps1
#
# Afterwards: in game, CET -> Reload all mods, spawn the Phoenix, click Rosso Fiorano.

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

Write-Host ""
Write-Host "folder : $ModDir"

if (-not (Test-Path $ModDir)) { Write-Host "!! that folder does not exist - check the -Game path"; exit 1 }
if (-not (Test-Path $init))   { Write-Host "!! init.lua not found"; exit 1 }
if (-not (Test-Path $orig)) {
    Write-Host "!! init.lua.orig is missing, so there is no pristine copy to rebuild from."
    Write-Host "   Re-download the Car Manager, copy init.lua to init.lua.orig, then re-run this."
    exit 1
}

$utf8  = New-Object System.Text.UTF8Encoding($false)
$text  = [IO.File]::ReadAllText($orig)

$newLine = "records = (function() local t = rec('xaires_aston_valkyrie') local p = rec('phoenix_aston_valkyrie') if type(p) == 'table' then for i = 1, #p do t[#t + 1] = p[i] end end return t end)(),"

$re = [regex]"records\s*=\s*rec\('xaires_aston_valkyrie'\)"
$m  = $re.Matches($text)
Write-Host "matches for the stock line in init.lua.orig : $($m.Count)"

if ($m.Count -lt 1) {
    Write-Host "!! could not find  records = rec('xaires_aston_valkyrie')  in init.lua.orig"
    Write-Host "   Either the manager changed, or .orig is not the pristine file."
    exit 1
}

Copy-Item $init $prev -Force
Write-Host "current init.lua saved as init.lua.prev"

$out = $re.Replace($text, $newLine, 1)
[IO.File]::WriteAllText($init, $out, $utf8)

Write-Host ""
Write-Host "PATCHED v2"
Select-String -Path $init -Pattern "phoenix_aston_valkyrie" |
    ForEach-Object { Write-Host ("  {0}: {1}" -f $_.LineNumber, $_.Line) }

Write-Host ""
Write-Host "how rec() builds the ids (this is what decides whether it works):"
Select-String -Path $init -Pattern "function rec" -Context 0, 10 |
    ForEach-Object { $_.Context.PostContext | Where-Object { $_ -ne $null } | ForEach-Object { Write-Host ("  " + $_) } }

Write-Host ""
Write-Host "Now in game: CET -> Reload all mods, spawn the Phoenix, pick Rosso Fiorano."
Write-Host "Then run tools\dump-car-manager.ps1 and paste paint_dump.txt."
