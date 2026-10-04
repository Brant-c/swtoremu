$out = 'D:\SWTORClassic\swtoremu\_csproj_probe.txt'
$p = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$t = [System.IO.File]::ReadAllText($p)
$i = $t.IndexOf('CMsgC26464A9.cs')
$o = New-Object System.Collections.Generic.List[string]
$null = $o.Add('=== csproj probe ===')
if ($i -ge 0) {
    $null = $o.Add('FOUND CMsgC26464A9.cs at index ' + $i)
    $start = [Math]::Max(0, $i - 40)
    $len = [Math]::Min(90, $t.Length - $start)
    $null = $o.Add('context: [' + $t.Substring($start, $len) + ']')
    $lineStart = $t.Substring(0, $i).LastIndexOf("`n") + 1
    $lineEnd = $t.IndexOf("`n", $i)
    if ($lineEnd -lt 0) { $lineEnd = $t.Length }
    $null = $o.Add('full line: [' + $t.Substring($lineStart, $lineEnd - $lineStart) + ']')
} else {
    $null = $o.Add('NOT FOUND CMsgC26464A9.cs')
}
$null = $o.Add('')
function fileInfo($path) {
    if (Test-Path $path) {
        $gi = Get-Item $path
        return $gi.Name + ' exists len=' + $gi.Length + ' LWT=' + $gi.LastWriteTimeUtc.ToString('o')
    } else {
        return $path + ' MISSING'
    }
}
foreach ($f in @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')) {
    $fp = 'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client\' + $f
    $null = $o.Add(fileInfo($fp))
}
$null = $o.Add('')
$null = $o.Add('csproj total length: ' + $t.Length)
[System.IO.File]::WriteAllText($out, ($o -join "`r`n"), [System.Text.Encoding]::UTF8)
