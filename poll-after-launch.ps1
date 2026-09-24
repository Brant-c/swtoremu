# check running server processes + fresh log entries
$logFile = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== server process check (poll after launch) ===')
$null = $lines.Add('[poll] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$names = @('NexusToRServer','ShardServer','TimeServer','LoginServer')
foreach ($n in $names) {
    $procs = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) {
        $null = $lines.Add('RUNNING: ' + $n + ' count=' + $procs.Count)
        foreach ($p in $procs) {
            $null = $lines.Add('   PID=' + $p.Id + ' started=' + $p.StartTime.ToString('o') + ' CPU=' + $p.TotalProcessorTime.ToString())
        }
    } else {
        $null = $lines.Add('not-running: ' + $n)
    }
}
$null = $lines.Add('')
$null = $lines.Add('=== NexusToR.log tail (last 40 non-empty lines) ===')
if (Test-Path $logFile) {
    $gi = Get-Item $logFile
    $null = $lines.Add('log file: size=' + $gi.Length + ' LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $content = [System.IO.File]::ReadAllText($logFile, [System.Text.Encoding]::UTF8)
    $allLines = $content -split '`r`n'
    # take last 40 non-empty
    $nonEmpty = New-Object System.Collections.Generic.List[string]
    foreach ($l in $allLines) {
        if ($l.Trim()) { $null = $nonEmpty.Add($l) }
    }
    $start = [Math]::Max(0, $nonEmpty.Count - 40)
    $null = $lines.Add('[ok] total non-empty lines=' + $nonEmpty.Count)
    $null = $lines.Add('--- last ' + ([Math]::Min(40, $nonEmpty.Count)) + ' non-empty lines ---')
    for ($i = $start; $i -lt $nonEmpty.Count; $i++) {
        $null = $lines.Add('L' + ($i + 1) + ': ' + $nonEmpty[$i])
    }
} else {
    $null = $lines.Add('MISSING: ' + $logFile)
}

[System.IO.File]::WriteAllText('C:\Users\brant\AppData\Local\Temp\_poll_after_launch.txt', ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
