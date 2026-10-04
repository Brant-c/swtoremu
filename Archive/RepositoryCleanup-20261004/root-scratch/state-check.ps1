# verify: is a server running? what's the exe LWT? when was trace launched?
$log = 'C:\Users\brant\AppData\Local\Temp\_state_check.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== current state check ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

# 1) running server processes
$null = $lines.Add('')
$null = $lines.Add('--- running server processes ---')
$names = @('NexusToRServer','ShardServer','ShardListServer','TimeServer','LoginServer','PlatformServer')
foreach ($n in $names) {
    $p = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($p) {
        foreach ($pr in $p) {
            $null = $lines.Add('RUNNING: ' + $n + ' PID=' + $pr.Id + ' start=' + $pr.StartTime.ToString('o') + ' cmd=' + (Get-WmiObject Win32_Process -Filter ('ProcessId=' + $pr.Id) -ErrorAction SilentlyContinue | ForEach-Object { $_.CommandLine }) interpolated=$false)
            # simpler cmdline
            try {
                $wmi = Get-WmiObject -Class Win32_Process -Filter ('ProcessId=' + $pr.Id) -ErrorAction SilentlyContinue
                if ($wmi) { $null = $lines.Add('   cmdline: ' + $wmi.CommandLine) }
            } catch {}
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
$pdb = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.pdb'
if (Test-Path $pdb) {
    $gi = Get-Item $pdb
    $null = $lines.Add('pdb LWT=' + $gi.LastWriteTimeUtc.ToString('o') + ' len=' + $gi.Length)
} else {
    $null = $lines.Add('pdb MISSING')
}

# 4) log LWT and size
$logf = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
if (Test-Path $logf) {
    $gi = Get-Item $logf
    $null = $lines.Add('NexusToR.log LWT=' + $gi.LastWriteTimeUtc.ToString('o') + ' len=' + $gi.Length)
} else {
    $null = $lines.Add('NexusToR.log MISSING')
}

# 5) tasklist snapshot (process start times)
$null = $lines.Add('')
$null = $lines.Add('--- tasklist snapshot ---')
$tl = tasklist /FI 'IMAGENAME eq NexusToRServer.exe' 2>&1
$null = $lines.Add($tl)
$tl2 = tasklist /FI 'IMAGENAME eq ShardServer.exe' 2>&1
$null = $lines.Add($tl2)

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
