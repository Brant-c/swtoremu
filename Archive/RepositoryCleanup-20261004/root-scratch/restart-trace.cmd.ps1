# Launch the trace run in background (hidden window), then poll.
# DO NOT wait for the process; it runs detached.

$batch = 'D:\SWTORClassic\swtoremu\Run-SWTORClassic-Trace-Tython.cmd'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'cmd.exe'
$psi.Arguments = '/c ' + '"' + $batch + '"'
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.WindowStyle = 'Hidden'
$proc = [System.Diagnostics.Process]::Start($psi)
Write-Output 'started process id=' + $proc.Id + ' path=' + $batch
Write-Output 'now waiting 10s for servers to come up...'
Start-Sleep -Seconds 10
$proc.Refresh()
Write-Output 'after 10s: hasExited=' + $proc.HasExited + ' exitcode=' + $proc.ExitCode
