# Launch only on the user's interactive desktop. Preparation does not run this.
$ErrorActionPreference = 'Stop'
$active = @(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if ($active.Count) { throw 'Close the old client and servers first; this control requires fresh processes.' }
if (Test-Path (Join-Path $PSScriptRoot 'launch-requested.txt')) { throw 'This one-run record has already been launched. Preserve and evaluate it before allocating another experiment.' }
foreach ($row in Import-Csv (Join-Path $PSScriptRoot 'identity.csv')) {
    if ((Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash -ne $row.SHA256) {
        throw "Prepared input changed: $($row.Path). Revalidate before launching."
    }
}
# Refuse inherited experimental switches. The frozen launcher supplies all its
# original assignments, including the disabled retry baseline; no new hypothesis.
$inherited = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($inherited.Count) { throw ('Use a fresh terminal without inherited SWTOR switches: ' + (($inherited.Name) -join ', ')) }
& (Join-Path $PSScriptRoot 'Preserve-Logs.ps1') -Label 'prelaunch'
if (!$?) { throw 'Log preservation failed; launch aborted.' }
Get-Date -Format o | Set-Content (Join-Path $PSScriptRoot 'launch-requested.txt')
$launcher = Join-Path $PSScriptRoot 'control.cmd'
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f $launcher)) -WindowStyle Hidden
Write-Output 'Control launched. Enter the Masters Retreat, walk through the visible exit once, then leave the client open for evidence collection. Do not use abilities or a second launcher.'
