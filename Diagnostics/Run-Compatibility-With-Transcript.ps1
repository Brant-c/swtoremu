param(
    [Parameter(Mandatory = $true)]
    [string]$ClientDirectory,
    [int]$TimeoutSeconds = 600
)

$transcript = Join-Path $PSScriptRoot 'last-compatibility-run.log'
& (Join-Path $PSScriptRoot 'CompatibilityLauncher.exe') $ClientDirectory $TimeoutSeconds 2>&1 |
    Tee-Object -FilePath $transcript
exit $LASTEXITCODE
