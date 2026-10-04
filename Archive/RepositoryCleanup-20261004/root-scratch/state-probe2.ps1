# state probe: exe LWT, new-cs presence, csproj entries, server process, CRT3 disabled
$out = 'D:\SWTORClassic\swtoremu\_state_probe2.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== state probe 2 ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$lines.Add('')

# 1) exe
$exe = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (Test-Path $exe) {
    $gi = Get-Item $exe
    $lines.Add('EXE: ' + $exe)
    $lines.Add('  LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $lines.Add('  len=' + $gi.Length)
} else {
    $lines.Add('EXE: MISSING')
}
$lines.Add('')

# 2) new cs files
$src = 'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client'
$files = @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')
$lines.Add('--- new reply .cs files ---')
foreach ($f in $files) {
    $fp = Join-Path $src $f
    if (Test-Path $fp) {
        $gi = Get-Item $fp
        $lines.Add($f + '  EXISTS  LWT=' + $gi.LastWriteTimeUtc.ToString('o') + '  len=' + $gi.Length)
    } else {
        $lines.Add($f + '  MISSING')
    }
}
$lines.Add('')

# 3) csproj entries
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$lines.Add('--- csproj mentions ---')
if (Test-Path $csproj) {
    $txt = [System.IO.File]::ReadAllText($csproj)
    foreach ($f in $files) {
        $present = $txt.Contains($f)
        $lines.Add($f + '  in-csproj=' + $present)
    }
} else {
    $lines.Add('csproj MISSING')
}
$lines.Add('')

# 4) server process
$lines.Add('--- server process ---')
$proc = Get-Process -Name NexusToRServer -ErrorAction SilentlyContinue
if ($proc -and $proc.Count -gt 0) {
    $lines.Add('NexusToRServer RUNNING count=' + $proc.Count)
    foreach ($p in $proc) {
        $lines.Add('  PID=' + $p.Id)
    }
} else {
    $lines.Add('NexusToRServer NOT running')
}
$lines.Add('')

# 5) CRT3 disabled
$dir = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT'
$f = 'tython_blockout-4611686019869492753-1.3.acrt.disabled'
$fp = Join-Path $dir $f
if (Test-Path $fp) {
    $lines.Add('CRT3_DISABLED=YES  (' + $fp + ')')
} else {
    $lines.Add('CRT3_DISABLED=NO  (missing: ' + $fp + ')')
}

[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
