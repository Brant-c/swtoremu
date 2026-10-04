# Build the C# server with the validated dotnet command; write result to TEMP log.
$log = 'C:\Users\brant\AppData\Local\Temp\_dotnet_build_result.txt'
$csproj = 'D:\SWTORClassic\swtoremu\SharpServer\NexusToRServer.csproj'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'C:\Program Files\dotnet\dotnet.exe'
$psi.Arguments = 'build "' + $csproj + '" -c Debug -f net48 --nologo'
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$p = [System.Diagnostics.Process]::Start($psi)
$out = $p.StandardOutput.ReadToEnd()
$err = $p.StandardError.ReadToEnd()
$p.WaitForExit(120000)
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== dotnet build result ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
$null = $lines.Add('exit=' + $p.ExitCode)
if ($out) { $null = $lines.Add('--- stdout ---'); foreach ($l in $out -split "`r`n") { if ($l) { $null = $lines.Add('  ' + $l) } } }
if ($err) { $null = $lines.Add('--- stderr ---'); foreach ($l in $err -split "`r`n") { if ($l) { $null = $lines.Add('  ' + $l) } } }
$null = $lines.Add('')
$null = $lines.Add('=== bin\Debug artifacts after build ===')
$bd = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug'
if (Test-Path $bd) {
    $items = Get-ChildItem -Path $bd -ErrorAction SilentlyContinue
    $null = $lines.Add('items count=' + $items.Count)
    foreach ($w in @('NexusToRServer.exe','NexusToRServer.pdb')) {
        $f = Join-Path $bd $w
        if (Test-Path $f) {
            $gi = Get-Item $f
            $null = $lines.Add('EXISTS ' + $w + '  len=' + $gi.Length + '  LWT=' + $gi.LastWriteTimeUtc.ToString('o'))
        } else { $null = $lines.Add('MISSING ' + $w) }
    }
}
[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
