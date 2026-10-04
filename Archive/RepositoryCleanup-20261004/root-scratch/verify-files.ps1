# verify CRT3 .disabled + 3 new .cs files exist; write to workspace root
$log = 'D:\SWTORClassic\swtoremu\_verify_files.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== verify files ' + [DateTimeOffset]::UtcNow.ToString('o') + ' ===')
$null = $lines.Add('')

# CRT3 .disabled
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt.disabled'
if (Test-Path $f) {
    $gi = Get-Item $f
    $null = $lines.Add('CRT3.disabled EXISTS  len=' + $gi.Length + '  LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    try {
        $b = [System.IO.File]::ReadAllBytes($f)
        $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($b).Replace('-','')).ToLowerInvariant()
        $null = $lines.Add('  sha=' + $sha + '  tail=0x' + $b[-1].ToString('X2'))
    } catch {
        $null = $lines.Add('  [sha failed: ' + $_.Exception.Message + ']')
    }
} else {
    $null = $lines.Add('CRT3.disabled MISSING (PROBLEM)')
}

$null = $lines.Add('')
$null = $lines.Add('--- new reply .cs files ---')
$base = 'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client'
foreach ($name in @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')) {
    $p = Join-Path $base $name
    if (Test-Path $p) {
        $gi = Get-Item $p
        $null = $lines.Add('EXISTS: ' + $name + '  len=' + $gi.Length + '  LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    } else {
        $null = $lines.Add('MISSING: ' + $name + '  (PROBLEM)')
    }
}

$null = $lines.Add('')
$null = $lines.Add('--- csproj tail: does it contain our 3 files? ---')
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
if (Test-Path $csproj) {
    $txt = [System.IO.File]::ReadAllText($csproj, [System.Text.Encoding]::UTF8)
    foreach ($name in @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')) {
        $found = $txt.Contains($name)
        $null = $lines.Add($name + ' in csproj: ' + $found)
    }
} else {
    $null = $lines.Add('csproj MISSING')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
