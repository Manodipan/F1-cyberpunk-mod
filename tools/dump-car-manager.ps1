# Collects everything needed to diagnose the Phoenix / Xaires's Car Manager paint
# problem into ONE text file, so nothing has to be scrolled or copy-pasted by hand.
#
# RUN IT *AFTER* YOU CLICK A COLOUR IN GAME, so the saved-choices JSON shows
# whether the click was stored at all.
#
#   powershell -ExecutionPolicy Bypass -File .\tools\dump-car-manager.ps1
#
# Writes two files next to the repo root:
#   car_manager_dump.txt  - everything
#   paint_dump.txt        - only the paint diagnosis, opened in Notepad (this is the one
#                           to paste into the chat: select all, copy, paste)

param(
    [string]$Game = "G:\Cyberpunk2077\Cyberpunk 2077 Phantom Liberty",
    [string]$Out  = ""
)

$ErrorActionPreference = "Continue"

$modDir = Join-Path $Game "bin\x64\plugins\cyber_engine_tweaks\mods\xaires_car_manager"
$init   = Join-Path $modDir "init.lua"
$logCandidates = @(
    (Join-Path $Game "bin\x64\plugins\cyber_engine_tweaks\cyber_engine_tweaks.log"),
    (Join-Path $Game "r6\logs\cyber_engine_tweaks.log"),
    (Join-Path $Game "r6\logs\redscript_rCURRENT.log")
)

if (-not $Out) {
    $Out = Join-Path (Split-Path -Parent $PSScriptRoot) "car_manager_dump.txt"
}

$lines = New-Object System.Collections.Generic.List[string]

function Section($title) {
    $lines.Add("")
    $lines.Add("================ $title ================")
}

Section "WHERE"
$lines.Add("game    : $Game")
$lines.Add("mod dir : $modDir")
$lines.Add("exists  : " + (Test-Path $modDir))
$lines.Add("date    : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))

if (-not (Test-Path $modDir)) {
    $lines.Add("!! mod folder not found - check the -Game path")
    $lines | Out-File -FilePath $Out -Encoding utf8
    Write-Host "written: $Out"
    exit 1
}

Section "FILES IN THE MANAGER FOLDER"
$lines.Add((Get-ChildItem $modDir | Select-Object Name, Length, LastWriteTime |
            Format-Table -AutoSize | Out-String -Width 200))

Section "SAVED CHOICES (every .json in that folder)"
$json = Get-ChildItem $modDir -Filter *.json -ErrorAction SilentlyContinue
if (-not $json) { $lines.Add("(no .json files)") }
foreach ($j in $json) {
    $lines.Add("--- $($j.Name) ($($j.Length) bytes) ---")
    $cap = 6000
    if (-not ($j.Name -eq "ayarlar.json" -or $j.Name -eq "ses.json")) { $cap = 600 }
    try {
        $txt = (Get-Content $j.FullName -Raw -ErrorAction Stop | Out-String)
        if ($txt.Length -gt $cap) {
            $lines.Add($txt.Substring(0, $cap))
            $lines.Add("... (only the first $cap chars - the full dump has the same cap)")
        } else {
            $lines.Add($txt)
        }
    } catch {
        $lines.Add("(could not read: " + $_.Exception.Message + ")")
    }
}

$paintStart = $lines.Count

Section "IS THE PATCH THERE?"
$patchHits = Select-String -Path $init -Pattern "phoenix_aston_valkyrie"
if (-not $patchHits) { $lines.Add("(no hit - the patch is NOT in init.lua)") }
foreach ($h in $patchHits) { $lines.Add("$($h.LineNumber): $($h.Line)") }
$lines.Add("backup present: " + (Test-Path "$init.orig"))

Section "init.lua 420-463  (chosen / carOf / currentVehicle)"
if (Test-Path $init) {
    $content = Get-Content $init
    $lines.Add("# total lines: $($content.Count)")
    for ($i = 419; $i -le 462 -and $i -lt $content.Count; $i++) {
        $lines.Add(("{0,4}: {1}" -f ($i + 1), $content[$i]))
    }
} else {
    $lines.Add("init.lua not found")
}

Section "EVERY MENTION OF THE ASTON / RECORD IDS IN init.lua"
if (Test-Path $init) {
    $hits = Select-String -Path $init -Pattern "aston|xaires|phoenix|GetRecordID|recordID|records"
    foreach ($h in $hits) {
        $t = $h.Line.Trim()
        if ($t.Length -gt 140) { $t = $t.Substring(0, 140) + " ..." }
        $lines.Add(("{0,4}: {1}" -f $h.LineNumber, $t))
    }
    $lines.Add("(total hits: " + @($hits).Count + ")")
}

Section "FUNCTION INDEX (line: definition)"
if (Test-Path $init) {
    $fns = Select-String -Path $init -Pattern "^\s*(local\s+)?function\s+[\w\.:]+"
    foreach ($f in $fns) {
        $t = $f.Line.Trim()
        if ($t.Length -gt 90) { $t = $t.Substring(0, 90) + " ..." }
        $lines.Add(("{0,4}: {1}" -f $f.LineNumber, $t))
    }
    $lines.Add("(total functions: " + @($fns).Count + ")")
}

Section "init.lua 20-45  (the rec() helper itself)"
if (Test-Path $init) {
    $c3 = Get-Content $init
    for ($i = 19; $i -le 44 -and $i -lt $c3.Count; $i++) {
        $lines.Add(("{0,4}: {1}" -f ($i + 1), $c3[$i]))
    }
}

Section "init.lua 160-260  (helpers above the CARS table)"
if (Test-Path $init) {
    $c2 = Get-Content $init
    for ($i = 159; $i -le 259 -and $i -lt $c2.Count; $i++) {
        $lines.Add(("{0,4}: {1}" -f ($i + 1), $c2[$i]))
    }
}

Section "PAINT APPLY CODE  (init.lua 455-640)"
if (Test-Path $init) {
    $content = Get-Content $init
    for ($i = 454; $i -le 639 -and $i -lt $content.Count; $i++) {
        $lines.Add(("{0,4}: {1}" -f ($i + 1), $content[$i]))
    }
}

Section "PAINT KEYWORD INDEX (line + trimmed line)"
if (Test-Path $init) {
    $pat = "SetAppearance|appearance|Component|kaplama|apply|Apply|desired|chosen|slots|comps|onek|palet"
    Select-String -Path $init -Pattern $pat | ForEach-Object {
        $t = $_.Line.Trim()
        if ($t.Length -gt 130) { $t = $t.Substring(0, 130) + " ..." }
        $lines.Add(("{0,4}: {1}" -f $_.LineNumber, $t))
    }
}

Section "PALETTE FILES (what the lists actually contain)"
foreach ($name in @("marka_renkleri.json", "sdh0_palet.json", "kaplamalar.json", "countach_renkler.json")) {
    $p = Join-Path $modDir $name
    if (-not (Test-Path $p)) { $lines.Add("--- $name : (missing)"); continue }
    $lines.Add("--- $name ($((Get-Item $p).Length) bytes)")
    try {
        $o = Get-Content $p -Raw | ConvertFrom-Json
        $keys = @($o.PSObject.Properties.Name)
        $lines.Add("keys(" + $keys.Count + "): " + (($keys | Select-Object -First 40) -join ", "))
        if ($name -eq "kaplamalar.json") {
            $amv = $o.PSObject.Properties | Where-Object { $_.Name -eq "amv" } | Select-Object -First 1
            if ($amv) {
                $lines.Add("--- kaplamalar.json .amv ---")
                $j = @(($amv.Value | ConvertTo-Json -Depth 6) -split "`n")
                $n = 0
                foreach ($ln in $j) {
                    if ($n -ge 60) { break }
                    $lines.Add($ln)
                    $n++
                }
                if ($j.Count -gt 60) { $lines.Add("... (" + ($j.Count - 60) + " more lines)") }
            } else {
                $lines.Add("(no .amv key in kaplamalar.json)")
            }
        }
    } catch {
        $lines.Add("(not valid JSON: " + $_.Exception.Message + ")")
    }
}

Section "ARE THE TWO COLOURS IN THE PALETTE? (rosso / bronz / bronze)"
$found = $false
foreach ($j in (Get-ChildItem $modDir -Filter *.json -ErrorAction SilentlyContinue)) {
    $hits = Select-String -Path $j.FullName -Pattern "rosso|bronz|bronze" -ErrorAction SilentlyContinue
    if ($hits) {
        $found = $true
        foreach ($h in ($hits | Select-Object -First 12)) {
            $t = $h.Line.Trim()
            if ($t.Length -gt 150) { $t = $t.Substring(0, 150) + " ..." }
            $lines.Add("$($j.Name):$($h.LineNumber): $t")
        }
    }
}
if (-not $found) { $lines.Add("(no line mentions rosso / bronz / bronze)") }

Section "LOGS (last 30 xaires / phoenix / error lines per file)"
$anyLog = $false
foreach ($log in $logCandidates) {
    $lines.Add("--- $log")
    if (Test-Path $log) {
        $anyLog = $true
        $hits = Select-String -Path $log -Pattern "xaires|phoenix|rror" | Select-Object -Last 30
        if (-not $hits) { $lines.Add("(no matching lines)") }
        foreach ($h in $hits) { $lines.Add($h.Line) }
    } else {
        $lines.Add("(missing)")
    }
}

Section "END"

$lines | Out-File -FilePath $Out -Encoding utf8

$small = Join-Path (Split-Path -Parent $Out) "paint_dump.txt"
$slice = $lines.GetRange($paintStart, $lines.Count - $paintStart)
$slice | Out-File -FilePath $small -Encoding utf8

Write-Host ""
Write-Host "written: $Out"
Write-Host "lines  : $($lines.Count)"
Write-Host "paste this one: $small  ($($slice.Count) lines)"
Write-Host ""
Write-Host "Next: paste the sections 'SAVED CHOICES', 'ARE THE TWO COLOURS IN THE PALETTE?'"
Write-Host "and 'PAINT APPLY CODE'. Those three decide the diagnosis."
Start-Process notepad.exe $small
