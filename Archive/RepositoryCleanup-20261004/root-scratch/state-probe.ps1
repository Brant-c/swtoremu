# state probe: write to workspace root (known-writable), avoid inline branching anti-patterns
$log = 'D:\SWTORClassic\swtoremu\_state_probe.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== state probe ' + [DateTimeOffset]::UtcNow.ToString('o') + ' ===')
$null = $lines.Add('')

# 1) running processes (tasklist)
$null = $lines.Add('--- tasklist NexusToRServer ---')
try { $tl = tasklist /FI 'IMAGENAME eq NexusToRServer.exe' 2>&1; $null = $lines.Add($tl) } catch { $null = $lines.Add('[tasklist failed: ' + $_.Exception.Message + ']') }
$null = $lines.Add('')
$null = $lines.Add('--- tasklist ShardListServer ---')
try { $tl = tasklist /FI 'IMAGENAME eq ShardListServer.exe' 2>&1; $null = $lines.Add($tl) } catch { $null = $lines.Add('[tasklist failed]') }
$null = $lines.Add('')
$null = $lines.Add('--- tasklist TimeServer ---')
try { $tl = tasklist /FI 'IMAGENAME eq TimeServer.exe' 2>&1; $null = $lines.Add($tl) } catch { $null = $lines.Add('[tasklist failed]') }

# 2) CRT3 state
$null = $lines.Add('')
$null = $lines.Add('--- CRT3 dir ---')
$crtDir = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT'
if (Test-Path $crtDir -PathType Container) {
    $gci = Get-ChildItem -Path $crtDir
    $null = $lines.Add('[ok] CRT dir exists, items=' + $gci.Count)
    foreach ($i in $gci) {
        $name = $i.Name
        $len = $i.Length
        $lwt = $i.LastWriteTimeUtc.ToString('o')
        $killer = $name.Contains('1.3')
        $null = $lines.Add('  ' + $name + '  len=' + $len + '  LWT=' + $lwt + (if ($killer) { '  <-- CRT3' } else { '' }))
    }
} else {
    $null = $lines.Add('[missing] CRT dir')
}

# 3) exe state
$null = $lines.Add('')
$null = $lines.Add('--- exe ---')
$exe = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (Test-Path $exe) {
    $gi = Get-Item $exe
    $len = $gi.Length
    $lwt = $gi.LastWriteTimeUtc.ToString('o')
    try { $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.IO.File]::ReadAllBytes($exe)).Replace('-','')).ToLowerInvariant() } catch { $sha = '[hash-failed]' }
    $null = $lines.Add('EXISTS len=' + $len + ' LWT=' + $lwt + ' sha=' + $sha)
} else {
    $null = $lines.Add('MISSING exe')
}

# 4) log growth
$null = $lines.Add('')
$null = $lines.Add('--- log ---')
$logf = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
if (Test-Path $logf) {
    $gi = Get-Item $logf
    $len = $gi.Length
    $lwt = $gi.LastWriteTimeUtc.ToString('o')
    $null = $lines.Add('log len=' + $len + ' LWT=' + $lwt)
} else {
    $null = $lines.Add('log MISSING')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
