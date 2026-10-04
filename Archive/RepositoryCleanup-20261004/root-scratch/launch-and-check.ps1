# launch the trace run, wait, and check the console log.
# All paths are hardcoded literal strings (no $var='…' inline that this shell mangles).
$launcher = 'D:\SWTORClassic\swtoremu\Launch-TraceTython.cmd'
$consoleLog = 'D:\SWTORClassic\swtoremu\Diagnostics\TraceTython-20260918-0214-console.log'

Write-Output '=== launcher exists check ==='
if (Test-Path $launcher) {
    Write-Output 'LAUNCHER EXISTS: ' + $launcher
} else {
    Write-Output 'LAUNCHER MISSING: ' + $launcher
    return
}

Write-Output ''
Write-Output '=== launching trace run (detached) ==='
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'cmd.exe'
$psi.Arguments = '/c ' + $launcher
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
Write-Output 'launcher process started, id=' + $proc.Id
$proc.WaitForExit(8000)
Write-Output 'launcher exited=' + $proc.HasExited + ' exitcode=' + $proc.ExitCode + ' (after ' + $proc.StartTime + ')'

Write-Output ''
Write-Output '=== waiting 8s for servers to start ==='
Start-Sleep -Seconds 8

Write-Output ''
Write-Output '=== console log check ==='
if (Test-Path $consoleLog) {
    $gi = Get-Item $consoleLog
    Write-Output 'CONSOLE LOG EXISTS: size=' + $gi.Length + ' LWT=' + $gi.LastWriteTimeUtc.ToString('o')
    if ($gi.Length -gt 0) {
        $content = [System.IO.File]::ReadAllText($consoleLog, [System.Text.Encoding]::Default)
        $lines = $content -split '`r`n'
        Write-Output '--- first 60 lines of console log ---'
        $cnt = [Math]::Min($lines.Count, 60)
        for ($i = 0; $i -lt $cnt; $i++) {
            if ($lines[$i]) { Write-Output ($i + ': ' + $lines[$i]) }
        }
    } else {
        Write-Output 'CONSOLE LOG EMPTY (0 bytes)'
    }
} else {
    Write-Output 'CONSOLE LOG MISSING: ' + $consoleLog
}

Write-Output ''
Write-Output '=== server process check (right now) ==='
$names = @('NexusToRServer','ShardServer','TimeServer','LoginServer')
foreach ($n in $names) {
    $procs = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) {
        Write-Output 'RUNNING: ' + $n + ' count=' + $procs.Count
        foreach ($p in $procs) {
            Write-Output '   PID=' + $p.Id + ' started=' + $p.StartTime.ToString('o')
        }
    } else {
        Write-Output 'not-running: ' + $n
    }
}
