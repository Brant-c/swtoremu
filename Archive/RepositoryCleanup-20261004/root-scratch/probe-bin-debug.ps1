# verify bin\Debug artifacts post-build + dump key build-output lines
$log = 'C:\Users\brant\AppData\Local\Temp\_bin_debug_check.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== bin\Debug artifact check (post dotnet build) ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$bd = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug'
if (-not (Test-Path $bd)) {
    $null = $lines.Add('[dir missing: ' + $bd + ']')
} else {
    $items = Get-ChildItem -Path $bd -ErrorAction SilentlyContinue
    $null = $lines.Add('[ok] items count=' + $items.Count)
    $want = @('NexusToRServer.exe','NexusToRServer.pdb','NexusToRServer.dll','NexusToRServer.exe.config')
    foreach ($w in $want) {
        $f = Join-Path $bd $w
        if (Test-Path $f) {
            $gi = Get-Item $f
            $len = $gi.Length
            $lwt = $gi.LastWriteTimeUtc.ToString('o')
            $bytes = [System.IO.File]::ReadAllBytes($f)
            $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
            $null = $lines.Add('EXISTS ' + $w + '  len=' + $len + '  LWT=' + $lwt + '  sha=' + $sha)
        } else {
            $null = $lines.Add('MISSING ' + $w)
        }
    }
    $null = $lines.Add('')
    $null = $lines.Add('--- all files in bin\Debug (name | len | LWT) ---')
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $null = $lines.Add('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
    }
}

# dump build output lines 86..147 from the dotnet probe log
$null = $lines.Add('')
$null = $lines.Add('=== dotnet build output (lines 86..147) ===')
$buildLog = 'C:\Users\brant\AppData\Local\Temp\_dotnet_probe.txt'
if (Test-Path $buildLog) {
    $all = [System.IO.File]::ReadAllLines($buildLog)
    $null = $lines.Add('[ok] build log lines=' + $all.Count)
    $s = 86
    $e = [Math]::Min(147, $all.Count - 1)
    for ($i = $s; $i -le $e; $i++) {
        $null = $lines.Add('L' + $i + ': ' + $all[$i])
    }
} else {
    $null = $lines.Add('[missing] build log: ' + $buildLog)
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
