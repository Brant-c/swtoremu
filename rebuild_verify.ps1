$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$of = 'D:\SWTORClassic\swtoremu\_build_verify.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('=== rebuild verify (no client launch) ===')
$lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
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
$lines.Add('dotnet-build exit=' + $p.ExitCode)
$lines.Add('')
$lines.Add('--- stdout (errors/warnings only) ---')
if ($outAll) {
    $ls = $outAll -split "`r`n"
    foreach ($l in $ls) {
        if ($l -match 'Error|error|Warning|warning|Build succeeded|Time Elapsed|NexusToRServer ->') {
            $lines.Add('  ' + $l)
        }
    }
    $lines.Add('  [full line count=' + $ls.Count + ']')
}
if ($errAll) {
    $lines.Add('')
    $lines.Add('--- stderr ---')
    $els = $errAll -split "`r`n"
    foreach ($l in $els) { if ($l.Trim()) { $lines.Add('  ERR: ' + $l) } }
}
$lines.Add('')
$lines.Add('--- exe after build ---')
$exe = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe'
if (Test-Path $exe) {
    $gi = Get-Item $exe
    $lines.Add('EXE LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
    $lines.Add('EXE len=' + $gi.Length)
    $csCutoff = [DateTime]::Parse('2026-09-18T03:35:00Z')
    $lines.Add('EXE newer-than-edits(03:35)=' + ($gi.LastWriteTimeUtc.CompareTo($csCutoff) -gt 0))
} else {
    $lines.Add('EXE MISSING')
}
$lines.Add('')
$lines.Add('[end] ' + [DateTimeOffset]::UtcNow.ToString('o'))
[System.IO.File]::WriteAllText($of, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
