# CRT3 + tooling probe (safe .NET IO writes to root). Read-only except CRT3 Status (also read-only).
 $crtLog = 'D:\SWTORClassic\swtoremu\_crt3_status.txt'
 $toolLog = 'D:\SWTORClassic\swtoremu\_tooling_status.txt'

 # --- CRT3 Status (positional arg, read-only) ---
 $script = 'D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1'
 $lines = New-Object System.Collections.Generic.List[string]
 $null = $lines.Add('=== CRT3 Status (via Set-Crt3Variant.ps1 Status) ===')
 try {
     $out = & $script Status 2>&1
     $null = $lines.Add(($out -join "`n"))
 } catch {
     $null = $lines.Add('[Set-Crt3Variant.ps1 Status failed: ' + $_.Exception.Message + ']')
 }
 $null = $lines.Add('')
 $null = $lines.Add('=== CRT3 fixture file hash/len ===')
 $f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt'
 try {
     if (Test-Path $f) {
         $bytes = [System.IO.File]::ReadAllBytes($f)
         $hash = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
         $null = $lines.Add('EXISTS: ' + $f)
         $null = $lines.Add('len: ' + $bytes.Length)
         $null = $lines.Add('SHA256: ' + $hash)
         $null = $lines.Add('head32 hex: ' + ([System.BitConverter]::ToString($bytes,0,4)).Replace('-',' '))
         $null = $lines.Add('head32 uint32: 0x' + ([System.BitConverter]::ToUInt32($bytes,0)).ToString('X8'))
         $null = $lines.Add('tail byte: 0x' + $bytes[-1].ToString('X2'))
     } else {
         $null = $lines.Add('MISSING: ' + $f)
     }
 } catch {
     $null = $lines.Add('[fixture probe failed: ' + $_.Exception.Message + ']')
 }
 [System.IO.File]::WriteAllText($crtLog, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)

 # --- Tooling probe (safe: where.exe via Start-Process RedirectStandardOutput) ---
 $lines2 = New-Object System.Collections.Generic.List[string]
 $null = $lines2.Add('=== tooling probe ===')
 foreach ($exe in @('git','msbuild','csc')) {
     $null = $lines2.Add('--- which ' + $exe + ' ---')
     $tmp = Join-Path $env:TEMP ('where_' + $exe + '.tmp')
     try {
         $proc = Start-Process -FilePath where.exe -ArgumentList $exe -NoNewWindow -Wait -RedirectStandardOutput $tmp -PassThru -ErrorAction Stop
         $txt = ''
         if (Test-Path $tmp) { $txt = [System.IO.File]::ReadAllText($tmp, [System.Text.Encoding]::Default) }
         if ($txt) { $null = $lines2.Add($txt) } else { $null = $lines2.Add('[no output]') }
     } catch {
         $null = $lines2.Add('[where ' + $exe + ' failed: ' + $_.Exception.Message + ']')
     }
 }
 $null = $lines2.Add('')
 $null = $lines2.Add('--- VS2022 Community MSBuild.exe ---')
 $m = 'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe'
 if (Test-Path $m) { $null = $lines2.Add($m) } else { $null = $lines2.Add('NOT FOUND at expected path') }
 if ($env:VSINSTALLDIR) { $null = $lines2.Add('VSINSTALLDIR=' + $env:VSINSTALLDIR) } else { $null = $lines2.Add('VSINSTALLDIR=[null]') }
 if ($env:DevEnvDir) { $null = $lines2.Add('DevEnvDir=' + $env:DevEnvDir) } else { $null = $lines2.Add('DevEnvDir=[null]') }
 $null = $lines2.Add('')
 $null = $lines2.Add('--- Diagnostics dir test ---')
 $d = 'D:\SWTORClassic\swtoremu\Diagnostics'
 $null = $lines2.Add('Test-Path Diagnostics: ' + (Test-Path $d))
 $null = $lines2.Add('Test-Path Container: ' + (Test-Path $d -PathType Container))
 try {
     $items = Get-ChildItem -Path $d -ErrorAction Stop
     $null = $lines2.Add('Items in Diagnostics (count=' + $items.Count + '):')
     foreach ($i in $items) {
         $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
         $null = $lines2.Add('  ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o') + '  len=' + $len)
     }
 } catch {
     $null = $lines2.Add('[Get-ChildItem Diagnostics failed: ' + $_.Exception.Message + ']')
 }
 try {
     $t = $d + '\ProbeWriteTest2.txt'
     [System.IO.File]::WriteAllText($t, 'probe-write-ok-2', [System.Text.Encoding]::UTF8)
     $null = $lines2.Add('ProbeWriteTest2.txt written: ' + (Test-Path $t))
     Remove-Item $t -ErrorAction SilentlyContinue
 } catch {
     $null = $lines2.Add('[ProbeWriteTest2 write failed: ' + $_.Exception.Message + ']')
 }
 [System.IO.File]::WriteAllText($toolLog, ($lines2 -join "`r`n"), [System.Text.Encoding]::UTF8)
