$log = 'C:\Users\brant\AppData\Local\Temp\_server_state.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== server process state ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(NexusToRServer|ShardListServer|ShardServer|TimeServer|LoginServer|PlatformServer)$' }
$null = $lines.Add('matching processes: ' + $procs.Count)
foreach ($p in $procs) {
    $null = $lines.Add('  ' + $p.ProcessName + ' PID=' + $p.Id + ' StartTime=' + $p.StartTime.ToString('o') + ' CPU=' + $p.TotalProcessorTime.ToString() + ' Resp=' + $p.Responding)
}
[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
