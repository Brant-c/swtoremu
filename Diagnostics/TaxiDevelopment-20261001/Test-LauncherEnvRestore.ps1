# Proves the launcher no longer pollutes the calling shell: it must leave zero
# SWTOR_* variables behind, so a second invocation in the same window is allowed.
# Before this, verify mode left ~25 behind and every subsequent run in that window
# was rejected by the inherited-switch guard, forcing a fresh terminal each time.
$ErrorActionPreference = 'Stop'
$before = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*').Count
Write-Host "SWTOR_* before : $before"
& (Join-Path $PSScriptRoot 'Launch.ps1') -VerifyOnly -CloneControl -TaxiRung 1 |
    Select-Object -Last 1
$after = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*').Count
Write-Host "SWTOR_* after  : $after"
if ($after -ne $before) {
    throw "Launcher leaked environment: $before before, $after after."
}
if ($after -ne 0) {
    throw 'Test session already had SWTOR_* set; rerun from a clean shell.'
}
Write-Host 'PASS: shell is clean; a second run in this window will be accepted.'

# And prove the guard now permits a second consecutive invocation.
& (Join-Path $PSScriptRoot 'Launch.ps1') -VerifyOnly -CloneControl -TaxiRung 1 |
    Select-Object -Last 1
Write-Host 'PASS: second invocation in the same window was accepted.'