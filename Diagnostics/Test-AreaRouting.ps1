param([string]$AssemblyPath=(Join-Path $PSScriptRoot 'RepositoryValidationBuild\NexusToRServer.exe'))
$ErrorActionPreference='Stop'
$assembly=[Reflection.Assembly]::LoadFrom($AssemblyPath)
$type=$assembly.GetType('NexusToRServer.NET.Packets.Server.AreaSetCharacter',$true)
foreach($clientHandle in @([uint16]8,[uint16]19)) {
 $packet=[Activator]::CreateInstance($type,[object[]]@([uint64]0x102030405060708))
 $packet.ClientAreaServiceID=$clientHandle
 $packet.InitBuffers(); $packet.WriteImplementation()
 $bytes=$packet._stream.ToArray()
 if($bytes.Length -ne 16){throw 'Unexpected AreaSetCharacter length'}
 if([BitConverter]::ToUInt16($bytes,4) -ne 0x65B3 -or [BitConverter]::ToUInt16($bytes,6) -ne $clientHandle){throw 'Area handle pair mismatch'}
 if([BitConverter]::ToUInt64($bytes,8) -ne 0x102030405060708){throw 'Character payload changed'}
}
$packet=[Activator]::CreateInstance($type,[object[]]@([uint64]1))
$packet.InitBuffers(); $rejected=$false
try{$packet.WriteImplementation()}catch{$rejected=$true}
if(!$rejected){throw 'Unattached area packet accepted'}
$base=$assembly.GetType('NexusToRServer.NET.TORAreaServerPacket',$true)
$names=@('AreaRequestRPC','AreaEffEventMessage','AreaUpdateTimeSource','AreaClientReplicationTransaction','AreaHackPack','AreaSetCharacter','SMsg23B61238','AreaAwarenessEntered','AreaTeleportCharacter','AreaTalk','AreaSendAwarenessRange')
foreach($name in $names){if(!$base.IsAssignableFrom($assembly.GetType('NexusToRServer.NET.Packets.Server.'+$name,$true))){throw ('Missing area routing: '+$name)}}
'PASS: area source 65B3, dynamic destinations 8/19, intact character payload, unattached rejection, all 11 legacy area packets use shared routing.'
