# Restore CRT3 to recorded original, then disable it (rename to .disabled).
# This establishes the proven crash-free baseline from the 18:11 run.
$script = 'D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1'
$fixture = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt'
$disabled = $fixture + '.disabled'

Write-Output '=== Step 1: Status before restore ==='
& $script Status

Write-Output ''
Write-Output '=== Step 2: Restore (writes recorded original 55 bytes) ==='
& $script Restore

Write-Output ''
Write-Output '=== Step 3: Status after restore (should show recorded original, sha 3E79B4C9...) ==='
& $script Status

Write-Output ''
Write-Output '=== Step 4: Disable (rename to .disabled) ==='
if (Test-Path $fixture) {
    Rename-Item -Path $fixture -NewName ($fixture + '.disabled') -Force
    Write-Output 'Renamed to .disabled'
} else {
    Write-Output 'Fixture already absent; nothing to rename.'
}

Write-Output ''
Write-Output '=== Step 5: Verify dir state ==='
$gci = Get-ChildItem -Path 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT' -ErrorAction SilentlyContinue
foreach ($i in $gci) {
    $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
    Write-Output ('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
}
