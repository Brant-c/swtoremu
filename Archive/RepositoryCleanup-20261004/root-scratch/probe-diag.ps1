# diagnostics: capture every failure to TEMP (which we know is writable)
$tmpLog = Join-Path $env:TEMP '_probe_diag.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== start diagnostics ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) Test & $script Status
$lines.Add('--- test & $script Status ---') | Out-Null
$script = 'D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1'
try {
    $null = $lines.Add('[ok] script path exists: ' + (Test-Path $script))
    $res = & $script Status 2>&1
    $null = $lines.Add('[ok] & script Status returned. lines:')
    foreach ($r in $res) { $null = $lines.Add('   ' + $r) }
} catch {
    $null = $lines.Add('[FAIL] & script Status: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 2) Test fixture read
$lines.Add('') | Out-Null
$lines.Add('--- fixture read ---') | Out-Null
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt'
try {
    $null = $lines.Add('[ok] Test-Path fixture: ' + (Test-Path $f))
    $bytes = [System.IO.File]::ReadAllBytes($f)
    $null = $lines.Add('[ok] ReadAllBytes len=' + $bytes.Length)
    $hashBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    $hash = [System.BitConverter]::ToString($hashBytes).Replace('-','').ToLowerInvariant()
    $null = $lines.Add('[ok] SHA256=' + $hash)
} catch {
    $null = $lines.Add('[FAIL] fixture read: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 3) Test Start-Process -RedirectStandardOutput
$lines.Add('') | Out-Null
$lines.Add('--- Start-Process where.exe git ---') | Out-Null
$tmp = Join-Path $env:TEMP 'where_git_redir.tmp'
try {
    $proc = Start-Process -FilePath where.exe -ArgumentList git -NoNewWindow -Wait -RedirectStandardOutput $tmp -PassThru -ErrorAction Stop
    $null = $lines.Add('[ok] Start-Process exit=' + $proc.ExitCode)
    if (Test-Path $tmp) {
        $txt = [System.IO.File]::ReadAllText($tmp, [System.Text.Encoding]::Default)
        $null = $lines.Add('[ok] tmp content: ' + $txt.Replace("`r","").Replace("`n"," / "))
    } else {
        $null = $lines.Add('[warn] tmp file not created')
    }
} catch {
    $null = $lines.Add('[FAIL] Start-Process: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 4) Test Get-ChildItem Diagnostics
$lines.Add('') | Out-Null
$lines.Add('--- Get-ChildItem Diagnostics ---') | Out-Null
$d = 'D:\SWTORClassic\swtoremu\Diagnostics'
try {
    $items = Get-ChildItem -Path $d -ErrorAction Stop
    $null = $lines.Add('[ok] items count=' + $items.Count)
} catch {
    $null = $lines.Add('[FAIL] Get-ChildItem: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 5) Test TEMP write (sanity)
$lines.Add('') | Out-Null
$lines.Add('--- TEMP write sanity ---') | Out-Null
try {
    [System.IO.File]::WriteAllText($tmpLog, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
    $null = $lines.Add('[ok] wrote ' + $tmpLog)
} catch {
    # last resort: write directly and hope
    try {
        [System.IO.File]::WriteAllText($tmpLog, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
        $null = $lines.Add('[ok2] wrote ' + $tmpLog + ' (second try)')
    } catch {
        $null = $lines.Add('[FATAL] cannot write to TEMP: ' + $_.Exception.Message)
    }
}

[System.IO.File]::WriteAllText($tmpLog, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
