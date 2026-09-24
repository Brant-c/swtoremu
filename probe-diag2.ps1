# probe everything; write its own log to a hardcoded TEMP path
$log = 'C:\Users\brant\AppData\Local\Temp\_probe_diag2.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== start diagnostics ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) CRT3 script
$lines.Add('--- CRT3 script Status ---') | Out-Null
$script = 'D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1'
try {
    $null = $lines.Add('[ok] script path exists: ' + (Test-Path $script))
    $res = & $script Status 2>&1
    $null = $lines.Add('[ok] & script Status returned ' + $res.Count + ' line(s):')
    foreach ($r in $res) { $null = $lines.Add('   ' + $r) }
} catch {
    $null = $lines.Add('[FAIL] & script Status: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 2) fixture read
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
    $null = $lines.Add('[ok] head32 hex=' + ([System.BitConverter]::ToString($bytes,0,4)).Replace('-',' '))
    $null = $lines.Add('[ok] head32 uint32=0x' + ([System.BitConverter]::ToUInt32($bytes,0)).ToString('X8'))
    $null = $lines.Add('[ok] tail byte=0x' + $bytes[-1].ToString('X2'))
} catch {
    $null = $lines.Add('[FAIL] fixture read: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 3) where.exe git/msbuild/csc via Start-Process
$lines.Add('') | Out-Null
$lines.Add('--- where.exe probes ---') | Out-Null
foreach ($exe in @('git','msbuild','csc')) {
    $lines.Add('--- where ' + $exe + ' ---') | Out-Null
    $tmp = 'C:\Users\brant\AppData\Local\Temp\where_' + $exe + '.tmp'
    try {
        $proc = Start-Process -FilePath where.exe -ArgumentList $exe -NoNewWindow -Wait -RedirectStandardOutput $tmp -PassThru -ErrorAction Stop
        $null = $lines.Add('[ok] Start-Process exit=' + $proc.ExitCode)
        if (Test-Path $tmp) {
            $txt = [System.IO.File]::ReadAllText($tmp, [System.Text.Encoding]::Default)
            $null = $lines.Add('[ok] tmp content: ' + $txt.Replace("`r","").Replace("`n"," / "))
        } else {
            $null = $lines.Add('[warn] tmp file not created')
        }
    } catch {
        $null = $lines.Add('[FAIL] Start-Process ' + $exe + ': ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
    }
}

# 4) Get-ChildItem Diagnostics
$lines.Add('') | Out-Null
$lines.Add('--- Get-ChildItem Diagnostics ---') | Out-Null
$d = 'D:\SWTORClassic\swtoremu\Diagnostics'
try {
    $items = Get-ChildItem -Path $d -ErrorAction Stop
    $null = $lines.Add('[ok] items count=' + $items.Count)
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $null = $lines.Add('   ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o') + '  len=' + $len)
    }
} catch {
    $null = $lines.Add('[FAIL] Get-ChildItem: ' + $_.Exception.GetType().FullName + ' : ' + $_.Exception.Message)
}

# 5) VS vars
$lines.Add('') | Out-Null
$lines.Add('--- VS env vars ---') | Out-Null
if ($env:VSINSTALLDIR) { $null = $lines.Add('VSINSTALLDIR=' + $env:VSINSTALLDIR) } else { $null = $lines.Add('VSINSTALLDIR=[null]') }
if ($env:DevEnvDir) { $null = $lines.Add('DevEnvDir=' + $env:DevEnvDir) } else { $null = $lines.Add('DevEnvDir=[null]') }

# 6) MSBuild.exe at expected path
$lines.Add('') | Out-Null
$lines.Add('--- MSBuild.exe expected path ---') | Out-Null
$m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
if (Test-Path $m) { $null = $lines.Add('FOUND: ' + $m) } else { $null = $lines.Add('NOT FOUND at expected path') }

# write log
[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
