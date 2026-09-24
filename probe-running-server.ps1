# focused: identify the running NexusToRServer + CRT3 .disabled verify
$log = 'C:\Users\brant\AppData\Local\Temp\_running_server.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== running server identification ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))
try {
    $procs = Get-Process -Name 'NexusToRServer' -ErrorAction SilentlyContinue
    $null = $lines.Add('NexusToRServer count=' + $procs.Count)
    if ($procs) {
        foreach ($p in $procs) {
            $null = $lines.Add('  PID=' + $p.Id)
            $null = $lines.Add('  StartTime=' + $p.StartTime.ToString('o'))
            $null = $lines.Add('  CPU(s)=' + $p.TotalProcessorTime.ToString())
            $null = $lines.Add('  MainWindowTitle=' + $p.MainWindowTitle)
            $null = $lines.Add('  Responding=' + $p.Responding)
            $null = $lines.Add('  MachineName=' + $p.MachineName)
            $null = $lines.Add('  Path=' + $p.Path)
            # command line via WMI/CIM if available
            try {
                $wmi = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $p.Id) -ErrorAction SilentlyContinue
                if ($wmi) {
                    $null = $lines.Add('  CommandLine=' + $wmi.CommandLine)
                }
            } catch {
                $null = $lines.Add('  [WMI query failed: ' + $_.Exception.Message + ']')
            }
        }
    }
} catch {
    $null = $lines.Add('[FAIL] Get-Process: ' + $_.Exception.Message)
}

$null = $lines.Add('')
$null = $lines.Add('=== CRT3 .disabled verify ===')
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt.disabled'
if (Test-Path $f) {
    $gi = Get-Item $f
    $len = $gi.Length
    $lwt = $gi.LastWriteTimeUtc.ToString('o')
    $b = [System.IO.File]::ReadAllBytes($f)
    $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($b)).Replace('-','').ToLowerInvariant()
    $null = $lines.Add('disabled-exists=True')
    $null = $lines.Add('len=' + $len)
    $null = $lines.Add('sha=' + $sha)
    $null = $lines.Add('tail=0x' + $b[-1].ToString('X2'))
    $null = $lines.Add('head32=0x' + [BitConverter]::ToUInt32($b,0).ToString('X8'))
    $null = $lines.Add('file-LWT=' + $lwt)
} else {
    $null = $lines.Add('disabled-exists=False (PROBLEM)')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
