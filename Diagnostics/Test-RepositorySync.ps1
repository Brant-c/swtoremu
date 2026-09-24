# Use 32-bit Windows PowerShell to load the x86 emulator assembly.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$assembly=[Reflection.Assembly]::LoadFrom((Join-Path $root 'SharpServer\bin\Debug\NexusToRServer.exe'))
$requestType=$assembly.GetType('NexusToRServer.NET.Packets.Client.RepositorySyncRequest',$true)
$replyType=$assembly.GetType('NexusToRServer.NET.Packets.Server.RepositorySyncReply',$true)
$data=[byte[]](0x86,0x7B,0xF7,0x45,2,0,0xA8,0x65,0,0,0,0,0,0,0,0)
$request=[Activator]::CreateInstance($requestType,$true)
$request.SetBuffers($data)
$request.ReadImplementation()
if($request._stream.Position -ne 16){throw 'Request was not fully consumed'}
foreach($bad in @([byte[]]$data[0..14], [byte[]]($data+[byte]0))) {
    $request.SetBuffers($bad)
    $rejected=$false
    try{$request.ReadImplementation()}catch{$rejected=$true}
    if(!$rejected){throw 'Malformed request was accepted'}
}
$reply=[Activator]::CreateInstance($replyType,[object[]]@([uint16]2))
$reply.InitBuffers()
$reply.WriteImplementation()
$hex=[BitConverter]::ToString($reply._stream.ToArray())
if($hex -ne '72-9B-95-26-A8-65-02-00-01-00-00-00-00'){throw ('Unexpected wire reply: '+$hex)}
'PASS: captured request, truncated/extra-byte rejection, and native empty-string reply encoding.'
$revisionType=$assembly.GetType('NexusToRServer.NET.Packets.Server.RepositoryRevision',$true)
$revision=[Activator]::CreateInstance($revisionType,[object[]]@([uint16]2))
$revision.InitBuffers()
$revision.WriteImplementation()
if([BitConverter]::ToString($revision._stream.ToArray()) -ne 'CF-1A-8C-A0-A8-65-02-00-02-00-00-00-31-00'){throw 'Revision notification encoding mismatch'}
'PASS: native repository revision notification encoding.'
