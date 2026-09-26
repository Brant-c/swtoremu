param(
    [string]$AssemblyPath = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\NexusToRServer.exe'),
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug')
)
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) {
    throw 'Run with 32-bit PowerShell because the server assembly is x86.'
}
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path $AssemblyPath).Path)
$oldDirectory = [Environment]::CurrentDirectory
$captured = [uint64]0x4000010E218A839C
$selected = [uint64]0x4000010E218A839B

function Packed([uint64]$value) {
    [byte[]]$bytes = New-Object byte[] 9
    $bytes[0] = 0xCF
    foreach ($i in 0..7) { $bytes[$i + 1] = [byte](($value -shr (56 - 8 * $i)) -band 0xFF) }
    return $bytes
}
function Count-Pattern([byte[]]$data, [byte[]]$pattern) {
    $count = 0
    for ($i = 0; $i -le $data.Length - $pattern.Length; $i++) {
        $match = $true
        for ($j = 0; $j -lt $pattern.Length; $j++) {
            if ($data[$i + $j] -ne $pattern[$j]) { $match = $false; break }
        }
        if ($match) { $count++; $i += $pattern.Length - 1 }
    }
    return $count
}
function Packet-Bytes($packet) {
    $packet.ClientAreaServiceID = [uint16]8
    $packet.SetModule([byte]8)
    $packet.Encrypted = $false
    $packet.InitBuffers()
    $packet.WriteImplementation()
    try { return $packet._stream.ToArray() } finally { $packet._stream.Dispose() }
}

try {
    [Environment]::CurrentDirectory = (Resolve-Path $DataDirectory).Path
    $crtType = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaClientReplicationTransaction', $true)
    $crt = [Activator]::CreateInstance($crtType, [object[]]@('tython_blockout','4611686019869492753','1',2,$selected))
    [byte[]]$crtBytes = Packet-Bytes $crt
    if ((Count-Pattern $crtBytes (Packed $captured)) -ne 0) { throw 'CRT2 still contains captured character id.' }
    if ((Count-Pattern $crtBytes (Packed $selected)) -ne 25) { throw 'CRT2 did not remap all 25 character references.' }

    $effectType = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaEffEventMessage', $true)
    $effect = [Activator]::CreateInstance($effectType, [object[]]@('tython_blockout','4611686019869492753','1',1,$selected))
    [byte[]]$effectBytes = Packet-Bytes $effect
    if ((Count-Pattern $effectBytes ([BitConverter]::GetBytes($captured))) -ne 0) { throw 'Effect1 still contains captured character id.' }
    if ((Count-Pattern $effectBytes ([BitConverter]::GetBytes($selected))) -ne 2) { throw 'Effect1 did not remap both character references.' }

    $batchType = $assembly.GetType('NexusToRServer.NET.Packets.Server.SMsg23B61238', $true)
    [byte[]]$blob = (Packed $captured) + (Packed $captured) + (Packed $captured)
    $batch = [Activator]::CreateInstance($batchType, [object[]]@([uint32]1,$blob,$selected))
    [byte[]]$batchBytes = Packet-Bytes $batch
    if ((Count-Pattern $batchBytes (Packed $captured)) -ne 0) { throw 'On Enter batch still contains captured character id.' }
    if ((Count-Pattern $batchBytes (Packed $selected)) -ne 3) { throw 'On Enter batch did not remap all character references.' }
    'PASS: CRT2 (25), effect1 (2), and On Enter (3) captured-character references remapped to the selected character.'
}
finally { [Environment]::CurrentDirectory = $oldDirectory }
