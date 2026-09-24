# tooling + CRT3 fixture probe (writes via .NET IO to root)
$of = 'D:\SWTORClassic\swtoremu\ToolingProbe5.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== which git ===')
$out = where.exe git 2>$null
$null = $lines.Add(($out -join "`n"))
$null = $lines.Add('')
$null = $lines.Add('=== which msbuild ===')
$out = where.exe msbuild 2>$null
$null = $lines.Add(($out -join "`n"))
$null = $lines.Add('')
$null = $lines.Add('=== which csc ===')
$out = where.exe csc 2>$null
$null = $lines.Add(($out -join "`n"))
$null = $lines.Add('')
$null = $lines.Add('=== VS2022 Community MSBuild.exe ===')
$m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
if (Test-Path $m) { $null = $lines.Add($m) } else { $null = $lines.Add('NOT FOUND at expected path') }
if ($env:VSINSTALLDIR) { $null = $lines.Add('VSINSTALLDIR=' + $env:VSINSTALLDIR) }
if ($env:DevEnvDir) { $null = $lines.Add('DevEnvDir=' + $env:DevEnvDir) }
[System.IO.File]::WriteAllText($of, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
