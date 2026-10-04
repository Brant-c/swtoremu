param([string]$AssemblyPath = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe')
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) { throw 'Use 32-bit PowerShell.' }
$assembly = [Reflection.Assembly]::LoadFrom($AssemblyPath)
$type = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaReplicationDestroy', $true)
foreach ($handle in @([uint16]8, [uint16]19)) {
    foreach ($enabled in @($false, $true)) {
        # Captured-ID serializer control; runtime selected-ID integration is
        # checked separately by PhaseTransitionAudit/Test-SelectedPhase.ps1.
        $packet = [Activator]::CreateInstance($type, [object[]]@([uint32]0x1B502E, [uint64]0x1AC6F6DC1F, [bool]$enabled, [uint64]0x4000010E218A839C))
        $packet.ClientAreaServiceID = $handle
        $packet.InitBuffers()
        $packet.WriteImplementation()
        $bytes = $packet._stream.ToArray()
        if ([BitConverter]::ToUInt16($bytes,6) -ne $handle) { throw 'Wrong destination' }
        $expectedLength = if ($enabled) { 120 } else { 46 }
        if ($bytes.Length -ne $expectedLength) { throw "Unexpected length $($bytes.Length) expected $expectedLength" }
        $label = if ($enabled) { 'clear' } else { 'baseline' }
        [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "$label-$handle.bin"), $bytes)
    }
}
$baseline = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'baseline-8.bin'))
$hash = [Security.Cryptography.SHA256]::Create()
$actual = ([BitConverter]::ToString($hash.ComputeHash($baseline))).Replace('-','')
if ($actual -ne '2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF') { throw 'Destroy-only baseline changed' }
'PASS: default packet byte-identical; opt-in packets serialized with dynamic destinations 8/19.'
