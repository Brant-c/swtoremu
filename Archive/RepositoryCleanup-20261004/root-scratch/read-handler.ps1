$log = 'C:\Users\brant\AppData\Local\Temp\_handler_read.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== TORGamePacketHandler.cs: AUTHED/CMsg/default lines ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$path = 'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGamePacketHandler.cs'
$fi = Get-Item $path
$null = $lines.Add('file LWT: ' + $fi.LastWriteTimeUtc.ToString('o'))
$null = $lines.Add('file len: ' + $fi.Length)
$txt = [System.IO.File]::ReadAllText($path)
$allLines = $txt -split "`r`n"
$idx = 0
foreach ($ln in $allLines) {
    $idx = $idx + 1
    $lower = $ln.ToLowerInvariant()
    if ($lower -match 'auth' -or $lower -match 'cmsgc586bd22' -or $lower -match 'cmsgf96dcdb0' -or $lower -match 'cmsg4a765897' -or $lower -match 'unknownpackettrace' -or $lower -match 'default:' -or $lower -match 'case clientstate') {
        $null = $lines.Add('L' + $idx + ': ' + $ln)
    }
}
[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
