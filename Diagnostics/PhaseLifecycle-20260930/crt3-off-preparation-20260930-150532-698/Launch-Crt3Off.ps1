$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$active = @(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if ($active.Count) { throw 'Close the old client and servers first; this ablation requires fresh processes.' }
$inherited = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($inherited.Count) { throw ('Use a fresh terminal without inherited SWTOR switches: ' + (($inherited.Name) -join ', ')) }
foreach ($row in Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'identity.csv')) {
    if ((Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash -ne $row.SHA256) { throw "Pinned input changed: $($row.Path)" }
}
& (Join-Path $root 'Diagnostics\DoorwayControl-20260930\Preserve-Logs.ps1') -Label 'crt3-off-prelaunch'
if (!$?) { throw 'Log preservation failed; launch aborted.' }
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'crt3-off-launch-requested.txt')
$launcher = Join-Path $root 'Run-SWTORClassic-PhaseLifecycle-Crt3Off.cmd'
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden
Write-Output "CRT3-off ablation launched. Enter the same character and Tython route. Confirm rendering and movement before approaching the Masters' Retreat doorway; do not use abilities."
