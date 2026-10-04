# locate IPacket and dump TORGameClientPacket + any SetBuffers/Data field
$out = 'D:\SWTORClassic\swtoremu\_packet_contract.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== locate IPacket / SPacket / TORGameClientPacket ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$lines.Add('')

# enumerate candidate files
$cand = @(
    'D:\SWTORClassic\swtoremu\SharpServer\NET\IPacket.cs',
    'D:\SWTORClassic\swtoremu\SharpServer\NET\Packet.cs',
    'D:\SWTORClassic\swtoremu\SharpServer\NET\Packet\IPacket.cs',
    'D:\SWTORClassic\swtoremu\SharpServer\NET\Packet\Packet.cs',
    'D:\SWTORClassic\swtoremu\SharpServer\NET\TorGameClientPacket.cs',
    'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGameClientPacket.cs'
)
foreach ($fp in $cand) {
    $lines.Add('--- ' + $fp + ' ---')
    if (Test-Path $fp) {
        $lines.Add('  EXISTS len=' + (Get-Item $fp).Length + ' LWT=' + (Get-Item $fp).LastWriteTimeUtc.ToString('o'))
        $txt = [System.IO.File]::ReadAllText($fp)
        $lines.Add('  CONTENT:')
        foreach ($l in $txt -split "`r`n") { $lines.Add('    ' + $l) }
    } else {
        $lines.Add('  MISSING')
    }
    $lines.Add('')
}

# search for 'Data' field / SetBuffers in NexusToRServer source
$lines.Add('=== grep Data / SetBuffers / GetClient in SharpServer ===')
$srcRoot = 'D:\SWTORClassic\swtoremu\SharpServer'
$hits = New-Object System.Collections.Generic.List[string]
function scan($dir) {
    if (-not (Test-Path $dir)) { return }
    try {
        $items = Get-ChildItem -Path $dir -ErrorAction SilentlyContinue
        foreach ($it in $items) {
            if ($it.PSIsContainer) {
                if ($it.Name -ne 'bin' -and $it.Name -ne 'obj') { scan $it.FullName }
            } else {
                if ($it.Name -like '*.cs') {
                    $t = [System.IO.File]::ReadAllText($it.FullName)
                    foreach ($kw in @('Data\s*\{get', 'string Data', 'byte\[\] Data', 'SetBuffers', 'GetClient\(\)', 'readonly.*Data', 'private.*Data', 'public.*Data')) {
                        if ($t -match $kw) {
                            $hits.Add($it.FullName + '  [' + $kw + ']')
                            break
                        }
                    }
                }
            }
        }
    } catch {}
}
scan $srcRoot
$lines.Add('[hits count=' + $hits.Count + ']')
foreach ($h in $hits) { $lines.Add('  ' + $h) }

[System.IO.File]::WriteAllText($out, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
