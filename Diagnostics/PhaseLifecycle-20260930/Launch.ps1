param([switch]$VerifyOnly,[switch]$Crt3Off)
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

# Both comparison arms share this configuration; only CRT3 differs.
# No process memory scanner is started in either log-only run.
$env:SWTOR_ENABLE_UNVERIFIED_CRT3 = if ($Crt3Off) { '0' } else { '1' }
$env:SWTOR_PHASE_INSTANCE_RETRY = ''
$env:SWTOR_PHASE_LIFECYCLE_LOG_ONLY = '1'
$launcher = Join-Path $root 'Run-SWTORClassic-Trace-Tython.cmd'
if ($VerifyOnly) {
    & $env:ComSpec /d /c ('""{0}" --verify-config {1}"' -f $launcher,$env:SWTOR_ENABLE_UNVERIFIED_CRT3)
    if ($LASTEXITCODE -ne 0) { throw 'Effective configuration verification failed.' }
    Write-Output 'VERIFIED: pinned inputs agree; configuration checked without launching processes.'
    exit 0
}

$label = if ($Crt3Off) { 'crt3-off-prelaunch' } else { 'phase-lifecycle-prelaunch' }
& (Join-Path $root 'Diagnostics\DoorwayControl-20260930\Preserve-Logs.ps1') -Label $label
if (!$?) { throw 'Log preservation failed; launch aborted.' }

$stamp = if ($Crt3Off) { 'crt3-off-launch-requested.txt' } else { 'launch-requested.txt' }
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $PSScriptRoot $stamp)
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'launcher-console.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'launcher-errors.log')
Write-Output ("CRT3={0} log-only run launched. No full-memory observer is running. Wait for named hook installation and server confirmation of the CRT3 setting before a doorway attempt. Use no abilities." -f $env:SWTOR_ENABLE_UNVERIFIED_CRT3)
