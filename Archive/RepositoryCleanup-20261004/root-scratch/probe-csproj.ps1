# check if the 3 new .cs files are in the csproj Compile list
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$txt = [System.IO.File]::ReadAllText($csproj)
$p1 = 'CMsgC586BD22'
$p2 = 'CMsgF96DCDB0'
$p3 = 'CMsg4A765897'

$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== csproj check ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$null = $lines.Add('')
$null = $lines.Add('CMsgC586BD22.cs in csproj: ' + $txt.Contains($p1))
$null = $lines.Add('CMsgF96DCDB0.cs in csproj: ' + $txt.Contains($p2))
$null = $lines.Add('CMsg4A765897.cs in csproj: ' + $txt.Contains($p3))
$null = $lines.Add('')

# count Compile includes
$matches = [regex]::Matches($txt, '<Compile Include')
$null = $lines.Add('Compile Include count: ' + $matches.Count)
$null = $lines.Add('')

# show the last 15 Compile includes (to see where new files would go)
$null = $lines.Add('--- last 15 Compile includes ---')
$all = [regex]::Matches($txt, '<Compile Include="([^"]+)"')
$cnt = 0
for ($i = $all.Count - 1; $i -ge 0 -and $cnt -lt 15; $i--) {
    $null = $lines.Add('  ' + $all[$i].Groups[1].Value)
    $cnt++
}
$null = $lines.Add('')
$null = $lines.Add('--- new .cs files on disk ---')
foreach ($f in @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')) {
    $fp = Join-Path 'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client' $f
    if (Test-Path $fp) {
        $gi = Get-Item $fp
        $null = $lines.Add('EXISTS: ' + $f + ' LWT=' + $gi.LastWriteTimeUtc.ToString('o') + ' len=' + $gi.Length)
    } else {
        $null = $lines.Add('MISSING: ' + $f)
    }
}

[System.IO.File]::WriteAllText('C:\Users\brant\AppData\Local\Temp\_csproj_check.txt', ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
