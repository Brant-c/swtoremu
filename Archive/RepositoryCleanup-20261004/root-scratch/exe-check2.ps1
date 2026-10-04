# check the built exe contains the three reply log strings + dispatch cases
$out = 'D:\SWTORClassic\swtoremu\_exe_strings2.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== exe string presence check v2 ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (-not (Test-Path $f)) { $lines.Add('EXE MISSING'); goto done }
$raw = [System.IO.File]::ReadAllBytes($f)
$enc = [System.Text.Encoding]::UTF8
$txt = $enc.GetString($raw)
$needles = @('CMsgC586BD22','CMsgF96DCDB0','CMsg4A765897','replying','AreaRequestRPC','SystemRequestRPC')
foreach ($n in $needles) {
    $idx = $txt.IndexOf($n)
    $lines.Add($n + ' found=' + ($idx -ge 0) + ' idx=' + $idx)
}
# Also check the handler source for the dispatch + instantiation
$h = 'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGamePacketHandler.cs'
if (Test-Path $h) {
    $ht = [System.IO.File]::ReadAllText($h)
    $lines.Add('')
    $lines.Add('--- handler dispatch (raw source) ---')
    foreach ($cn in @('CMsgC586BD22','CMsgF96DCDB0','CMsg4A765897')) {
        $lines.Add($cn + ' case-in-handler = ' + $ht.Contains('case PacketType.' + $cn))
        $lines.Add($cn + ' new-in-handler = ' + $ht.Contains('new ' + $cn + '()'))
    }
}
:done
[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
