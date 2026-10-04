# proper UTF-16LE string search in the exe + handler dispatch verification
$out = 'D:\SWTORClassic\swtoremu\_exe_strings3.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== exe string presence check v3 (UTF-16LE aware) ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (-not (Test-Path $f)) { $lines.Add('EXE MISSING'); goto done }
$raw = [System.IO.File]::ReadAllBytes($f)
$needles = @('CMsgC586BD22: replying','CMsgF96DCDB0: replying','CMsg4A765897: replying','replying to area-entry','CMsgC586BD22()','CMsgF96DCDB0()','CMsg4A765897()')
foreach ($n in $needles) {
    # search both as raw ASCII/UTF8 and as UTF-16LE
    $b8 = [System.Text.Encoding]::UTF8.GetBytes($n)
    $found8 = $false
    for ($i = 0; $i -le $raw.Length - $b8.Length; $i++) {
        $m = $true
        for ($j = 0; $j -lt $b8.Length; $j++) { if ($raw[$i+$j] -ne $b8[$j]) { $m=$false; break } }
        if ($m) { $found8 = $true; break }
    }
    # UTF-16LE
    $b16 = [System.Text.Encoding]::Unicode.GetBytes($n)
    $found16 = $false
    for ($i = 0; $i -le $raw.Length - $b16.Length; $i++) {
        $m = $true
        for ($j = 0; $j -lt $b16.Length; $j++) { if ($raw[$i+$j] -ne $b16[$j]) { $m=$false; break } }
        if ($m) { $found16 = $true; break }
    }
    $lines.Add($n + ' | ascii-in-exe=' + $found8 + ' | utf16-in-exe=' + $found16)
}
# handler dispatch
$h = 'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGamePacketHandler.cs'
if (Test-Path $h) {
    $ht = [System.IO.File]::ReadAllText($h)
    $lines.Add('')
    $lines.Add('--- handler dispatch ---')
    foreach ($cn in @('CMsgC586BD22','CMsgF96DCDB0','CMsg4A765897')) {
        $lines.Add($cn + ' case+new-in-handler = ' + ($ht.Contains('case PacketType.' + $cn) -and $ht.Contains('new ' + $cn + '()')))
    }
}
:done
$lines.Add('')
$lines.Add('[end] ' + [DateTimeOffset]::UtcNow.ToString('o'))
[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
