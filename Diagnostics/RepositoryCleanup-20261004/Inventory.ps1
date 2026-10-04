param([switch]$After)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $root
$upstream = @{}
foreach ($p in @(git ls-tree -r --name-only upstream/master)) { $upstream[$p] = $true }
$head = @{}
foreach ($p in @(git ls-tree -r --name-only HEAD)) { $head[$p] = $true }
$tracked = @{}
foreach ($p in @(git -c core.quotepath=false ls-files)) { $tracked[$p] = $true }
$paths = @(rg --files --hidden --no-ignore -g '!**/.git/**')
if ($LASTEXITCODE -ne 0) { throw 'Filesystem inventory failed' }
$rows = foreach ($raw in $paths) {
    $p = $raw.Replace('\','/')
    $f = Get-Item -Force -LiteralPath (Join-Path $root $raw)
    $origin = if ($upstream.ContainsKey($p)) {'UPSTREAM-PATH'} elseif ($head.ContainsKey($p)) {'FORK-COMMITTED'} else {'LOCAL-UNCOMMITTED-OR-IGNORED'}
    [pscustomobject]@{Path=$p;TopLevel=($p -split '/')[0];Bytes=$f.Length;Tracked=$tracked.ContainsKey($p);Origin=$origin}
}
$suffix = if ($After) {'after'} else {'before'}
$rows | Sort-Object Path | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot "inventory-$suffix.csv")
$rows | Group-Object TopLevel | ForEach-Object {
    [pscustomobject]@{Directory=$_.Name;Files=$_.Count;Bytes=($_.Group | Measure-Object Bytes -Sum).Sum;Tracked=@($_.Group | Where-Object Tracked).Count}
} | Sort-Object Directory | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot "tree-summary-$suffix.csv")
# Hash runtime sources, fixtures and launcher inputs. This identifies cleanup's
# preservation boundary without copying the entire client/resource installation.
$runtime = foreach ($r in $rows) {
    if ($r.Path -match '^(SharpServer/.*\.(cs|csproj|acrt|aaw|aeff|bin)|Client/Hook/.*\.(cpp|h|vcxproj)|Run-.*\.(cmd|bat)|Diagnostics/CompatibilityLauncher\.(cpp|exe)|Diagnostics/GeneratedPhaseCandidate/.*\.acrt|SharpServer/bin/Debug/NexusToRServer\.exe|Client/Hook/Bin/x86/MemoryMan\.dll)$') {
        [pscustomobject]@{Path=$r.Path;Bytes=$r.Bytes;SHA256=(Get-FileHash -LiteralPath (Join-Path $root $r.Path) -Algorithm SHA256).Hash}
    }
}
$runtime | Sort-Object Path | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot "runtime-hashes-$suffix.csv")
$rows | Group-Object Origin | Select-Object Name,Count
Write-Output "Inventory ${suffix}: $($rows.Count) filesystem files; $($tracked.Count) indexed files; $($upstream.Count) upstream paths; $($head.Count) HEAD paths."
