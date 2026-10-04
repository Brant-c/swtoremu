# verify: is a server running? what's the exe LWT?
$log = 'C:\Users\brant\AppData\Local\Temp\_state_check.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== current state check ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) running server processes (simple)
$null = $lines.Add('')
$null = $lines.Add('--- running server processes ---')
$names = @('NexusToRServer','ShardServer','ShardListServer','TimeServer','LoginServer','PlatformServer')
foreach ($n in $names) {
    $p = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($p -and $p.Count -gt 0) {
        $null = $lines.Add('RUNNING: ' + $n + ' count=' + $p.Count)
        foreach ($pr in $p) {
            $null = $lines.Add('   PID=' + $pr.Id + ' start=' + $pr.StartTime.ToString('o'))
        }
    } else {
        $null = $lines.Add('not-running: ' + $n)
    }
}

# 2) exe LWT + hash
$null = $lines.Add('')
$null = $lines.Add('--- NexusToRServer.exe ---')
$exe = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (Test-Path $exe) {
    $gi = Get-Item $exe
    $null = $lines.Add('exists=True')
    $null = $lines.Add('LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $null = $lines.Add('len=' + $gi.Length)
    $bytes = [System.IO.File]::ReadAllBytes($exe)
    $null = $lines.Add('sha256=' + [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace('-','').ToLowerInvariant())
} else {
    $null = $lines.Add('MISSING: ' + $exe)
}

# 3) pdb LWT
$null = $lines.Add('')
$null = $lines.Add('--- NexusToRServer.pdb ---')
$pdb = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.pdb'
if (Test-Path $pdb) {
    $gi = Get-Item $pdb
    $null = $lines.Add('LWT=' + $gi.LastWriteTimeUtc.ToString('o') + ' len=' + $gi.Length)
} else {
    $null = $lines.Add('MISSING')
}

# 4) log LWT and size
$null = $lines.Add('')
$null = $lines.Add('--- NexusToR.log ---')
$logf = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
if (Test-Path $logf) {
    $gi = Get-Item $logf
    $null = $lines.Add('LWT=' + $gi.LastWriteTimeUtc.ToString('o') + ' len=' + $gi.Length)
} else {
    $null = $lines.Add('MISSING')
}

# 5) tasklist snapshot
$null = $lines.Add('')
$null = $lines.Add('--- tasklist snapshot ---')
$tl = tasklist /FI 'IMAGENAME eq NexusToRServer.exe' 2>&1
$null = $lines.Add($tl)

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
