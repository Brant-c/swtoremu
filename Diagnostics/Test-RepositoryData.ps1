param([string]$AssemblyPath)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$AssemblyPath){$AssemblyPath=Join-Path $root 'SharpServer\bin\Debug\NexusToRServer.exe'}
$a=[Reflection.Assembly]::LoadFrom($AssemblyPath)
$t=$a.GetType('NexusToRServer.NET.Packets.Server.RepositoryDataNotFound',$true)
$r=[Activator]::CreateInstance($t,[object[]]@([uint32]0x65A80002,[uint32]37,'/missing'))
$r.InitBuffers(); $r.WriteImplementation()
$b=New-Object IO.BinaryReader (New-Object IO.MemoryStream (,$r._stream.ToArray()))
function Read-Text { $n=$b.ReadUInt32(); $v=$b.ReadBytes($n); if($v[-1] -ne 0){throw 'Missing terminator'}; [Text.Encoding]::ASCII.GetString($v,0,$n-1) }
if($b.ReadUInt32() -ne 0x2F7A6A25 -or $b.ReadUInt32() -ne 0x000265A8 -or $b.ReadUInt32() -ne 37){throw 'Header mismatch'}
if((Read-Text) -ne 'FQN NOT FOUND' -or (Read-Text) -ne '/missing'){throw 'Error/path mismatch'}
if($b.ReadUInt32() -ne 0){throw 'Metadata mismatch'}
1..3 | ForEach-Object {if((Read-Text) -ne ''){throw 'Metadata text mismatch'}}
if($b.ReadUInt64() -ne 0 -or $b.ReadUInt32() -ne 0 -or $b.ReadUInt32() -ne 0 -or $b.BaseStream.Position -ne $b.BaseStream.Length){throw 'Trailing fields mismatch'}
$t=$a.GetType('NexusToRServer.NET.Packets.Client.WorldByteReport',$true)
$p=[Activator]::CreateInstance($t,$true)
$data=[byte[]](0xE9,0x8D,0xB2,0x8E,7,0,0xAB,0x65,48,0,0,0)+[byte[]]::new(48)
$p.SetBuffers($data); $p.ReadImplementation()
$p.SetBuffers([byte[]]$data[0..58]); $rejected=$false
try {$p.ReadImplementation()} catch {$rejected=$true}
if(!$rejected){throw 'Truncated report accepted'}
'PASS: native repository failure wire fields, route reversal, valid 48-byte World report, and malformed report rejection.'
$t=$a.GetType('NexusToRServer.NET.Packets.Client.RepositoryDataRequest',$true)
$p=[Activator]::CreateInstance($t,$true)
$data=[byte[]](0x17,0x0D,0x3B,0x46,2,0,0xA8,0x65,37,0,0,0,9,0,0,0)+[Text.Encoding]::ASCII.GetBytes("/missing`0")
$p.SetBuffers($data); $p.ReadImplementation()
$unterminated=[byte[]]$data.Clone(); $unterminated[-1]=65
foreach($bad in @([byte[]]$data[0..23],$unterminated,[byte[]]($data+[byte]0))) {
    $p.SetBuffers($bad); $rejected=$false
    try {$p.ReadImplementation()} catch {$rejected=$true}
    if(!$rejected){throw 'Malformed resource request accepted'}
}
'PASS: resource request parsing, truncation, missing terminator, and trailing-byte rejection.'
$t=$a.GetType('NexusToRServer.NET.Packets.Client.RepositoryDataReceipt',$true)
$p=[Activator]::CreateInstance($t,$true)
$data=[byte[]](0xC3,0x82,0xBF,0xB4,2,0,0xA8,0x65,0,0,0,0)
$p.SetBuffers($data); $p.ReadImplementation()
foreach($bad in @([byte[]]$data[0..10],[byte[]]($data+[byte]0))) {
    $p.SetBuffers($bad); $rejected=$false
    try {$p.ReadImplementation()} catch {$rejected=$true}
    if(!$rejected){throw 'Malformed resource receipt accepted'}
}
'PASS: captured repository receipt and exact-length validation.'
