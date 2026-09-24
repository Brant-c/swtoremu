# tooling probe v8 (PS5-safe: no ??, no Out-File, writes to root via .NET IO)
$of = 'D:\SWTORClassic\swtoremu\ToolingProbe8.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== which git ===')
try {
    $tmp = "$env:TEMP\where_git.tmp"
    $proc = Start-Process -FilePath where.exe -ArgumentList git -NoNewWindow -Wait -RedirectStandardOutput $tmp -PassThru -ErrorAction Stop
    if (Test-Path $tmp) {
        $s = Get-Content $tmp -Raw -ErrorAction SilentlyContinue
        if ($s) { $null = $lines.Add($s) } else { $null = $lines.Add('[empty]') }
    } else {
        $null = $lines.Add('[no tmp file]')
    }
} catch {
    $null = $lines.Add('[where git failed: ' + $_.Exception.Message + ']')
}
$null = $lines.Add('')
$null = $lines.Add('=== which msbuild ===')
try {
    $tmp = "$env:TEMP\where_msbuild.tmp"
    $proc = Start-Process -FilePath where.exe -ArgumentList msbuild -NoNewWindow -Wait -RedirectStandardOutput $tmp -PassThru -ErrorAction Stop
    if (Test-Path $tmp) {
        $s = Get-Content $tmp -Raw -ErrorAction SilentlyContinue
        if ($s) { $null = $lines.Add($s) } else { $null = $lines.Add('[empty]') }
    } else {
        $null = $lines.Add('[no tmp file]')
    }
} catch {
    $null = $lines.Add('[where msbuild failed: ' + $_.Exception.Message + ']')
}
$null = $lines.Add('')
$null = $lines.Add('=== VS2022 Community MSBuild.exe ===')
$m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
if (Test-Path $m) { $null = $lines.Add($m) } else { $null = $lines.Add('NOT FOUND at expected path') }
if ($env:VSINSTALLDIR) { $null = $lines.Add('VSINSTALLDIR=' + $env:VSINSTALLDIR) } else { $null = $lines.Add('VSINSTALLDIR=[null]') }
if ($env:DevEnvDir) { $null = $lines.Add('DevEnvDir=' + $env:DevEnvDir) } else { $null = $lines.Add('DevEnvDir=[null]') }
$null = $lines.Add('')
$null = $lines.Add('=== Diagnostics dir test ===')
$d = 'D:\SWTORClassic\swtoremu\Diagnostics'
$null = $lines.Add('Test-Path Diagnostics: ' + (Test-Path $d))
$null = $lines.Add('Test-Path Container: ' + (Test-Path $d -PathType Container))
try {
    $items = Get-ChildItem -Path $d -ErrorAction Stop
    $null = $lines.Add('Items in Diagnostics (count=' + $items.Count + '):')
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $null = $lines.Add('  ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o') + '  len=' + $len)
    }
} catch {
    $null = $lines.Add('[Get-ChildItem Diagnostics failed: ' + $_.Exception.Message + ']')
}
try {
    $t = $d + '\ProbeWriteTest.txt'
    [System.IO.File]::WriteAllText($t, 'probe-write-ok', [System.Text.Encoding]::UTF8)
    $null = $lines.Add('ProbeWriteTest.txt written: ' + (Test-Path $t))
    Remove-Item $t -ErrorAction SilentlyContinue
} catch {
    $null = $lines.Add('[ProbeWriteTest write failed: ' + $_.Exception.Message + ']')
}
[System.IO.File]::WriteAllText($of, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
