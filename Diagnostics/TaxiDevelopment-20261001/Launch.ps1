param([switch]$VerifyOnly, [switch]$CloneControl, [int]$TaxiRung = 0)
$ErrorActionPreference = 'Stop'
if ($TaxiRung -lt 0 -or $TaxiRung -gt 1) { throw "TaxiRung must be 0 or 1, got $TaxiRung" }
# The launcher must leave the calling shell exactly as it found it. It sets ~25
# SWTOR_* variables so the child .cmd and the server inherit them, and in verify mode
# those settings are never consumed by anything. Without the restore below, a second
# invocation in the same window trips the inherited-switch guard below and the user
# is forced to open a fresh terminal for every run.
# Snapshot first, restore in `finally` so every exit path -- including `exit 0` in
# verify mode and any throw -- puts the environment back.
$priorSwtor = @{}
foreach ($e in @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')) {
    $priorSwtor[$e.Name] = $e.Value
}
try {
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$active = @(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if ($active.Count) { throw 'Close the old client and servers first; fresh processes are required.' }
$inherited = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($inherited.Count) { throw ('Use a fresh terminal without inherited SWTOR switches: ' + ($inherited.Name -join ', ')) }
$identity = @(Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'identity.csv'))
if ($identity.Count -lt 10) { throw 'Taxi identity manifest is incomplete.' }
foreach ($row in $identity) {
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
$env:SWTOR_TYTHON_TAXI = '1'
# Control run: send a byte-for-byte copy of the captured medcenter droid record
# (only the identity differs) instead of the generated taxi, from the same position
# in the startup bundle. Isolates our synthesis/delivery from taxi content. Off by
# default; modifies no captured .aaw/.acrt fixture.
$env:SWTOR_TAXI_CLONE_CONTROL = if ($CloneControl) { '1' } else { '0' }
$env:SWTOR_TAXI_RUNG = "$TaxiRung"
$launcher = Join-Path $root 'Run-SWTORClassic-Trace-Tython.cmd'
if ($VerifyOnly) {
    if ($env:SWTOR_TYTHON_TAXI -ne '1') { throw 'Taxi experiment is not enabled.' }
    if ($env:SWTOR_WELLER_CONVERSATION -ne '1') { throw 'Weller conversation response is not enabled.' }
    if ($env:SWTOR_WELLER_END -ne '1') { throw 'Weller conversation cleanup is not enabled.' }
    & $env:ComSpec /d /c ('""{0}" --verify-config 0"' -f $launcher)
    if ($LASTEXITCODE -ne 0) { throw 'Effective configuration verification failed.' }
    if ($env:SWTOR_PHASE_EXIT_CLEAR_FIELD -ne '1' -or $env:SWTOR_TRACE_PHASE_UPDATE -ne '1' -or $env:SWTOR_MOVEMENT_TETHER_REFRESH -ne '1' -or $env:SWTOR_PHASE_REENTRY -ne '1' -or $env:SWTOR_RETREAT_GATEWAY_TIMING -ne '1') {
        throw 'Required phase baseline or tether-only configuration is wrong.'
    }
    $mode = if ($env:SWTOR_TAXI_CLONE_CONTROL -eq '1') { "MERGED TAXI rung $env:SWTOR_TAXI_RUNG (real taxi payload appended to awareness set 1)" } else { 'taxi NPC/map' }
    Write-Output "VERIFIED: mode=$mode; Weller response=1; cleanup=1; movement tether refresh=1; phase reentry=1; authored-gateway timing=1; all runtime inputs pinned; CRT3=0; retry disabled. No processes launched."
    exit 0
}
& (Join-Path $PSScriptRoot 'Preserve-CurrentLogs.ps1')
if (!$?) { throw 'Log preservation failed; launch aborted.' }
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-requested.txt')
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'launcher-console.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'launcher-errors.log')
if ($CloneControl) { Write-Output "MERGED TAXI rung $TaxiRung launched. This is the REAL taxi record, not a stand-in. Rung 0 = as shipped (expect six script errors). Rung 1 = only _characterSpecification reverted to the captured donor value (8 bytes of 677). If the droid and its overhead taxi icon appear, the spec was the blocker. Close afterward for log review." }
else { Write-Output 'Taxi test launched. Leave the retreat and right-click the new taxi droid near the exit. If a map opens, select Gnarls once. Flight is pending; close afterward for log review.' }
}
finally {
    # Restore the shell exactly as found. Remove anything the launcher set that was
    # not there before, then put back any prior value. `exit 0` in verify mode and
    # every `throw` above still pass through here.
    foreach ($e in @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')) {
        if (-not $priorSwtor.ContainsKey($e.Name)) { Remove-Item -LiteralPath ('Env:' + $e.Name) -ErrorAction SilentlyContinue }
    }
    foreach ($name in $priorSwtor.Keys) {
        Set-Item -LiteralPath ('Env:' + $name) -Value $priorSwtor[$name]
    }
}
