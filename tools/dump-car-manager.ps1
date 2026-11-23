# Collects everything needed to diagnose the Phoenix / Xaires's Car Manager paint
# problem into ONE text file, so nothing has to be scrolled or copy-pasted by hand.
#
# RUN IT *AFTER* YOU CLICK A COLOUR IN GAME, so the saved-choices JSON shows
# whether the click was stored at all.
#
#   powershell -ExecutionPolicy Bypass -File .\tools\dump-car-manager.ps1
#
# Writes .\car_manager_dump.txt next to the repo root and opens it in Notepad.

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
    try {
        $raw = @(Get-Content $j.FullName -Raw -ErrorAction Stop)
        $txt = ($raw | Out-String)
        if ($txt.Length -gt 6000) {
            $lines.Add($txt.Substring(0, 6000))
            $lines.Add("... (truncated - pasted only the first 6000 chars)")
        } else {
            $lines.Add($txt)
        }
    } catch {
        $lines.Add("(could not read: " + $_.Exception.Message + ")")
    }
}

Section "IS THE PATCH THERE? (line 225)"
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
Write-Host ""
Write-Host "written: $Out"
Write-Host "lines  : $($lines.Count)"
Write-Host ""
Write-Host "Next: paste the sections 'SAVED CHOICES', 'ARE THE TWO COLOURS IN THE PALETTE?'"
Write-Host "and 'PAINT APPLY CODE'. Those three decide the diagnosis."
Start-Process notepad.exe $Out
