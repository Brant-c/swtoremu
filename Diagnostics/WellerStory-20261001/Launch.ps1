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
$env:SWTOR_TRACE_MOVEMENT_COLLISION = '0'
$env:SWTOR_MOVEMENT_TETHER_REFRESH = '1'
$env:SWTOR_PHASE_REENTRY = '1'
$env:SWTOR_RETREAT_GATEWAY_TIMING = '1'
$env:SWTOR_WELLER_CONVERSATION = '1'
$env:SWTOR_WELLER_END = '1'
$launcher = Join-Path $root 'Run-SWTORClassic-Trace-Tython.cmd'
if ($VerifyOnly) {
    if ($env:SWTOR_WELLER_CONVERSATION -ne '1') { throw 'Weller conversation response is not enabled.' }
    if ($env:SWTOR_WELLER_END -ne '1') { throw 'Weller conversation cleanup is not enabled.' }
    & $env:ComSpec /d /c ('""{0}" --verify-config 0"' -f $launcher)
    if ($LASTEXITCODE -ne 0) { throw 'Effective configuration verification failed.' }
    if ($env:SWTOR_PHASE_EXIT_CLEAR_FIELD -ne '1' -or $env:SWTOR_TRACE_PHASE_UPDATE -ne '1' -or $env:SWTOR_MOVEMENT_TETHER_REFRESH -ne '1' -or $env:SWTOR_PHASE_REENTRY -ne '1' -or $env:SWTOR_RETREAT_GATEWAY_TIMING -ne '1') {
        throw 'Required phase baseline or tether-only configuration is wrong.'
    }
    Write-Output 'VERIFIED: Weller conversation response=1; cleanup=1; movement tether refresh=1; phase reentry=1; authored-gateway timing=1; all runtime inputs pinned; CRT3=0; retry disabled. No processes launched.'
    exit 0
}
& (Join-Path $PSScriptRoot 'Preserve-CurrentLogs.ps1')
if (!$?) { throw 'Log preservation failed; launch aborted.' }
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-requested.txt')
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'launcher-console.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'launcher-errors.log')
Write-Output 'Weller conversation launched. Finish the conversation, verify normal camera/movement returns, then right-click again and press Escape to check cancellation. Quest progression remains pending.'
