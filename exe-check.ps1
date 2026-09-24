# check the built exe contains the three reply log strings + dispatch cases
$out = 'D:\SWTORClassic\swtoremu\_exe_strings.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== exe string presence check ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$e = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (-not (Test-Path $e)) { $lines.Add('EXE MISSING'); [System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8); return }
$s = [System.IO.File]::ReadAllBytes($e)
$enc = [System.Text.Encoding]::UTF8
$needles = @('CMsgC586BD22: replying','CMsgF96DCDB0: replying','CMsg4A765897: replying')
foreach ($n in $needles) {
    $b = [System.Linq.Enumerable]::ToArray($enc.GetBytes($n))
    $found = $false
    for ($i = 0; $i -le $s.Length - $b.Length; $i++) {
        $m = $true
        for ($j = 0; $j -lt $b.Length; $j++) {
            if ($s[$i + $j] -ne $b[$j]) { $m = $false; break }
        }
        if ($m) { $found = $true; break }
    }
    $lines.Add($n + ' = ' + $found)
}
# also check handler dispatch cases: grep the exe dll? easier: grep the handler source
$h = 'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGamePacketHandler.cs'
if (Test-Path $h) {
    $ht = [System.IO.File]::ReadAllText($h)
    $lines.Add('')
    $lines.Add('--- handler dispatch cases present ---')
    foreach ($cn in @('CMsgC586BD22','CMsgF96DCDB0','CMsg4A765897')) {
        $lines.Add($cn + ' case in handler = ' + $ht.Contains('case PacketType.' + $cn))
        $lines.Add($cn + ' new instantiation in handler = ' + $ht.Contains('new ' + $cn + '()'))
    }
}
[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
