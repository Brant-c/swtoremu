param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
# Only CRT3 differs; preparation, logging and runtime launch code are shared.
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'live-20260930-145102-logonly\RESULTS.md'))) {
    throw 'The preserved CRT3-on comparator is missing; ablation aborted.'
}
& (Join-Path $PSScriptRoot 'Launch.ps1') -Crt3Off -VerifyOnly:$VerifyOnly
