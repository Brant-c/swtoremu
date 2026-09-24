# verify csproj now lists the 3 files + rebuild + check exe LWT
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$of = 'D:\SWTORClassic\swtoremu\_csproj_verify2.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== csproj verify + rebuild ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$txt = [System.IO.File]::ReadAllText($csproj)
$files = @('CMsgC586BD22.cs','CMsgF96DCDB0.cs','CMsg4A765897.cs')
foreach ($f in $files) {
    $lines.Add($f + ' in-csproj=' + $txt.Contains($f))
}

# rebuild
$lines.Add('')
$lines.Add('--- dotnet build ---')
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'C:\Program Files\dotnet\dotnet.exe'
$psi.Arguments = 'build "' + $csproj + '" -c Debug -f net48 --nologo'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$p = [System.Diagnostics.Process]::Start($psi)
$outAll = $p.StandardOutput.ReadToEnd()
$errAll = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$lines.Add('exit=' + $p.ExitCode)
if ($outAll) {
    $ls = $outAll -split "`r`n"
    foreach ($l in $ls) { if ($l.Trim()) { $lines.Add('  OUT: ' + $l) } }
}
if ($errAll) {
    $ls = $errAll -split "`r`n"
    foreach ($l in $ls) { if ($l.Trim()) { $lines.Add('  ERR: ' + $l) } }
}

# exe after build
$lines.Add('')
$lines.Add('--- exe after build ---')
$exe = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (Test-Path $exe) {
    $gi = Get-Item $exe
    $lines.Add('EXE LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $lines.Add('EXE len=' + $gi.Length)
    $before = [DateTime]::Parse('2026-09-18T02:33:50Z')
    $after = $gi.LastWriteTimeUtc.CompareTo($before) -gt 0
    $lines.Add('EXE newer-than-new-cs-files(02:33:50)=' + $after)
} else {
    $lines.Add('EXE MISSING')
}

[System.IO.File]::WriteAllText($of, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
