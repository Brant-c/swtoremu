$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$destination = Join-Path $PSScriptRoot ('prelaunch-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $destination | Out-Null
$paths = @(
    (Join-Path $root 'SharpServer\bin\Debug\NexusToR.log'),
    (Join-Path $root 'nexusclient\nexusclient\nexus_hook.log'),
    (Join-Path $PSScriptRoot 'launcher-console.log'),
    (Join-Path $PSScriptRoot 'launcher-errors.log')
)
$manifest = foreach ($path in $paths) {
    if (!(Test-Path -LiteralPath $path)) { continue }
    $source = Get-Item -LiteralPath $path
    $saved = Join-Path $destination $source.Name
    $mode = 'full'
    if ($source.Length -le 8MB) {
        Copy-Item -LiteralPath $path -Destination $saved
    } else {
        $mode = 'last-2000-lines'
        Get-Content -LiteralPath $path -Tail 2000 | Set-Content -LiteralPath $saved
    }
    [pscustomobject]@{Source=$path;Saved=$saved;Mode=$mode;SourceBytes=$source.Length;
        SavedBytes=(Get-Item -LiteralPath $saved).Length;
        SHA256=(Get-FileHash -LiteralPath $saved -Algorithm SHA256).Hash}
}
$manifest | Export-Csv -LiteralPath (Join-Path $destination 'manifest.csv') -NoTypeInformation
Write-Output "Current logs preserved: $destination"
