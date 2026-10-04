$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$active = @(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if ($active.Count) { throw 'Close the old client and servers first; this lifecycle run requires fresh processes.' }
$inherited = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($inherited.Count) { throw ('Use a fresh terminal without inherited SWTOR switches: ' + (($inherited.Name) -join ', ')) }

$identityPath = Join-Path $PSScriptRoot 'identity.csv'
foreach ($row in Import-Csv -LiteralPath $identityPath) {
    if (!(Test-Path -LiteralPath $row.Path)) { throw "Pinned input is missing: $($row.Path)" }
    $actual = (Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash
    if ($actual -ne $row.SHA256) { throw "Pinned input changed: $($row.Path)" }
}

& (Join-Path $root 'Diagnostics\DoorwayControl-20260930\Preserve-Logs.ps1') -Label 'phase-lifecycle-prelaunch'
if (!$?) { throw 'Log preservation failed; launch aborted.' }

$capture = Join-Path $PSScriptRoot ('live-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$watcher = Join-Path $PSScriptRoot 'Watch-PhaseLifecycle.ps1'
$hookLog = Join-Path $root 'nexusclient\nexusclient\nexus_hook.log'
$watcherArgs = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -OutputDirectory "{1}" -HookLog "{2}"' -f $watcher,$capture,$hookLog
Start-Process -FilePath "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList $watcherArgs `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'watcher-console.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'watcher-errors.log') -WindowStyle Hidden

Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-requested.txt')
$launcher = Join-Path $root 'Run-SWTORClassic-Trace-Tython.cmd'
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden
Write-Output "Lifecycle run launched. Wait for $PSScriptRoot\watcher-console.log to say READY. Before authorizing doorway movement, independently confirm genuine non-overlapping private-memory method addresses, CRT3 enabled, the corrected server hash, CRT18 suppression and retry disabled. READY alone does not authorize crossing. Do not use abilities."
