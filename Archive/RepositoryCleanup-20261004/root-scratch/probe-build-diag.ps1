# Diagnose why bin\Debug\NexusToRServer.exe wasn't updated despite "Build succeeded".
# Check: running processes, obj folder timestamps, file locks, and recent writes.
$log = 'C:\Users\brant\AppData\Local\Temp\_build_diag.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== build diagnostic ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) Is bin\Debug\NexusToRServer.exe locked / in use?
$exeFile = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
$null = $lines.Add('')
$null = $lines.Add('--- exe file state ---')
$null = $lines.Add('exists=' + (Test-Path $exeFile))
if (Test-Path $exeFile) {
    $gi = Get-Item $exeFile
    $null = $lines.Add('LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $null = $lines.Add('len=' + $gi.Length)
    $null = $lines.Add('attributes=' + $gi.Attributes.ToString())
}

# 2) Are any swtoremu server processes running?
$null = $lines.Add('')
$null = $lines.Add('--- server processes ---')
$names = @('NexusToRServer','ShardListServer','ShardServer','TimeServer','LoginServer','PlatformServer')
foreach ($n in $names) {
    $procs = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) {
        foreach ($p in $procs) {
            $null = $lines.Add('RUNNING: ' + $n + ' PID=' + $p.Id + ' LWT=' + $p.StartTimeUtc.ToString('o') + ' modules=' + $p.ModuleCount)
        }
    } else {
        $null = $lines.Add('not-running: ' + $n)
    }
}

# 3) Check obj\Debug timestamps (where MSBuild actually compiles to)
$null = $lines.Add('')
$null = $lines.Add('--- obj\Debug ---')
$objDir = 'D:\SWTORClassic\swtoremu\SharpServer\obj\Debug'
if (Test-Path $objDir) {
    $items = Get-ChildItem -Path $objDir -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending
    $null = $lines.Add('items count=' + ($items.Count))
    $shown = 0
    foreach ($i in $items) {
        if ($shown -ge 25) { $null = $lines.Add('  ... (more)'); break }
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $null = $lines.Add('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
        $shown++
    }
} else { $null = $lines.Add('[dir missing]') }

# 4) Check bin\Debug -> bin\Debug\NexusToRServer.exe vs bin\Debug themselves
$null = $lines.Add('')
$null = $lines.Add('--- bin\Debug contents (all) ---')
$bd = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug'
if (Test-Path $bd) {
    $items = Get-ChildItem -Path $bd -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $null = $lines.Add('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
    }
} else { $null = $lines.Add('[dir missing]') }

# 5) Try to open the exe for write (detect lock)
$null = $lines.Add('')
$null = $lines.Add('--- exe write-test (FileShare.None) ---')
try {
    $fs = [System.IO.File]::Open($exeFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $null = $lines.Add('[ok] exe is writable (not locked for write)')
    $fs.Close()
} catch {
    $null = $lines.Add('[LOCKED] cannot open exe for write: ' + $_.Exception.Message)
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
