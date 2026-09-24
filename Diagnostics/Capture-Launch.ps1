param([switch]$AllowPartialAssets)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$client = Join-Path $repo 'nexusclient\nexusclient'
$settings = Get-Content -LiteralPath (Join-Path $client 'client_defaults.ini') -Raw
if ($settings -match 'BaseResourceFileName=.*AssetsConverted') {
    $report = Get-Content -LiteralPath (Join-Path $repo 'AssetsConverted\conversion-report.json') -Raw | ConvertFrom-Json
    if ($report.archives.Count -ne 101 -and -not $AllowPartialAssets) { throw 'Asset preparation is not complete yet. Use Test-ConvertedAssets.bat for a partial startup test.' }
    if ($AllowPartialAssets) { Write-Host "Partial asset test: $($report.archives.Count) of 101 archives are ready. Missing archives may cause a later failure." }
    foreach ($archive in $report.archives) {
        $asset = Get-Item -LiteralPath (Join-Path $repo ('AssetsConverted\' + $archive.archive))
        if ($asset.Length -ne $archive.output_bytes) { throw "Asset size mismatch: $($archive.archive)" }
    }
}
$capture = Join-Path $PSScriptRoot ('Captures\' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $capture -Force | Out-Null
$logs = Join-Path $client 'swtor\logs'
if (Test-Path $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $capture 'logs-before') -Recurse }
$started = Get-Date
try {
    $line = (Get-Content -LiteralPath (Join-Path $client 'go1.bat') -Raw).Trim()
    if ($line -notmatch '^swtor-emu\.exe\s+([^\r\n]+)$') { throw 'Unexpected go1.bat format; launch cancelled.' }
    $launchArguments = $Matches[1]
    Write-Host 'Starting client. Close it normally if it stays open.'
    $process = Start-Process -FilePath (Join-Path $client 'swtor-emu.exe') -ArgumentList $launchArguments -WorkingDirectory $client -RedirectStandardOutput (Join-Path $capture 'stdout.txt') -RedirectStandardError (Join-Path $capture 'stderr.txt') -PassThru
    $process.WaitForExit()
    "Started: $($started.ToString('o'))`r`nEnded: $((Get-Date).ToString('o'))`r`nParent process ID: $($process.Id)`r`nParent exit code: $($process.ExitCode)" | Set-Content (Join-Path $capture 'result.txt')
} finally {
    if (Test-Path $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $capture 'logs-after') -Recurse }
    try {
        Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$started} -ErrorAction Stop |
            Where-Object { $_.ProviderName -in @('Application Error','Windows Error Reporting','Application Hang') -and $_.Message -match 'swtor|MemoryMan|Nexus|RemoteRenderer' } |
            Format-List TimeCreated,ProviderName,Id,Message | Out-File (Join-Path $capture 'windows-errors.txt')
    } catch { $_.Exception.Message | Set-Content (Join-Path $capture 'windows-event-query.txt') }
    Write-Host "Capture saved: $capture"
}
