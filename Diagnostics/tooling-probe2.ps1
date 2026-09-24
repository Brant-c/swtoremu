# Tooling probe v3 (plain strings only, no here-strings)
$of = 'D:\SWTORClassic\swtoremu\Diagnostics\ToolingProbe2.txt'
"=== which git ===" | Out-File -FilePath $of -Encoding utf8
where.exe git 2>$null | Out-File -Append -FilePath $of
"" | Out-File -Append -FilePath $of -Encoding utf8
"=== which msbuild ===" | Out-File -Append -FilePath $of -Encoding utf8
where.exe msbuild 2>$null | Out-File -Append -FilePath $of
"" | Out-File -Append -FilePath $of -Encoding utf8
"=== which csc ===" | Out-File -Append -FilePath $of -Encoding utf8
where.exe csc 2>$null | Out-File -Append -FilePath $of
"" | Out-File -Append -FilePath $of -Encoding utf8
"=== VS2022 Community MSBuild.exe ===" | Out-File -Append -FilePath $of -Encoding utf8
$m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
if (Test-Path $m) { Write-Output $m | Out-File -Append -FilePath $of } else { Write-Output 'NOT FOUND at expected path' | Out-File -Append -FilePath $of }
if ($env:VSINSTALLDIR) { 'VSINSTALLDIR=' + $env:VSINSTALLDIR | Out-File -Append -FilePath $of }
if ($env:DevEnvDir) { 'DevEnvDir=' + $env:DevEnvDir | Out-File -Append -FilePath $of }
