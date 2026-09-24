# minimal: write to TEMP path and read back, plus a Get-Process test
$log = 'C:\Users\brant\AppData\Local\Temp\_simple_write_test.txt'
try {
    [System.IO.File]::WriteAllText($log, 'write-ok ' + [DateTimeOffset]::UtcNow.ToString('o'), [System.Text.Encoding]::UTF8)
    Write-Output 'Wrote ' + $log
} catch {
    Write-Output 'FAIL write: ' + $_.Exception.Message
}

# Get-Process test
try {
    $p = Get-Process -Name 'NexusToRServer' -ErrorAction SilentlyContinue
    Write-Output 'Get-Process NexusToRServer: ' + $(if ($p) { $p.Count } else { 'null/empty' })
} catch {
    Write-Output 'Get-Process FAILED: ' + $_.Exception.Message
}

# also write the same log content
try {
    $lines = New-Object System.Collections.Generic.List[string]
    $null = $lines.Add('simple write test')
    $null = $lines.Add('[ok] wrote ' + $log)
    [System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
    Write-Output 'appended ok'
} catch {
    Write-Output 'append FAIL: ' + $_.Exception.Message
}
