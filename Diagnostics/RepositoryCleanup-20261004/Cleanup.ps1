$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $root
$archive = Join-Path $root 'Archive/RepositoryCleanup-20261004'
$upstream = @{}
foreach ($p in @(git ls-tree -r --name-only upstream/master)) { $upstream[$p] = $true }
$head = @{}
foreach ($p in @(git ls-tree -r --name-only HEAD)) { $head[$p] = $true }
if (@(git diff --cached --name-only).Count) { throw 'Index changed; preserve it before cleanup.' }
if (@(git branch --list cleanup-baseline-20261004).Count -eq 0) {
    git branch cleanup-baseline-20261004 HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Could not protect HEAD with checkpoint branch' }
}
# Exact root-only candidates from the inventory, all later-fork files. Active
# run/experiment launch chains and their pinned files stay at their existing paths.
$candidates = @(Get-ChildItem -LiteralPath $root -File | Where-Object {
    $_.Extension -eq '.ps1' -or $_.Name -match '^_(?!JPEXTRACT).*\.txt(\.latin1)?$' -or
    $_.Name -match '^ToolingProbe\d+\.txt$' -or
    $_.Name -in @('Launch-TraceTython.cmd','Launch-Trace-Tython.cmd','Launch-Trace-Tython-F96Echo.cmd')
})
$manifest = foreach ($f in $candidates) {
    if ($upstream.ContainsKey($f.Name) -or !$head.ContainsKey($f.Name)) { throw "Unreviewed origin: $($f.Name)" }
    $source = [IO.Path]::GetFullPath($f.FullName)
    $target = [IO.Path]::GetFullPath((Join-Path $archive ('root-scratch/' + $f.Name)))
    if (!$source.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        !$target.StartsWith($archive + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe move boundary' }
    if (Test-Path -LiteralPath $target) { throw "Archive destination exists: $target" }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
    Move-Item -LiteralPath $source -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $hash) { throw 'Archive hash mismatch' }
    [pscustomobject]@{Original=$f.Name;Archive=('Archive/RepositoryCleanup-20261004/root-scratch/' + $f.Name);SHA256=$hash;Action='ARCHIVE';Reason='Fork-only one-shot root probe, output or redundant trace wrapper; not in supported launch chain'}
}
$manifest | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot 'archive-manifest.csv')
foreach ($name in @('README.md','START-HERE.md','AGENTS.md','.gitignore')) {
    $dest = Join-Path $archive ('before-docs/' + $name)
    New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
    Copy-Item -LiteralPath (Join-Path $root $name) -Destination $dest
}
# Remove only later-fork generated artifacts from the INDEX. Bytes remain on disk.
# Required fixture/config/resource inputs and upstream paths are never selected.
$untrack = @(git -c core.quotepath=false ls-files | Where-Object {
    !$upstream.ContainsKey($_) -and (
      $_ -match '(^|/)(\.vs|obj|Obj|__pycache__)/' -or
      $_ -match '(^|/)(bin|Bin)/.*\.(pdb|exp|iobj|ipdb|cache|tlog)$' -or
      $_ -match '^Diagnostics/(Extracted2012|python-deps|ProcessMonitor)/' -or
      $_ -match '^Diagnostics/[^/]*Build/.*\.(pdb|cache)$' -or
      $_ -match '^Diagnostics/(last-[^/]+|nexus[^/]*before-latest|startup-summary)\.log$' -or
      $_ -match '^SharpServer/bin/Debug/NexusToR\.log$' -or
      $_ -match '^nexusclient/.*(\.log|\.dmp)$'
    )
})
$untrack | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'untracked-generated-paths.txt')
# Each path is passed as an argument (no string-built deletion commands).
foreach ($p in $untrack) {
    git rm --cached -f --quiet -- $p
    if ($LASTEXITCODE -ne 0) { throw "Index removal failed: $p" }
}
Write-Output "Archived $($manifest.Count) fork-only root files; removed $($untrack.Count) generated/local paths from tracking; no physical deletions."
