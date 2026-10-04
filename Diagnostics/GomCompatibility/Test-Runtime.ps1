$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$client = Join-Path $repo 'nexusclient\nexusclient'
$config = Join-Path $client 'client_defaults.ini'
$original = [IO.File]::ReadAllBytes($config)
$backup = Join-Path $PSScriptRoot 'client_defaults.runtime-backup.ini'
[IO.File]::WriteAllBytes($backup, $original)
try {
    $settings = [IO.File]::ReadAllText($config)
    $settings = $settings -replace '(?m)^BaseResourceFileName=.*$', "BaseResourceFileName=$PSScriptRoot\RuntimeAssets\swtor_"
    [IO.File]::WriteAllText($config, $settings)
    & "$repo\Diagnostics\TraceReads.exe" $client | Out-File -Encoding utf8 "$PSScriptRoot\trace-runtime-zlib.txt"
} finally {
    [IO.File]::WriteAllBytes($config, $original)
    if ((Get-FileHash $config).Hash -ne (Get-FileHash $backup).Hash) { throw 'Configuration restore verification failed' }
    Write-Output 'Original client configuration restored and verified.'
}
