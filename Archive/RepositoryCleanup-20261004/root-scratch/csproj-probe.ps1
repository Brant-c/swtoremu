$out = 'D:\SWTORClassic\swtoremu\_csproj_probe.txt'
$p = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$t = [System.IO.File]::ReadAllText($p)
$i = $t.IndexOf('CMsgC26464A9.cs')
$out_lines = New-Object System.Collections.Generic.List[string]
if ($i -ge 0) {
    $null = $out_lines.Add('FOUND at index ' + $i)
    $null = $out_lines.Add('context: [' + $t.Substring([Math]::Max(0,$i-40), [Math]::Min(80, $t.Length-$i)) + ']')
    # show the exact line containing CMsgC26464A9
    $before = $t.Substring(0, $i)
    $lineStart = $before.LastIndexOf("`n") + 1
    $lineEnd = $t.IndexOf("`n", $i)
    if ($lineEnd -lt 0) { $lineEnd = $t.Length }
    $null = $out_lines.Add('full line: [' + $t.Substring($lineStart, $lineEnd - $lineStart) + ']')
} else {
    $null = $out_lines.Add('NOT FOUND')
}
# also check each new file exists
foreach ($f in @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')) {
    $fp = 'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client\' + $f
    $null = $out_lines.Add($f + ' on disk: ' + (Test-Path $fp) + ' len=' + (if (Test-Path $fp) { (Get-Item $fp).Length } else { 'NA' }))
}
[System.IO.File]::WriteAllText($out, ($out_lines -join "`r`n"), [System.Text.Encoding]::UTF8)
