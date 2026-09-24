# probe PacketAnalyser contents + locate C# TOR.Character definition
$out = 'D:\SWTORClassic\swtoremu\_probe_pa_and_tor.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== PacketAnalyser + C# TOR.Character probe ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$lines.Add('')

# 1) PacketAnalyser: list root + any exe/config/README
$pa = 'D:\SWTORClassic\swtoremu\Tools\PacketAnalyser'
if (Test-Path $pa) {
    $lines.Add('--- PacketAnalyser root ---')
    $items = Get-ChildItem -Path $pa -ErrorAction SilentlyContinue
    $lines.Add('items count=' + $items.Count)
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $lines.Add('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
    }
    $lines.Add('')
    # recurse for executables / dlls / readme / scripts
    $lines.Add('--- PacketAnalyser recurse (exe/dll/config/json/md/txt/cs/csproj) ---')
    $found = New-Object System.Collections.Generic.List[string]
    try {
        $all = Get-ChildItem -Path $pa -Recurse -ErrorAction SilentlyContinue
        foreach ($i in $all) {
            if ($i.PSIsContainer) { continue }
            $ext = $i.Extension.ToLowerInvariant()
            if ($ext -in '.exe','.dll','.config','.json','.md','.txt','.cs','.csproj','.bat','.cmd') {
                $found.Add($i.FullName + '  len=' + $i.Length + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
            }
        }
    } catch {
        $lines.Add('[recurse FAIL: ' + $_.Exception.Message + ']')
    }
    $lines.Add('found count=' + $found.Count)
    foreach ($f in $found) { $lines.Add('  ' + $f) }
} else {
    $lines.Add('PacketAnalyser: MISSING')
}
$lines.Add('')

# 2) nexusclient tree top-level
$nc = 'D:\SWTORClassic\swtoremu\nexusclient\nexusclient'
if (Test-Path $nc) {
    $lines.Add('--- nexusclient top-level (dirs + files) ---')
    $items = Get-ChildItem -Path $nc -ErrorAction SilentlyContinue
    $lines.Add('items count=' + $items.Count)
    foreach ($i in $items) {
        $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
        $lines.Add('  ' + $i.Name + '  len=' + $len + '  LWT=' + $i.LastWriteTimeUtc.ToString('o'))
    }
} else {
    $lines.Add('nexusclient: MISSING')
}
$lines.Add('')

# 3) locate C# TOR.Character definition: search SharpServer + any referenced TOR project
$lines.Add('=== locate C# TOR.Character ===')
$candidates = @(
    'D:\SWTORClassic\swtoremu\SharpServer',
    'D:\SWTORClassic\swtoremu\Tools',
    'D:\SWTORClassic\swtoremu\nexusclient'
)
$foundDef = New-Object System.Collections.Generic.List[string]
function scan($dir) {
    if (-not (Test-Path $dir)) { return }
    try {
        $items = Get-ChildItem -Path $dir -ErrorAction SilentlyContinue
        foreach ($it in $items) {
            if ($it.PSIsContainer) {
                if ($it.Name -ne 'bin' -and $it.Name -ne 'obj' -and $it.Name -ne '.vs') {
                    scan $it.FullName
                }
            } else {
                $ext = $it.Extension.ToLowerInvariant()
                if ($ext -eq '.cs' -or $ext -eq '.csproj') {
                    try {
                        $txt = [System.IO.File]::ReadAllText($it.FullName)
                        if ($txt -match 'class Character' -or $txt -match 'TOR\.Character' -or $txt -match 'namespace.*TOR\b') {
                            $foundDef.Add($it.FullName + '  [' + $ext + ']')
                        }
                    } catch {}
                }
            }
        }
    } catch {}
}
foreach ($c in $candidates) { scan $c }
$lines.Add('TOR.Character / TOR namespace candidate files count=' + $foundDef.Count)
foreach ($f in $foundDef) { $lines.Add('  ' + $f) }
$lines.Add('')

# 4) grep SharpServer for 'TOR.' references to infer the TOR assembly/project
$lines.Add('=== TOR.* references in SharpServer .cs + .csproj ===')
$txtFiles = @()
try {
    $allCs = Get-ChildItem -Path 'D:\SWTORClassic\swtoremu\SharpServer' -Recurse -Filter '*.cs' -ErrorAction SilentlyContinue
    $txtFiles = $allCs.FullName
} catch {}
$torRefs = New-Object System.Collections.Generic.List[string]
foreach ($f in $txtFiles) {
    try {
        $t = [System.IO.File]::ReadAllText($f)
        if ($t -match 'TOR\.') {
            # find the matching line(s)
            $linesArr = $t -split "`r`n"
            foreach ($l in $linesArr) {
                if ($l -match 'TOR\.') {
                    $torRefs.Add($f + ': ' + $l.Trim())
                    break
                }
            }
        }
    } catch {}
}
$lines.Add('TOR.* reference lines count=' + $torRefs.Count)
foreach ($r in $torRefs) { $lines.Add('  ' + $r) }

[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
