# Run with 32-bit Windows PowerShell: the emulator assembly targets x86.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$lines=Get-Content (Join-Path $root 'SharpServer\bin\Debug\NexusToR.log')
$start=-1
for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match 'Received Unknown Packet \[09AB71E5\]') { $start=$i+1 }
}
if ($start -lt 0) { throw 'Captured script-error report not found.' }
$bytes=New-Object 'System.Collections.Generic.List[byte]'
for ($i=$start; $i -lt $lines.Length -and $lines[$i] -match '^\s+[0-9A-F]{2} .*\|'; $i++) {
    foreach ($hex in ($lines[$i].Split('|')[0].Trim() -split '\s+')) {
        $bytes.Add([Convert]::ToByte($hex,16))
    }
}
$assembly=[Reflection.Assembly]::LoadFrom((Join-Path $root 'SharpServer\bin\Debug\NexusToRServer.exe'))
$type=$assembly.GetType('NexusToRServer.NET.Packets.Client.SendScriptError',$true)
function New-Packet([byte[]]$Data) {
    $packet=[Activator]::CreateInstance($type,$true)
    $packet.SetBuffers($Data)
    return $packet
}
$packet=New-Packet $bytes.ToArray()
$packet.ReadImplementation()
$flags=[Reflection.BindingFlags]'Instance,NonPublic'
if ($type.GetField('_message',$flags).GetValue($packet) -ne 'Call to function TELLCHARACTERSELECTIONINFO with mismatched arguments') { throw 'Wrong decoded message' }
if ($type.GetField('_trace',$flags).GetValue($packet) -notmatch 'line 457') { throw 'Missing call trace' }
if ($packet._stream.Position -ne $packet._stream.Length) { throw 'Unconsumed captured bytes' }
$packet.Dispose()
$empty=New-Object byte[] 32
[BitConverter]::GetBytes([uint32]0x09AB71E5).CopyTo($empty,0)
$packet=New-Packet $empty
$packet.ReadImplementation()
if ($type.GetField('_message',$flags).GetValue($packet) -ne '') { throw 'Empty text failed' }
$packet.Dispose()
$bad=$bytes.ToArray()
[BitConverter]::GetBytes([uint32]::MaxValue).CopyTo($bad,8)
$packet=New-Packet $bad
$rejected=$false
try { $packet.ReadImplementation() } catch { $rejected=$true }
$packet.Dispose()
if (!$rejected) { throw 'Oversized text was not rejected' }
'PASS: captured report, empty text, and oversized text rejection.'
