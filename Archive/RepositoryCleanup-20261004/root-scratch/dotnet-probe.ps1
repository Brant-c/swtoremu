# minimal repro: write a file to root via .NET, write timestamped log to root
$log = 'D:\SWTORClassic\swtoremu\_dotnet_log.txt'
$target = 'D:\SWTORClassic\swtoremu\_dotnet_probe.txt'
$ts = [DateTimeOffset]::UtcNow.ToString('o')
try {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    [System.IO.File]::WriteAllText($target, 'written: ' + $ts, [System.Text.Encoding]::UTF8)
    $sw.Stop()
    $msg = 'OK wrote ' + $target + ' in ' + $sw.ElapsedMilliseconds + 'ms  exists=' + (Test-Path $target)
} catch {
    $msg = 'FAIL: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message
}
$full = '=== dotnet write probe ===' + "`r`n" + $ts + "`r`n" + $msg + "`r`n" + 'target exists after: ' + (Test-Path $target)
[System.IO.File]::WriteAllText($log, $full, [System.Text.Encoding]::UTF8)
