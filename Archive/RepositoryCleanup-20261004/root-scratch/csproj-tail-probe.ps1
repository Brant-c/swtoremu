$of = 'C:\Users\brant\AppData\Local\Temp\_csproj_tail.txt'
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$lines = [System.IO.File]::ReadAllLines($csproj)
$out = New-Object System.Collections.Generic.List[string]
$null = $out.Add('=== csproj tail lines 430..472 ===')
for ($i = 430; $i -le 472; $i++) {
    $null = $out.Add('L' + $i + ': ' + $lines[$i])
}
$null = $out.Add('')
$null = $out.Add('=== context around app.config ItemGroup ===')
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match 'app\.config' -or $lines[$i] -match '<ItemGroup />' -or $lines[$i] -match '<Import Project=' -or $lines[$i] -match '<Compile Include="NET\\\\Packets\\\\Client\\\\SelectCharacter') {
        $null = $out.Add('L' + $i + ': ' + $lines[$i])
    }
}
[System.IO.File]::WriteAllText($of, ($out -join "`r`n"), [System.Text.Encoding]::UTF8)
