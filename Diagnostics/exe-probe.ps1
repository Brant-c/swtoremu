# swtoremu: exe/csproj probe (read-only)
$paths = "D:\SWTORClassic\swtoremu\SharpServer\bin\Debug","D:\SWTORClassic\swtoremu\SharpServer\bin\Release","D:\SWTORClassic\swtoremu"
"=== NexusToRServer.exe copies ===" | Out-File -FilePath "D:\SWTORClassic\swtoremu\Diagnostics\ExeProbe.txt" -Encoding utf8
Get-ChildItem -Path $paths -Filter "NexusToRServer.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, @{n='LastWriteTimeUtc';e={$_.LastWriteTimeUtc}}, @{n='Length';e={$_.Length}} | Format-Table -AutoSize | Out-File -Append -FilePath "D:\SWTORClassic\swtoremu\Diagnostics\ExeProbe.txt"
"" | Out-File -Append -FilePath "D:\SWTORClassic\swtoremu\Diagnostics\ExeProbe.txt"
"=== csproj files ===" | Out-File -Append -FilePath "D:\SWTORClassic\swtoremu\Diagnostics\ExeProbe.txt"
Get-ChildItem -Recurse -Path $paths -Filter "NexusToRServer.csproj" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName | Out-File -Append -FilePath "D:\SWTORClassic\swtoremu\Diagnostics\ExeProbe.txt"
