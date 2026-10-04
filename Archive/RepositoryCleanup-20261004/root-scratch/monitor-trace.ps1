$log = 'C:\Users\brant\AppData\Local\Temp\_trace_monitor.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== trace run monitor ===')
$null = $lines.Add('[check] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# server processes
$procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(NexusToRServer|ShardListServer|ShardServer|TimeServer|LoginServer|PlatformServer)$' }
$null = $lines.Add('server processes: ' + $procs.Count)
foreach ($p in $procs) {
    $null = $lines.Add('  ' + $p.ProcessName + ' PID=' + $p.Id + ' Start=' + $p.StartTime.ToString('o') + ' CPU=' + $p.TotalProcessorTime.ToString() + ' Resp=' + $p.Responding)
}

# log tail
$null = $lines.Add('')
$null = $lines.Add('=== NexusToR.log tail (last 40 lines) ===')
$lf = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
if (Test-Path $lf) {
    $all = [System.IO.File]::ReadAllLines($lf)
    $null = $lines.Add('[ok] log lines=' + $all.Count)
    $s = [Math]::Max(0, $all.Count - 40)
    for ($i = $s; $i -lt $all.Count; $i++) {
        $null = $lines.Add('L' + ($i+1) + ': ' + $all[$i])
    }
    # also flag any lines with today's date or from the last 30 min
    $null = $lines.Add('')
    $null = $lines.Add('=== lines from last 60 min (or today) ===')
    $cutoff = [DateTimeOffset]::UtcNow.AddMinutes(-60)
    $recent = @()
    foreach ($l in $all) {
        if ($l -match '^\[(\d{4}-\d{2}-\d{2})') {
            $d = [DateTimeOffset]::Parse($Matches[1] + ' 00:00:00 +00:00')
            if ($d -ge $cutoff) { $recent += $l }
        }
    }
    $null = $lines.Add('recent count=' + $recent.Count)
    foreach ($r in $recent) { $null = $lines.Add('  ' + $r) }
} else {
    $null = $lines.Add('[missing] NexusToR.log')
}

# trace transcript
$null = $lines.Add('')
$null = $lines.Add('=== _trace_run_transcript.txt (last 30 lines) ===')
$tf = 'D:\SWTORClassic\swtoremu\_trace_run_transcript.txt'
if (Test-Path $tf) {
    $all = [System.IO.File]::ReadAllLines($tf)
    $null = $lines.Add('[ok] transcript lines=' + $all.Count)
    $s = [Math]::Max(0, $all.Count - 30)
    for ($i = $s; $i -lt $all.Count; $i++) {
        $null = $lines.Add('  ' + $all[$i])
    }
} else {
    $null = $lines.Add('[missing] _trace_run_transcript.txt (may not exist yet)')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
