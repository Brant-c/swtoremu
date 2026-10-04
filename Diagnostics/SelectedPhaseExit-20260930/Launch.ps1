param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$active = @(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if ($active.Count) { throw 'Close the old client and servers first; fresh processes are required.' }
$inherited = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($inherited.Count) { throw ('Use a fresh terminal without inherited SWTOR switches: ' + ($inherited.Name -join ', ')) }
foreach ($row in Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'identity.csv')) {
    if (!(Test-Path -LiteralPath $row.Path)) { throw "Pinned input is missing: $($row.Path)" }
    if ((Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash -ne $row.SHA256) {
        throw "Pinned input changed: $($row.Path)"
    }
}
$env:SWTOR_PHASE_EXIT_CLEAR_FIELD = '1'
$env:SWTOR_TRACE_PHASE_UPDATE = '1'
$env:SWTOR_ENABLE_UNVERIFIED_CRT3 = '0'
$env:SWTOR_PHASE_INSTANCE_RETRY = ''
$env:SWTOR_PHASE_LIFECYCLE_LOG_ONLY = '1'
$env:SWTOR_TRACE_ROOM_SELECTION = '1'
$env:SWTOR_TRACE_TRIGGER_COLLISION = '1'
$launcher = Join-Path $root 'Run-SWTORClassic-Trace-Tython.cmd'
if ($VerifyOnly) {
    & $env:ComSpec /d /c ('""{0}" --verify-config 0"' -f $launcher)
    if ($LASTEXITCODE -ne 0) { throw 'Effective configuration verification failed.' }
    if ($env:SWTOR_PHASE_EXIT_CLEAR_FIELD -ne '1' -or $env:SWTOR_TRACE_PHASE_UPDATE -ne '1') {
        throw 'Selected-player clear or callback observer is disabled.'
    }
    Write-Output 'VERIFIED: selected-player phase clear=1; bounded phase update observer=1; corrected server and new hook pinned; CRT3=0; lifecycle log-only=1; retry disabled. No processes launched.'
    exit 0
}
& (Join-Path $PSScriptRoot 'Preserve-CurrentLogs.ps1')
if (!$?) { throw 'Log preservation failed; launch aborted.' }
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-requested.txt')
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'launcher-console.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'launcher-errors.log')
Write-Output 'Selected-player phase exit launched. Load Tython and stand still; report loaded so callback installation can be checked before approaching the doorway.'
