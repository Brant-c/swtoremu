param([switch]$WhatIfOnly)
$ErrorActionPreference = 'Stop'
# Intentionally regenerate the pinned runtime-input manifest after a source or
# fixture change. Membership and order are preserved exactly; only Bytes and
# SHA256 are recomputed, so this cannot silently add or drop a pinned input.
$identityPath = Join-Path $PSScriptRoot 'identity.csv'
$rows = @(Import-Csv -LiteralPath $identityPath)
if ($rows.Count -lt 10) { throw 'Refusing to regenerate an implausible manifest.' }
$updated = New-Object System.Collections.Generic.List[object]
$changed = 0
foreach ($row in $rows) {
    if (!(Test-Path -LiteralPath $row.Path)) { throw "Pinned input is missing: $($row.Path)" }
    $item = Get-Item -LiteralPath $row.Path
    $hash = (Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash
    if ($hash -ne $row.SHA256) {
        $changed++
        Write-Output ("refreshed: {0} ({1} -> {2} bytes)" -f $row.Path, $row.Bytes, $item.Length)
    }
    $updated.Add([pscustomobject]@{ Path = $row.Path; Bytes = $item.Length; SHA256 = $hash })
}
Write-Output "pinned inputs: $($rows.Count); refreshed: $changed"
if ($WhatIfOnly) { Write-Output 'WhatIfOnly: manifest not written.'; exit 0 }
$csv = '"Path","Bytes","SHA256"' + [Environment]::NewLine
foreach ($row in $updated) {
    $csv += ('"{0}","{1}","{2}"' -f $row.Path, $row.Bytes, $row.SHA256) + [Environment]::NewLine
}
Set-Content -LiteralPath $identityPath -Value $csv -Encoding UTF8 -NoNewline
Write-Output 'identity.csv regenerated.'