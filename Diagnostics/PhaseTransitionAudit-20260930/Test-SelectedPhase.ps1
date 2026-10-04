param([string]$AssemblyPath='D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe')
$ErrorActionPreference='Stop'
if ([Environment]::Is64BitProcess) { throw 'Use 32-bit PowerShell.' }
$assembly=[Reflection.Assembly]::LoadFrom($AssemblyPath)
$destroy=$assembly.GetType('NexusToRServer.NET.Packets.Server.AreaReplicationDestroy',$true)
$crt=$assembly.GetType('NexusToRServer.NET.Packets.Server.AreaClientReplicationTransaction',$true)
$oldDirectory=[Environment]::CurrentDirectory
try {
 [Environment]::CurrentDirectory='D:\SWTORClassic\swtoremu\SharpServer\bin\Debug'
 foreach($id in @([uint64]0x4000010E218A839B,[uint64]0x4000010E218A1234)) {
  $label=$id.ToString('X16')
  foreach($handle in @([uint16]8,[uint16]19)) {
   $packet=[Activator]::CreateInstance($destroy,[object[]]@([uint32]0x1B502E,[uint64]0x1AC6F6DC1F,$true,$id))
   $packet.ClientAreaServiceID=$handle;$packet.InitBuffers();$packet.WriteImplementation()
   [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "clear-$label-$handle.bin"),$packet._stream.ToArray())
  }
  foreach($number in @(2,4)) {
   $packet=[Activator]::CreateInstance($crt,[object[]]@('tython_blockout','4611686019869492753','1',[int]$number,$id))
   $packet.ClientAreaServiceID=[uint16]8;$packet.InitBuffers();$packet.WriteImplementation()
   [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "crt$number-$label.bin"),$packet._stream.ToArray())
  }
 }
 $rejected=$false
 try { [void][Activator]::CreateInstance($destroy,[object[]]@([uint32]0x1B502E,[uint64]0x1AC6F6DC1F,$true,[uint64]0)) } catch { $rejected=$true }
 if(!$rejected) {throw 'Missing selected player ID accepted'}
 $packet=[Activator]::CreateInstance($destroy,[object[]]@([uint32]0x1B502E,[uint64]0x1AC6F6DC1F))
 $packet.ClientAreaServiceID=[uint16]8;$packet.InitBuffers();$packet.WriteImplementation()
 [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'default.bin'),$packet._stream.ToArray())
 'PASS: selected IDs serialized across startup/exit, zero rejected, default control captured.'
} finally { [Environment]::CurrentDirectory=$oldDirectory }
