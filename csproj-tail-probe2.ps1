$of = 'D:\SWTORClassic\swtoremu\_csproj_tail.txt'
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$lines = [System.IO.File]::ReadAllLines($csproj)
$out = New-Object System.Collections.Generic.List[string]
$null = $out.Add('=== csproj tail lines 425..472 ===')
for ($i = 425; $i -le 472; $i++) {
    if ($i -lt $lines.Length) { $null = $out.Add('L' + $i + ': ' + $lines[$i]) }
}
$null = $out.Add('')
$null = $out.Add('=== client CMsg Compile includes context ===')
for ($i = 0; $i -lt $lines.Length; $i++) {
    $l = $lines[$i]
    if ($l -match 'app\.config' -or $l -match '<ItemGroup />' -or $l -match '<Import Project=' -or $l -match 'SelectCharacterRequest' -or $l -match 'CMsg7CB9A193' -or $l -match 'CMsgC26464A9') {
        $null = $out.Add('L' + $i + ': ' + $l)
    }
}
$null = $out.Add('')
$null = $out.Add('=== csproj total line count ===')
$null = $out.Add($lines.Length)
[System.IO.File]::WriteAllText($of, ($out -join "`r`n"), [System.Text.Encoding]::UTF8)
