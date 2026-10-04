param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$components = @(
    @{Name='ShardListServer';Directory='SharpServer/ShardListServer/bin/Debug'},
    @{Name='NexusToRServer';Directory='SharpServer/bin/Debug'}
)
foreach ($component in $components) {
    $exe = Join-Path $root ($component.Directory + '/' + $component.Name + '.exe')
    if (!(Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Build required; missing $exe" }
}
if (!(Test-Path -LiteralPath (Join-Path $root 'SharpServer/ShardListServer/bin/Debug/Shards.xml'))) { throw 'Shards.xml is missing; run Build-Server.ps1.' }
foreach ($fixture in @(@{Folder='CRT';Count=17;Extension='acrt'},@{Folder='Awareness';Count=2;Extension='aaw'},@{Folder='EffectEvent';Count=8;Extension='aeff'})) {
    foreach ($id in 1..$fixture.Count) {
        $p = Join-Path $root ('SharpServer/bin/Debug/AreaServer/{0}/tython_blockout-4611686019869492753-1.{1}.{2}' -f $fixture.Folder,$id,$fixture.Extension)
        if (!(Test-Path -LiteralPath $p -PathType Leaf)) { throw "Required captured input missing: $p" }
    }
}
$active = @(Get-Process NexusToRServer,ShardListServer -ErrorAction SilentlyContinue)
$switches = @(Get-ChildItem Env: | Where-Object Name -Like 'SWTOR_*')
if ($CheckOnly) {
    Write-Output "Inputs present; active server processes=$($active.Count); inherited SWTOR switches=$($switches.Count). No processes launched."
    Write-Output 'This preflight does not verify binding, TLS/client acceptance, asset completeness or gameplay.'
    return
}
if ($active.Count) { throw 'Server process already running; inspect it before starting a second copy.' }
if ($switches.Count) { throw 'Use a fresh terminal without SWTOR_* experiment switches for server-only startup.' }
$occupied = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -In @(443,8888,7979,20060,20066))
if ($occupied.Count) { throw ('Required ports already occupied: ' + (($occupied.LocalPort | Sort-Object -Unique) -join ', ')) }
& (Join-Path $PSScriptRoot 'Collect-Logs.ps1')
$session = Join-Path $root ('RuntimeLogs/server-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $session | Out-Null
foreach ($component in $components) {
    $directory = Join-Path $root $component.Directory
    $process = Start-Process -FilePath (Join-Path $directory ($component.Name + '.exe')) -WorkingDirectory $directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $session ($component.Name + '.stdout.log')) -RedirectStandardError (Join-Path $session ($component.Name + '.stderr.log'))
    Write-Output "$($component.Name) started: PID=$($process.Id)"
}
Write-Output "Server consoles: $session"
Write-Output 'Client experiments require their own reviewed launcher; these servers have no experiment settings.'
