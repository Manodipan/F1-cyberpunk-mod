# Collects everything needed to diagnose the Phoenix / Xaires's Car Manager paint
# problem into ONE text file, so nothing has to be scrolled or copy-pasted by hand.
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
$log    = Join-Path $Game "r6\logs\cyber_engine_tweaks.log"

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
    $lines.Add((Get-Content $j.FullName -Raw))
}

Section "IS THE PATCH THERE? (line 225)"
$lines.Add((Select-String -Path $init -Pattern "phoenix_aston_valkyrie" |
            ForEach-Object { "$($_.LineNumber): $($_.Line)" }))
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

Section "CET LOG (last 30 xaires / phoenix / error lines)"
if (Test-Path $log) {
    $hits = Select-String -Path $log -Pattern "xaires|phoenix|rror" | Select-Object -Last 30
    if (-not $hits) { $lines.Add("(no matching lines)") }
    foreach ($h in $hits) { $lines.Add($h.Line) }
} else {
    $lines.Add("log not found: $log")
}

Section "END"

$lines | Out-File -FilePath $Out -Encoding utf8
Write-Host ""
Write-Host "written: $Out"
Write-Host "lines  : $($lines.Count)"
Write-Host ""
Write-Host "Next: open it, or paste the two sections 'SAVED CHOICES' and"
Write-Host "'init.lua 420-463' - those decide the diagnosis."
Start-Process notepad.exe $Out
