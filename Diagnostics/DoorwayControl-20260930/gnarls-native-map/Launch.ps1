$ErrorActionPreference='Stop'
$here=$PSScriptRoot;$controlRoot=Split-Path $here -Parent
if(Test-Path (Join-Path $here 'launch-requested.txt')){throw 'This experiment has already been launched.'}
$active=@(Get-Process swtor,swtor-emu,NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
if($active.Count){throw 'Close old client and server processes before this run.'}
$inherited=@(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if($inherited.Count){throw ('Use a fresh terminal without inherited SWTOR switches: '+(($inherited.Name)-join ', '))}
foreach($row in Import-Csv (Join-Path $here 'identity.csv')){if((Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash -ne $row.SHA256){throw "Prepared input changed: $($row.Path)"}}
& (Join-Path $controlRoot 'Preserve-Logs.ps1') -Label 'pre-gnarls-native-map'
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $here 'launch-requested.txt')
$scan=Join-Path $here 'Scan-GnarlsIdentity.ps1';$capture=Join-Path $here 'capture';$marker='D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log'
$args='-NoProfile -ExecutionPolicy Bypass -File "{0}" -OutputDirectory "{1}" -MarkerLog "{2}"' -f $scan,$capture,$marker
Start-Process -FilePath "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList $args -RedirectStandardOutput (Join-Path $here 'scanner-console.log') -RedirectStandardError (Join-Path $here 'scanner-errors.log') -WindowStyle Hidden
Start-Sleep -Milliseconds 300
Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',('""{0}""' -f (Join-Path $controlRoot 'control.cmd'))) -WindowStyle Hidden
'Launched frozen control plus one-time external read-only gnarls identity scan.'
