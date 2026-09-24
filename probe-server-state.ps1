# clean-slate check: are any swtoremu server processes running?
# writes results to a known TEMP file (hardcoded).
$log = 'C:\Users\brant\AppData\Local\Temp\_server_process_check.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== server process check ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$names = @('NexusToRServer','ShardServer','TimeServer','LoginServer')
foreach ($n in $names) {
    $procs = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) {
        $null = $lines.Add('RUNNING: ' + $n + ' count=' + $procs.Count)
        foreach ($p in $procs) {
            $null = $lines.Add('   PID=' + $p.Id + ' LWT=' + $p.StartTime.ToString('o') + ' CPU=' + $p.TotalProcessorTime.ToString())
        }
    } else {
        $null = $lines.Add('not-running: ' + $n)
    }
}
$null = $lines.Add('')
$null = $lines.Add('=== CRT3 .disabled file verification ===')
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt.disabled'
if (Test-Path $f) {
    $b = [System.IO.File]::ReadAllBytes($f)
    $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($b)).Replace('-','').ToLowerInvariant()
    $null = $lines.Add('disabled-exists=True')
    $null = $lines.Add('len=' + $b.Length)
    $null = $lines.Add('sha=' + $sha)
    $null = $lines.Add('tail=0x' + $b[-1].ToString('X2'))
    $null = $lines.Add('head32=0x' + [BitConverter]::ToUInt32($b,0).ToString('X8'))
} else {
    $null = $lines.Add('disabled-exists=False (PROBLEM: CRT3.disabled missing)')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
