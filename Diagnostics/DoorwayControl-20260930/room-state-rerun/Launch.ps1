$ErrorActionPreference = 'Stop'
$here=$PSScriptRoot
$controlRoot=Split-Path $here -Parent
if (Test-Path (Join-Path $here 'launch-requested.txt')) { throw 'This experiment has already been launched.' }
$active=@(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if($active.Count){throw 'Close old client and server processes before this rerun.'}
$inherited=@(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if($inherited.Count){throw ('Use a fresh terminal without inherited SWTOR switches: '+(($inherited.Name)-join ', '))}
foreach($row in Import-Csv (Join-Path $here 'identity.csv')) {
    if((Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash -ne $row.SHA256){throw "Prepared input changed: $($row.Path)"}
}
& (Join-Path $controlRoot 'Preserve-Logs.ps1') -Label 'pre-room-state-rerun'
Get-Date -Format o | Set-Content (Join-Path $here 'launch-requested.txt')
$watcher=Join-Path $here 'Watch-RoomState.ps1'
$timeline=Join-Path $here 'timeline.csv'
$watchLog=Join-Path $here 'watcher-console.log'
$watchArgs='-NoProfile -ExecutionPolicy Bypass -File "{0}" -OutputCsv "{1}"' -f $watcher,$timeline
Start-Process -FilePath "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList $watchArgs -RedirectStandardOutput $watchLog -RedirectStandardError (Join-Path $here 'watcher-errors.log') -WindowStyle Hidden
Start-Sleep -Milliseconds 300
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f (Join-Path $controlRoot 'control.cmd'))) -WindowStyle Hidden
'Launched unchanged doorway control plus external read-only room-state observer.'
