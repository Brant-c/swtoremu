param(
    [string]$AssemblyPath = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\NexusToRServer.exe')
)
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) {
    throw 'Run this test with C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe (the server assembly is x86).'
}
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path $AssemblyPath).Path)

$opcode = [uint32]::Parse('D5280283', [Globalization.NumberStyles]::HexNumber)
$t = $assembly.GetType('NexusToRServer.NET.Packets.Server.SMsgResults', $true)
$p = [Activator]::CreateInstance($t, [object[]]@('true', 'true', [uint16]0x65A7, [uint16]0))
$p.SetModule([byte]8)
$p.Encrypted = $false
$p.InitBuffers()
$p.WriteImplementation()
$plain = $p._stream.ToArray()
$p._stream.Dispose()

$hex = ($plain | ForEach-Object { $_.ToString('X2') }) -join ' '
"PLAIN ($($plain.Length) bytes): $hex"
if ([BitConverter]::ToUInt32($plain, 0) -ne $opcode) { throw 'SMsgResults type mismatch' }
if ([BitConverter]::ToUInt16($plain, 4) -ne 0x65A7 -or [BitConverter]::ToUInt16($plain, 6) -ne 0) { throw 'SMsgResults routing mismatch' }
# string 1: Int32(5) + "true" (74 72 75 65) + 00 ; string 2 same
$expect = [byte[]]@(0x05,0,0,0, 0x74,0x72,0x75,0x65, 0x00, 0x05,0,0,0, 0x74,0x72,0x75,0x65, 0x00)
for ($i = 0; $i -lt $expect.Length; $i++) {
    if ($plain[8 + $i] -ne $expect[$i]) { throw "body byte $i = $($plain[8+$i]) expected $($expect[$i])" }
}
if ($plain.Length -ne 8 + $expect.Length) { throw "length $($plain.Length) != $((8 + $expect.Length))" }
'PASS: SMsgResults 0xD5280283 = (string, string) on OmegaClientObject routing 0x65A7->0x0000.'

# empty strings variant (env default could be changed later)
$p2 = [Activator]::CreateInstance($t, [object[]]@('', '', [uint16]0x65A7, [uint16]0))
$p2.SetModule([byte]8)
$p2.Encrypted = $false
$p2.InitBuffers()
$p2.WriteImplementation()
$plain2 = $p2._stream.ToArray()
$p2._stream.Dispose()
if ([BitConverter]::ToUInt32($plain2, 0) -ne $opcode) { throw 'variant type mismatch' }
if ([BitConverter]::ToUInt16($plain2, 4) -ne 0x65A7 -or [BitConverter]::ToUInt16($plain2, 6) -ne 0) { throw 'variant routing mismatch' }
'PASS: SMsgResults OmegaClientObject routing and empty-string variant.'
