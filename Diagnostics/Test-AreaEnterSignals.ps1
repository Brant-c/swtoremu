param(
    [string]$AssemblyPath = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\NexusToRServer.exe')
)
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) {
    throw 'Run this test with C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe (the server assembly is x86).'
}
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path $AssemblyPath).Path)

$charID = [uint64]4611687178631283611
$handle = [uint16]8

# ---- CharacterSetRendezvousPoint: (u64, u32, vec3, vec3, u8) = 37-byte body ----
$rz = $assembly.GetType('NexusToRServer.NET.Packets.Server.CharacterSetRendezvousPoint', $true)
$packet = [Activator]::CreateInstance($rz, [object[]]@(
    $charID, [uint32]1,
    [single]-64.8741, [single]-6.906221, [single]-127.670998,
    [single]0.0, [single]-90.000198, [single]0.0,
    [byte]1))
$packet.ClientAreaServiceID = $handle
$packet.SetModule([byte]8)
$packet.Encrypted = $false
$packet.InitBuffers()
$packet.WriteImplementation()
$plain = $packet._stream.ToArray()

# header: type(4) + routing(4); body: 8 + 4 + 12 + 12 + 1
if ($plain.Length -ne 45) { throw ("Rendezvous plaintext length {0} != 45" -f $plain.Length) }
if ([BitConverter]::ToUInt32($plain, 0) -ne 0x2B4792AE) { throw 'Rendezvous type mismatch' }
if ([BitConverter]::ToUInt16($plain, 4) -ne 0x65B3 -or [BitConverter]::ToUInt16($plain, 6) -ne $handle) { throw 'Rendezvous routing mismatch' }
if ([BitConverter]::ToUInt64($plain, 8) -ne $charID) { throw 'Rendezvous charId mismatch' }
if ([BitConverter]::ToUInt32($plain, 16) -ne 1) { throw 'Rendezvous u32 mismatch' }
foreach ($spec in @(@(20, -64.8741), @(24, -6.906221), @(28, -127.670998), @(32, 0.0), @(36, -90.000198), @(40, 0.0))) {
    $got = [BitConverter]::ToSingle($plain, $spec[0])
    if ([Math]::Abs($got - [single]$spec[1]) -gt 0.001) { throw ("Rendezvous float@{0} = {1}" -f $spec[0], $got) }
}
if ($plain[44] -ne 1) { throw 'Rendezvous flag mismatch' }
$packet._stream.Dispose()
'PASS: CharacterSetRendezvousPoint body = u64 + u32 + vec3 + vec3 + u8 (37 bytes), area routing ok.'

# ---- CharacterChangeState: (u64, string) ----
$cs = $assembly.GetType('NexusToRServer.NET.Packets.Server.CharacterChangeState', $true)
$packet2 = [Activator]::CreateInstance($cs, [object[]]@($charID, ''))
$packet2.ClientAreaServiceID = $handle
$packet2.SetModule([byte]8)
$packet2.Encrypted = $false
$packet2.InitBuffers()
$packet2.WriteImplementation()
$plain2 = $packet2._stream.ToArray()
$ty = [BitConverter]::ToUInt32($plain2, 0)
if ($ty -ne [uint32]2917858467) { throw ("ChangeState type mismatch: {0}" -f $ty) } # 0xADEAFCA3
if ([BitConverter]::ToUInt16($plain2, 4) -ne 0x65B3 -or [BitConverter]::ToUInt16($plain2, 6) -ne $handle) { throw 'ChangeState routing mismatch' }
if ([BitConverter]::ToUInt64($plain2, 8) -ne $charID) { throw 'ChangeState charId mismatch' }
# trailing bytes: WriteString(s, hasTerminator=true) emits Int32(len+1) + bytes + 0x00;
# for "" that is 01-00-00-00-00 (5 bytes) — the same encoding TravelPending uses.
if ($plain2.Length -ne 21) { throw ("ChangeState length {0} != 21" -f $plain2.Length) }
$tail = ($plain2[16..20] | ForEach-Object { $_.ToString('X2') }) -join ' '
if ($tail -ne '01 00 00 00 00') { throw "ChangeState tail mismatch: $tail" }
$packet2._stream.Dispose()
'PASS: CharacterChangeState body = u64 + empty string (13 bytes), area routing ok.'

# ---- AreaEnterSignals entry point ----
$sig = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaEnterSignals', $true)
$fire = $sig.GetMethod('Fire', [Reflection.BindingFlags]'Static,Public')
if ($null -eq $fire) { throw 'AreaEnterSignals.Fire entry point not found.' }
if ($fire.GetParameters().Count -ne 1) { throw 'AreaEnterSignals.Fire should take one client argument.' }
'PASS: AreaEnterSignals.Fire entry point is present; packet shapes verified above.'
