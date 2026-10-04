$log = 'C:\Users\brant\AppData\Local\Temp\_handler_fresh.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== handler fresh read ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$f = 'D:\SWTORClassic\swtoremu\SharpServer\NET\TORGamePacketHandler.cs'
$gi = Get-Item $f
$null = $lines.Add('path: ' + $f)
$null = $lines.Add('len: ' + $gi.Length)
$null = $lines.Add('LWT: ' + $gi.LastWriteTimeUtc.ToString('o'))
$null = $lines.Add('')
$null = $lines.Add('=== line count (via .NET read) ===')
$allLines = [System.IO.File]::ReadAllLines($f)
$null = $lines.Add('lineCount: ' + $allLines.Count)
$null = $lines.Add('')
$null = $lines.Add('=== search for the three opcodes + AUTHED + break placement ===')
$needleArea = 'CMsgC586BD22'
$needleF96 = 'CMsgF96DCDB0'
$needle4A = 'CMsg4A765897'
$stateAuth = 'case ClientState.AUTHED'
$found = @()
for ($i = 0; $i -lt $allLines.Count; $i++) {
    $l = $allLines[$i]
    if ($l.Contains('CMsgC586BD22') -or $l.Contains('CMsgF96DCDB0') -or $l.Contains('CMsg4A765897') -or $l.Contains('case ClientState.AUTHED') -or $l.Contains('clientState == ClientState.AUTHED')) {
        $null = $lines.Add('L' + ($i+1) + ': ' + $l)
    }
    if ($l.Contains('SourceIsAreaServer') -or $l.Contains('sourceIsAreaServer') -or $l.Contains('AREA_SERVER')) {
        $null = $lines.Add('L' + ($i+1) + ' [routing]: ' + $l)
    }
}
$null = $lines.Add('')
$null = $lines.Add('=== AreaRequestRPC / SystemRequestRPC / TOSend usage hints ===')
for ($i = 0; $i -lt $allLines.Count; $i++) {
    $l = $allLines[$i]
    if ($l.Contains('SendPacket') -or $l.Contains('AreaRequestRPC') -or $l.Contains('SystemRequestRPC') -or $l.Contains('Client.') -or $l.Contains(' TORGameClient')) {
        $null = $lines.Add('L' + ($i+1) + ': ' + $l)
    }
}
[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
