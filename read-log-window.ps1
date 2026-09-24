$log = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
$out = 'D:\SWTORClassic\swtoremu\_log_window.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== log window: last 120 lines + CMsgC586BD22 first-occurrence context ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$lines.Add('log LWT=' + (Get-Item $log).LastWriteTimeUtc.ToString('o'))
$all = [System.IO.File]::ReadAllLines($log)
$lines.Add('total lines=' + $all.Count)
$lines.Add('')

# last 90 lines
$start = [Math]::Max(0, $all.Count - 90)
for ($i = $start; $i -lt $all.Count; $i++) {
    $lines.Add('L' + ($i+1) + ': ' + $all[$i])
}
$lines.Add('')
$lines.Add('=== first occurrences of the three opcodes in the log ===')
foreach ($tag in @('CMsgC586BD22','CMsgF96DCDB0','CMsg4A765897')) {
    $idx = -1
    for ($i = 0; $i -lt $all.Count; $i++) {
        if ($all[$i].Contains($tag)) { $idx = $i; break }
    }
    if ($idx -ge 0) {
        $lines.Add('')
        $lines.Add('--- first ' + $tag + ' at L' + ($idx+1) + ' ---')
        $a = [Math]::Max(0, $idx - 2)
        $b = [Math]::Min($all.Count - 1, $idx + 4)
        for ($i = $a; $i -le $b; $i++) {
            $lines.Add('L' + ($i+1) + ': ' + $all[$i])
        }
    } else {
        $lines.Add($tag + ': NOT FOUND in log')
    }
}

[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
