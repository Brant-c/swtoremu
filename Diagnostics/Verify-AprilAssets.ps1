$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$manifest=Get-Content (Join-Path $PSScriptRoot 'april-asset-manifest.json') -Raw | ConvertFrom-Json
$results=foreach($file in $manifest) {
    $path=Join-Path (Join-Path $root 'Assets2012April') $file.name
    $status='missing'; $actualSize=$null; $actualHash=$null
    if(Test-Path -LiteralPath $path) {
        $actualSize=(Get-Item -LiteralPath $path).Length
        $actualHash=(Get-FileHash -LiteralPath $path -Algorithm MD5).Hash.ToLowerInvariant()
        $status=if($actualSize -eq $file.size -and $actualHash -eq $file.md5){'verified'}else{'mismatch'}
    }
    [pscustomobject]@{name=$file.name;status=$status;size=$actualSize;md5=$actualHash}
}
$failures=@($results | Where-Object status -ne 'verified')
$report=[pscustomobject]@{
    checkedAt=(Get-Date).ToString('o')
    manifestCount=$manifest.Count
    verifiedCount=$results.Count-$failures.Count
    complete=($failures.Count -eq 0)
    archives=@($results)
}
$report | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $PSScriptRoot 'april-asset-verification.json')
if($failures.Count) {
    $failures | Format-Table name,status
    throw ('April asset verification incomplete: {0}/{1} verified.' -f $report.verifiedCount,$report.manifestCount)
}
'PASS: all {0} April archives match manifest size and MD5.' -f $manifest.Count
