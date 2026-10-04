# dump csproj lines around the TORGameClientPacket compile entry
$cp = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$lines = [System.IO.File]::ReadAllLines($cp)
$of = 'D:\SWTORClassic\swtoremu\_csproj_section.txt'
$buf = New-Object System.Collections.Generic.List[string]
$buf.Add('=== csproj section around TORGameClientPacket.cs (L370-395) ===')
for ($i = 369; $i -le 394; $i++) {
    if ($i -ge 0 -and $i -lt $lines.Length) {
        $buf.Add('L' + ($i+1) + ': ' + $lines[$i])
    }
}
[System.IO.File]::WriteAllText($of, ($buf -join "`r`n"), [System.Text.Encoding]::UTF8)
