param([string]$ClientLog)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$run = Join-Path $root ('RuntimeLogs/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $run | Out-Null
$sources = @(
    'SharpServer/bin/Debug/NexusToR.log',
    'nexusclient/nexusclient/nexus_hook.log',
    'Diagnostics/trace-server.out',
    'Diagnostics/last-server-full.log',
    'Diagnostics/last-server-out.log',
    'Diagnostics/last-nexus-hook.log',
    'Diagnostics/last-compatibility-run.log',
    'Diagnostics/startup-summary.log'
)
$manifest = @(foreach ($relative in $sources) {
    $source = Join-Path $root $relative
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        $dest = Join-Path $run $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
        Copy-Item -LiteralPath $source -Destination $dest
        $copy = Get-Item -LiteralPath $dest
        [pscustomobject]@{Source=$relative;Copy=$relative;Bytes=$copy.Length;SHA256=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash;SourceLastWriteUtc=(Get-Item -LiteralPath $source).LastWriteTimeUtc.ToString('o')}
    }
})
if ($ClientLog) {
    Copy-Item -LiteralPath $ClientLog -Destination (Join-Path $run 'client.log')
    $manifest += [pscustomobject]@{Source=$ClientLog;Copy='client.log';Bytes=(Get-Item -LiteralPath (Join-Path $run 'client.log')).Length;SHA256=(Get-FileHash -LiteralPath (Join-Path $run 'client.log')).Hash;SourceLastWriteUtc=(Get-Item -LiteralPath $ClientLog).LastWriteTimeUtc.ToString('o')}
}
$manifest | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $run 'manifest.csv')
@(Get-Process swtor,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue) | Select-Object ProcessName,Id,StartTime | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $run 'processes.csv')
git -C $root rev-parse HEAD | Set-Content -LiteralPath (Join-Path $run 'git-head.txt')
Write-Output "Log snapshot: $run"
Write-Output 'Copy hashes identify the saved bytes. Active logs may change during copying; compare event times to determine run identity.'
