<#
.SYNOPSIS
    Gate: every generated taxi fixture must walk to exactly its inner_size.

.DESCRIPTION
    The value-walk grammar was resolved offline against the captured vendor
    (see Diagnostics/Experiments/2026-10-02-05-taxi-wire-surface-and-precreate-spec.md
    #RESOLVED). Until that grammar existed no statement about any value in a
    character record was admissible and no fixture edit was safe. This gate is
    what makes that rule enforceable: it re-walks TaxiNpc.bin, TaxiRecord1.bin
    and TaxiClone.bin with the resolved grammar and fails if any record does not
    consume precisely inner_size.

    Read-only. It never rewrites a fixture and never launches the client.

.EXAMPLE
    pwsh -File Diagnostics/Test-TaxiValueWalk.ps1
    pwsh -File Diagnostics/Test-TaxiValueWalk.ps1 -Python C:\path\to\python.exe
#>
[CmdletBinding()]
param(
    [string] $Python = '',
    [string] $Report = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root 'Diagnostics\TaxiDevelopment-20261001\Verify-TaxiFixtures.py'
$expected = Join-Path $root 'Diagnostics\TaxiDevelopment-20261001\taxi-fixture-verification.txt'

function Resolve-Python {
    param([string] $Preferred)
    if ($Preferred) { return $Preferred }
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    $fallback = Join-Path $env:USERPROFILE `
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path $fallback) { return $fallback }
    throw 'No python interpreter found. Pass -Python <path>.'
}

$exe = Resolve-Python -Preferred $Python
Write-Host "taxi value-walk gate"
Write-Host "  python : $exe"
Write-Host "  script : $script"

$output = & $exe $script 2>&1
$exit = $LASTEXITCODE
$output | ForEach-Object { Write-Host $_ }

if ($exit -ne 0) {
    Write-Host "FAIL: verification script exited $exit"
    exit 1
}
if (-not (Test-Path $expected)) {
    Write-Host "FAIL: $expected was not written"
    exit 1
}

$verdict = Get-Content $expected | Select-String -SimpleMatch 'all records reconcile exactly:'
if (-not $verdict) {
    Write-Host 'FAIL: report does not carry a reconciliation verdict'
    exit 1
}
if ($verdict -notmatch 'all records reconcile exactly: True') {
    Write-Host 'FAIL: at least one fixture record does not walk to inner_size'
    exit 1
}

if ($Report) {
    Copy-Item $expected $Report -Force
    Write-Host "  report : $Report"
}
Write-Host 'PASS: every taxi fixture record walks to exactly inner_size'
exit 0