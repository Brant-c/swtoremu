# dump exact csproj lines around the client packet compiles (L378-395) to a file for precise anchor
$cp = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$lines = [System.IO.File]::ReadAllLines($cp)
$of = 'D:\SWTORClassic\swtoremu\_csproj_anchor.txt'
$buf = New-Object System.Collections.Generic.List[string]
for ($i = 377; $i -le 395; $i++) {
    $buf.Add('L' + ($i+1) + ': ' + $lines[$i])
}
[System.IO.File]::WriteAllText($of, ($buf -join "`r`n"), [System.Text.Encoding]::UTF8)
