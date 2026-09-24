# tooling probe v6 (defensive, no Out-File, writes to root)
$of = 'D:\SWTORClassic\swtoremu\ToolingProbe6.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== which git ===')
try {
    $cmd = Start-Process -FilePath where.exe -ArgumentList git -NoNewWindow -Wait -RedirectStandardOutput "$env:TEMP\where_git.tmp" -PassThru
    if (Test-Path "$env:TEMP\where_git.tmp") { $null = $lines.Add((Get-Content "$env:TEMP\where_git.tmp" -Raw)) } else { $null = $lines.Add('[no output captured]') }
} catch {
    $null = $lines.Add('[where git failed: ' + $_.Exception.Message + ']')
}
$null = $lines.Add('')
$null = $lines.Add('=== which msbuild ===')
try {
    $cmd = Start-Process -FilePath where.exe -ArgumentList msbuild -NoNewWindow -Wait -RedirectStandardOutput "$env:TEMP\where_msbuild.tmp" -PassThru
    if (Test-Path "$env:TEMP\where_msbuild.tmp") { $null = $lines.Add((Get-Content "$env:TEMP\where_msbuild.tmp" -Raw)) } else { $null = $lines.Add('[no output captured]') }
} catch {
    $null = $lines.Add('[where msbuild failed: ' + $_.Exception.Message + ']')
}
$null = $lines.Add('')
$null = $lines.Add('=== VS2022 Community MSBuild.exe ===')
$m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
if (Test-Path $m) { $null = $lines.Add($m) } else { $null = $lines.Add('NOT FOUND at expected path') }
$null = $lines.Add('VSINSTALLDIR=' + ($env:VSINSTALLDIR ?? '[null]'))
$null = $lines.Add('DevEnvDir=' + ($env:DevEnvDir ?? '[null]'))
$null = $lines.Add('')
$null = $lines.Add('=== Diagnostics dir test ===')
$d = 'D:\SWTORClassic\swtoremu\Diagnostics'
$null = $lines.Add('Test-Path Diagnostics: ' + (Test-Path $d))
$null = $lines.Add('Test-Path Container: ' + (Test-Path $d -PathType Container))
try {
    $items = Get-ChildItem -Path $d -ErrorAction Stop
    $null = $lines.Add('Items in Diagnostics (count=' + $items.Count + '):')
    foreach ($i in $items) {
        $null = $lines.Add('  ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o') + '  len=' + ($i.Length ?? '[dir]'))
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
