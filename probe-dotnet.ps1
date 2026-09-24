# probe dotnet buildability of the csproj + search for build scripts; write to TEMP log
$log = 'C:\Users\brant\AppData\Local\Temp\_dotnet_probe.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== dotnet probe ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) dotnet version
$null = $lines.Add('')
$null = $lines.Add('--- dotnet --version ---')
try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'C:\Program Files\dotnet\dotnet.exe'
    $psi.Arguments = '--version'
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    $null = $lines.Add('exit=' + $p.ExitCode)
    $null = $lines.Add('stdout: ' + $out)
    if ($err) { $null = $lines.Add('stderr: ' + $err) }
} catch {
    $null = $lines.Add('[FAIL] dotnet --version: ' + $_.Exception.Message)
}

# 2) dotnet --info (first 60 lines)
$null = $lines.Add('')
$null = $lines.Add('--- dotnet --info (first 80 lines) ---')
try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'C:\Program Files\dotnet\dotnet.exe'
    $psi.Arguments = '--info'
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $all = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    $null = $lines.Add('exit=' + $p.ExitCode)
    $arr = $all -split "`r`n"
    $cnt = [Math]::Min($arr.Count, 80)
    for ($i = 0; $i -lt $cnt; $i++) { $null = $lines.Add('  ' + $arr[$i]) }
    if ($err -and $err.Trim()) { $null = $lines.Add('stderr: ' + $err) }
} catch {
    $null = $lines.Add('[FAIL] dotnet --info: ' + $_.Exception.Message)
}

# 3) Try dotnet build on the csproj (dry-ish: just see if it parses). Target Debug|x86.
$null = $lines.Add('')
$null = $lines.Add('--- dotnet build NexusToRServer.csproj (Debug|x86, short timeout) ---')
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'C:\Program Files\dotnet\dotnet.exe'
    $psi.Arguments = 'build "' + $csproj + '" -c Debug -f net48 --nologo --verbosity quiet'
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    # read with timeout awareness: use async read via thread
    $out = $p.StandardOutput.ReadToEnd()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit(60000)
    $null = $lines.Add('exit=' + $p.ExitCode + ' (after ' + $p.StartTime + ')')
    if ($out) { $null = $lines.Add('stdout:'); foreach ($l in $out -split "`r`n") { if ($l) { $null = $lines.Add('  ' + $l) } } }
    if ($err) { $null = $lines.Add('stderr:'); foreach ($l in $err -split "`r`n") { if ($l) { $null = $lines.Add('  ' + $l) } } }
    if ($p.HasExited -eq $false) { $null = $lines.Add('[warn] process still running after 60s; killing'); $p.Kill(); $p.WaitForExit() }
} catch {
    $null = $lines.Add('[FAIL] dotnet build: ' + $_.Exception.Message)
}

# 4) Search for any .cmd / build scripts in repo root and SharpServer
$null = $lines.Add('')
$null = $lines.Add('--- build script search (root + SharpServer) ---')
try {
    $roots = @('D:\SWTORClassic\swtoremu', 'D:\SWTORClassic\swtoremu\SharpServer')
    foreach ($r in $roots) {
        $null = $lines.Add('--- ' + $r + ' ---')
        if (-not (Test-Path $r)) { $null = $lines.Add('[dir missing]'); continue }
        $items = Get-ChildItem -Path $r -Filter '*.cmd' -ErrorAction Stop
        $null = $lines.Add('[ok] cmd files count=' + $items.Count)
        foreach ($i in $items) { $null = $lines.Add('   ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o')) }
        $items2 = Get-ChildItem -Path $r -Filter '*.ps1' -ErrorAction SilentlyContinue
        $null = $lines.Add('[ok] ps1 files count=' + $items2.Count)
    }
} catch {
    $null = $lines.Add('[FAIL] search: ' + $_.Exception.Message)
}

# 5) Check bin\Debug contents (artifact indicators)
$null = $lines.Add('')
$null = $lines.Add('--- bin\Debug artifact check ---')
$bd = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug'
if (Test-Path $bd) {
    $items = Get-ChildItem -Path $bd -ErrorAction SilentlyContinue
    $null = $lines.Add('[ok] items count=' + $items.Count)
    # key files
    foreach ($want in @('NexusToRServer.exe','NexusToRServer.pdb','NexusToRServer.dll','NexusToRServer.exe.config')) {
        $f = Join-Path $bd $want
        $null = $lines.Add('  ' + $want + ': ' + (if (Test-Path $f) { 'EXISTS len=' + (Get-Item $f).Length } else { 'missing' }))
    }
} else {
    $null = $lines.Add('[dir missing]')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
