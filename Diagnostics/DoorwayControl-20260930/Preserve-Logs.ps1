param([Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ($Label -notmatch '^[a-zA-Z0-9-]+$') { throw 'Use a simple snapshot label.' }
$dest = Join-Path $PSScriptRoot ($Label + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $dest -ErrorAction Stop | Out-Null
$files = @(
    Get-ChildItem (Join-Path $root 'Diagnostics') -File | Where-Object {
        $_.Name -like 'last-*.log' -or $_.Name -like '*before-latest*' -or $_.Name -eq 'startup-summary.log'
    }
    foreach ($p in @('SharpServer/bin/Debug/NexusToR.log','nexusclient/nexusclient/nexus_hook.log')) {
        Get-Item (Join-Path $root $p) -ErrorAction SilentlyContinue
    }
    Get-Item (Join-Path $env:USERPROFILE 'NexusToR.server.out') -ErrorAction SilentlyContinue
    Get-ChildItem (Join-Path $env:USERPROFILE 'Documents') -Directory -Filter 'SWTOR*' -ErrorAction SilentlyContinue |
        Get-ChildItem -Recurse -File -Filter '*.log' -ErrorAction SilentlyContinue
)
$i = 0
$manifest = foreach ($f in $files | Sort-Object FullName -Unique) {
    $i++
    $copy = Join-Path $dest ('{0:D3}-{1}' -f $i,$f.Name)
    Copy-Item -LiteralPath $f.FullName -Destination $copy -ErrorAction Stop
    [pscustomobject]@{Source=$f.FullName; Saved=$copy; Bytes=(Get-Item $copy).Length;
        SHA256=(Get-FileHash $copy -Algorithm SHA256).Hash; SourceLastWriteUTC=$f.LastWriteTimeUtc.ToString('o')}
}
$manifest | Export-Csv (Join-Path $dest 'manifest.csv') -NoTypeInformation
Get-Date -Format o | Set-Content (Join-Path $dest 'snapshot-time.txt')
Get-TimeZone | Format-List | Out-File (Join-Path $dest 'timezone.txt')
Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue |
    Select-Object Id,ProcessName,Path,StartTime |
    Export-Csv (Join-Path $dest 'processes.csv') -NoTypeInformation
Write-Output $dest
