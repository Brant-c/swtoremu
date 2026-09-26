param(
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug'),
    [string]$AssemblyPath = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\NexusToRServer.exe')
)
$ErrorActionPreference = 'Stop'

$hookSourcePath = Join-Path $PSScriptRoot '..\Client\Hook\Src\ToR.cpp'
$hookSource = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $hookSourcePath))
foreach ($requiredPlayerFieldId in @(
    '0x4000000365D249CBULL', '0x400000045A767612ULL',
    '0x40000000009654C3ULL', '0x40000000009C971FULL',
    '0x400000077CDF593BULL',
    '0x4000000886E130D2ULL', '0x4000000D5DF53477ULL')) {
    if ($hookSource.IndexOf($requiredPlayerFieldId, [StringComparison]::Ordinal) -lt 0) {
        throw "Player-field observer is missing $requiredPlayerFieldId."
    }
}
if ($hookSource.IndexOf('0x004F5A00 - 0x00400000',
        [StringComparison]::Ordinal) -lt 0 -or
    $hookSource.IndexOf('HeroClassGetField_Hook',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Observation-only HeroClass::getField hook is missing.'
}
if ($hookSource.IndexOf('0x005D9FF0 - 0x00400000',
        [StringComparison]::Ordinal) -lt 0 -or
    $hookSource.IndexOf('SetNodeFieldEnum_Hook',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Observation-only HM.SetNodeFieldEnum hook is missing.'
}
$traceLauncherPath = Join-Path $PSScriptRoot '..\Run-SWTORClassic-Trace-Tython.cmd'
$traceLauncher = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $traceLauncherPath))
$compatibilityLauncherPath = Join-Path $PSScriptRoot 'CompatibilityLauncher.cpp'
$compatibilityLauncher = [IO.File]::ReadAllText(
    (Resolve-Path -LiteralPath $compatibilityLauncherPath))
if ($compatibilityLauncher.IndexOf('getenv("SWTOR_TRACE_REPLICATION_CREATE") != NULL;',
        [StringComparison]::Ordinal) -lt 0 -or
    $compatibilityLauncher.IndexOf('WorldFadeInGateWatch: marker=',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Opt-in RequestWorldFadeIn gate observer is missing.'
}
if ($compatibilityLauncher.IndexOf('page.State == MEM_COMMIT &&',
        [StringComparison]::Ordinal) -lt 0 -or
    $compatibilityLauncher.IndexOf('const DWORD offsets[] = {0x11E, 0x15C};',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Readable-page scan or verified RequestWorldFadeIn offsets are missing.'
}
if ($compatibilityLauncher.IndexOf('0x127A, 0x12D2, 0x130A',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Byte-exact B0/B2/B4 Replication_Create offsets are missing.'
}
if ($compatibilityLauncher.IndexOf('0x13C1, 0x13F7, 0x1497',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Byte-exact B7/B8/B9 Replication_Create offsets are missing.'
}
if ($compatibilityLauncher.IndexOf('installLoadingContinueFallback',
        [StringComparison]::Ordinal) -lt 0 -or
    $compatibilityLauncher.IndexOf('0xE9,0x56,0x00,0x00,0x00,0x90',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Local PhaseNeedsContinue(false) compatibility fallback is missing.'
}
if ($traceLauncher.IndexOf('set SWTOR_TRACE_PLAYER_FIELDS=',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Tython compatibility run does not disable the player-field observer.'
}
if ($traceLauncher.IndexOf('set SWTOR_TRACE_PLAYER_LOADED_ACCESS=',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Tython compatibility run does not disable the player-loaded data breakpoint.'
}
if ($traceLauncher.IndexOf('set SWTOR_TRACE_REPLICATION_CREATE=',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Tython compatibility run does not disable Replication_Create milestones.'
}

$traceAnalyzerPath = Join-Path $PSScriptRoot 'Analyze-TythonTrace.ps1'
$traceAnalyzer = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $traceAnalyzerPath))
if ($traceAnalyzer.IndexOf('Observed player-field reads:',
        [StringComparison]::Ordinal) -lt 0 -or
    $traceAnalyzer.IndexOf('PlayerFieldHook',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Tython trace analyzer does not summarize the player-field observer.'
}

# The September 18 ObjectReply -> AreaStartupBundle refactor promised to keep
# the captured packet order. Guard the ordering-sensitive prefix explicitly;
# packet-shape tests alone cannot detect a call moved later in the bundle.
$bundlePath = Join-Path $PSScriptRoot '..\SharpServer\NET\Packets\Server\AreaStartupBundle.cs'
$bundleSource = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $bundlePath))
if ($bundleSource.IndexOf('SWTOR_ENABLE_UNVERIFIED_CRT3',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Known-incomplete CRT3 is no longer guarded behind its diagnostic opt-in.'
}
if ($bundleSource.IndexOf('SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT',
        [StringComparison]::Ordinal) -lt 0 -or
    $bundleSource.IndexOf('new AreaEffEventMessage(area, areaID, areaCode, 1, characterID)',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Safe Login Immunity effect 1 is not guarded by its compatibility opt-out.'
}
$traceLauncherPath = Join-Path $PSScriptRoot '..\Run-SWTORClassic-Trace-Tython.cmd'
$traceLauncher = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $traceLauncherPath))
if ($traceLauncher.IndexOf('set SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT=1',
        [StringComparison]::Ordinal) -lt 0) {
    throw 'Tython compatibility run does not suppress the identified Safe Login Immunity effect.'
}
$orderedMarkers = @(
    'new AreaClientReplicationTransaction(area, areaID, areaCode, 1, characterID)',
    '0xCF, 0x75, 0xDC, 0xE5',
    '0xCF, 0x65, 0xF1, 0x36',
    '0xC7, 0x4F, 0x77, 0x41',
    'new AreaTalk("logon"',
    'new AreaClientReplicationTransaction(area, areaID, areaCode, 2, characterID)'
)
$previousMarker = -1
foreach ($markerText in $orderedMarkers) {
    $markerIndex = $bundleSource.IndexOf($markerText, $previousMarker + 1,
        [StringComparison]::Ordinal)
    if ($markerIndex -lt 0) {
        throw "Area startup ordering marker missing or out of order: $markerText"
    }
    $previousMarker = $markerIndex
}
if (($bundleSource.Split(@('0xCF, 0x65, 0xF1, 0x36'),
        [StringSplitOptions]::None).Count - 1) -ne 1) {
    throw 'The CF 65 F1 36 startup RPC must occur exactly once.'
}

function Find-Pattern([byte[]]$Data, [byte[]]$Pattern) {
    $hits = @()
    for ($i = 0; $i -le $Data.Length - $Pattern.Length; $i++) {
        $match = $true
        for ($j = 0; $j -lt $Pattern.Length; $j++) {
            if ($Data[$i + $j] -ne $Pattern[$j]) { $match = $false; break }
        }
        if ($match) { $hits += $i; $i += $Pattern.Length - 1 }
    }
    return @($hits)
}

function Packed-U64([uint64]$Value) {
    [byte[]]$result = New-Object byte[] 9
    $result[0] = 0xCF
    foreach ($i in 0..7) {
        $result[$i + 1] = [byte](($Value -shr (56 - 8 * $i)) -band 0xFF)
    }
    return $result
}

$crtDirectory = Join-Path (Resolve-Path $DataDirectory).Path 'AreaServer\CRT'
$fixtures = @{}
$previousStream = 0
foreach ($id in 1..17) {
    $path = Join-Path $crtDirectory ("tython_blockout-4611686019869492753-1.$id.acrt")
    if (!(Test-Path -LiteralPath $path)) { throw "Missing CRT$id fixture: $path" }
    [byte[]]$bytes = [IO.File]::ReadAllBytes($path)
    if ($bytes.Length -lt 12) { throw "CRT$id is too short: $($bytes.Length) bytes" }
    [uint32]$stream = [BitConverter]::ToUInt32($bytes, 0)
    if ($stream -le $previousStream) {
        throw ('CRT stream order is not increasing at CRT{0}: 0x{1:X8} after 0x{2:X8}' -f $id,$stream,$previousStream)
    }
    $previousStream = $stream
    $fixtures[$id] = $bytes
}

[byte[]]$crt2 = $fixtures[2]
[byte[]]$crt3 = $fixtures[3]
if ([BitConverter]::ToUInt32($crt3, 0) -ne 0x001B5014) { throw 'CRT3 has the wrong stream id.' }
if ($crt3.Length -ne 55) { throw "CRT3 has unexpected length $($crt3.Length), expected 55." }
if ($crt3[27] -ne 5 -or $crt3[28] -ne 7 -or $crt3[29] -ne 25) {
    throw 'CRT3 style-7 field header is not 05 07 19.'
}
if ($crt3.Length -ne 30 + $crt3[29]) { throw 'CRT3 declared payload length does not consume the complete fixture.' }
if ($crt3[-1] -ne 0) { throw ('CRT3 terminal state byte is 0x{0:X2}; the guarded fixture uses 0x00.' -f $crt3[-1]) }
if ($crt3[30] -ne 1) { throw 'CRT3 no longer declares the known-incompatible compact structure 1.' }

$phaseClass = Packed-U64 0x40000012338B5ACB
$capturedPlayer = Packed-U64 0x4000010E218A839C
$phaseHits = Find-Pattern $crt3 $phaseClass
$playerHits = Find-Pattern $crt3 $capturedPlayer
if ($phaseHits.Count -ne 1) { throw "CRT3 should contain one phsPlayerPhaseData class id; found $($phaseHits.Count)." }
if ($playerHits.Count -ne 1) { throw "CRT3 should contain one captured-player reference; found $($playerHits.Count)." }

# The first CF-packed id inside the 25-byte class value is the active phase.
# It must already have been created by CRT2, which precedes this phase update.
$payloadOffset = 30
$activeMarker = $crt3[$payloadOffset..($payloadOffset + 14)]
$marker = Find-Pattern $activeMarker ([byte[]]@(0xCF))
if ($marker.Count -lt 1) { throw 'CRT3 phase payload has no CF-packed active-phase reference.' }
$activeOffset = $payloadOffset + $marker[0]
[byte[]]$activePhase = $crt3[$activeOffset..($activeOffset + 8)]
$activeInCrt2 = Find-Pattern $crt2 $activePhase
if ($activeInCrt2.Count -lt 1) {
    throw 'CRT3 active-phase node does not appear in preceding CRT2.'
}

$namesPath = Join-Path $PSScriptRoot '..\Tools\tor_tools\gom_type_names.xml'
[xml]$names = Get-Content -LiteralPath $namesPath
$requiredSchema = @{
    '4611686096601569995' = 'phsPlayerPhaseData'
    '4611686083936082392' = 'phsActivePhases'
    '4611686124569125042' = 'phsInstanceAllowAll'
    '4611686245827200000' = 'phsOwnerOfShipToBeBoarded'
    '4611686095692169993' = 'phsUniqueActivePhase'
    '4611686084029482399' = 'phsAuthorityID'
}
foreach ($entry in $requiredSchema.GetEnumerator()) {
    $node = $names.gom_types.gom_type | Where-Object { $_.id -eq $entry.Key }
    if ($null -eq $node -or $node.name -ne $entry.Value) {
        throw "April GOM name mapping is missing $($entry.Value) ($($entry.Key))."
    }
}

$x86PowerShell = "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
if (!(Test-Path -LiteralPath $x86PowerShell)) { throw '32-bit PowerShell is required for server assembly tests.' }
$childArgs = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass')

& $x86PowerShell @childArgs -File (Join-Path $PSScriptRoot 'Test-CapturedCharacterRemap.ps1') -AssemblyPath $AssemblyPath -DataDirectory $DataDirectory
if ($LASTEXITCODE -ne 0) { throw 'Captured-character remap test failed.' }
& $x86PowerShell @childArgs -File (Join-Path $PSScriptRoot 'Test-AreaWireRoundTrip.ps1') -DataDirectory $DataDirectory
if ($LASTEXITCODE -ne 0) { throw 'Area wire round-trip test failed.' }
& $x86PowerShell @childArgs -File (Join-Path $PSScriptRoot 'Test-AreaEnterSignals.ps1') -AssemblyPath $AssemblyPath
if ($LASTEXITCODE -ne 0) { throw 'Area enter-signal packet test failed.' }

$activeValue = [uint64]0
foreach ($i in 1..8) { $activeValue = ($activeValue -shl 8) -bor $activePhase[$i] }
'PASS: offline world-entry gate.'
('  Captured startup prefix order is preserved through CRT2.')
('  CRT1..17 streams are ordered; CRT3=0x001B5014, style=7, payload=25 bytes.')
('  CRT3 phsPlayerPhaseData points at active phase 0x{0:X16}, present in preceding CRT2 ({1} references).' -f $activeValue,$activeInCrt2.Count)
('  April GOM identifies all five phase fields, but CRT3 declares compact structure 1 while this CRT1 assigns structure 1 to utlTrainerList.')
('  The known-incompatible CRT3 remains diagnostic-only; character remap, 54 packet wire round trips, and both final enter-signal packet shapes pass.')
'Scope: this rejects accidental emission or false validation of CRT3; it does not supply a matching phase schema.'
