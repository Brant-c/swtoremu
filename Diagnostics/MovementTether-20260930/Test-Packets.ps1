$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$a=[Reflection.Assembly]::LoadFrom((Join-Path $root 'SharpServer/bin/Debug/NexusToRServer.exe'))
$t=$a.GetType('NexusToRServer.NET.Packets.Server.AreaPlayerMovementUpdate',$true)
foreach($id in @([uint64]0x4000010E218A839B,[uint64]0x4000010E218A839C)) {
 foreach($h in @([uint16]8,[uint16]19)) {
  foreach($enter in @($false,$true)) {
   $args=if($enter){[object[]]@($id)}else{[object[]]@($id,[single]-62.9,[single]-6.9,[single]-126.3)}
   $p=[Activator]::CreateInstance($t,$args);$p.ClientAreaServiceID=$h;$p.InitBuffers();$p.WriteImplementation();$b=$p._stream.ToArray()
   if([BitConverter]::ToUInt32($b,0)-ne 0x0D446E80 -or [BitConverter]::ToUInt16($b,4)-ne 0x65B3 -or [BitConverter]::ToUInt16($b,6)-ne $h){throw 'Wrong packet routing'}
   [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot ('packet-{0:X16}-{1}-{2}.bin' -f $id,$h,$enter)),$b)
  }
 }
}
foreach($bad in @([single]::NaN,[single]::PositiveInfinity)) {
 $failed=$false
 try {$null=[Activator]::CreateInstance($t,[object[]]@([uint64]0x4000010E218A839B,$bad,[single]0,[single]0))}catch{$failed=$true}
 if(!$failed){throw 'Non-finite anchor accepted'}
}
'PASS selected identities, area handles, anchor/reentry packet exports, invalid anchor rejection'
