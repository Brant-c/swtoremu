param([string]$AssemblyPath = (Join-Path $PSScriptRoot '..\..\SharpServer\bin\Debug\NexusToRServer.exe'))
$ErrorActionPreference = 'Stop'
$assembly = [Reflection.Assembly]::LoadFrom($AssemblyPath)
$service = $assembly.GetType('NexusToRServer.AreaServer.WellerConversation',$true)
$parse = $service.GetMethod('TryParse',[Reflection.BindingFlags]'Static,NonPublic')
$valid = [byte[]](('10-00-00-00-C7-71-C3-79-12-D0-62-EB-99-01-CC-1A-C6-F6-DC-6D' -split '-') | ForEach-Object { [Convert]::ToByte($_,16) })
$args1 = [object[]]@($valid,[uint64]0)
if (!$parse.Invoke($null,$args1) -or $args1[1] -ne [uint64]0x1AC6F6DC6D) { throw 'Captured click did not decode' }
for ($count=0; $count -lt $valid.Length; $count++) {
    $args1 = [object[]]@([byte[]]$valid[0..([Math]::Max(0,$count-1))],[uint64]0)
    if ($parse.Invoke($null,$args1)) { throw "Truncation accepted: $count" }
}
foreach ($index in @(0,4,5,9,13,14)) {
    $bad = $valid.Clone(); $bad[$index] = $bad[$index] -bxor 0x10
    $args1 = [object[]]@($bad,[uint64]0)
    if ($parse.Invoke($null,$args1)) { throw "Malformed selector/type accepted: $index" }
}
$extra = [byte[]]($valid + 0); $extra[0]++
$args1 = [object[]]@($extra,[uint64]0)
if ($parse.Invoke($null,$args1)) { throw 'Trailing byte accepted' }
$packetType = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaWellerConversation',$true)
foreach ($serviceId in @([uint16]8,[uint16]19)) {
    $packet = [Activator]::CreateInstance($packetType,[object[]]@([uint64]0x1AC7000001,[uint64]0x1AC7000002,[uint64]0x1AC6F6DC6D))
    $packet.ClientAreaServiceID=$serviceId; $packet.InitBuffers(); $packet.WriteImplementation()
    $data = $packet._stream.ToArray()
    if ([BitConverter]::ToUInt16($data,4) -ne 0x65B3 -or [BitConverter]::ToUInt16($data,6) -ne $serviceId) { throw 'Routing mismatch' }
    [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "conversation-$serviceId.bin"),$data)
}
[IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'click-body.bin'),$valid)
$parseRequest = $service.GetMethod('TryParseRequest',[Reflection.BindingFlags]'Static,NonPublic')
foreach ($sid in @([uint32]0x70C14D2A,[uint32]0x14CDD239)) {
    $endBody = $valid.Clone(); [BitConverter]::GetBytes($sid).CopyTo($endBody,9)
    $endBody[16]=0xC7; $endBody[17]=0; $endBody[18]=0; $endBody[19]=2
    $args1 = [object[]]@($endBody,$sid,[uint64]0)
    if (!$parseRequest.Invoke($null,$args1) -or $args1[2] -ne [uint64]0x1AC7000002) { throw 'End request failed to decode' }
    [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot ('end-body-{0:X8}.bin' -f $sid)),$endBody)
    for ($count=0; $count -lt $endBody.Length; $count++) {
        $short = New-Object byte[] $count
        [Array]::Copy($endBody,$short,$count)
        if ($parseRequest.Invoke($null,[object[]]@([byte[]]$short,[uint32]$sid,[uint64]0))) { throw 'Truncated end request accepted' }
    }
    $bad = [byte[]]($endBody + 0); $bad[0]++
    if ($parseRequest.Invoke($null,[object[]]@($bad,$sid,[uint64]0))) { throw 'End request with trailing byte accepted' }
}
$canEnd = $service.GetMethod('CanEnd',[Reflection.BindingFlags]'Static,NonPublic')
$endArgs = [object[]]@([uint64]2,[uint64]2,[uint64]3,[uint64]3,[uint32]0x65B30008,[uint16]8)
if (!$canEnd.Invoke($null,$endArgs)) { throw 'Valid active conversation rejected' }
foreach ($index in @(0,1,2,3,4,5)) {
    $bad = $endArgs.Clone(); $bad[$index] = [Convert]::ChangeType(0,$endArgs[$index].GetType())
    if ($canEnd.Invoke($null,$bad)) { throw "Foreign/stale conversation end accepted: $index" }
}
foreach ($serviceId in @([uint16]8,[uint16]19)) {
    foreach ($stage in @(1,2)) {
        $packet = [Activator]::CreateInstance($packetType,[object[]]@([uint64]0x1AC7000001,[uint64]0x1AC7000002,[uint64]0x1AC6F6DC6D,[int]$stage))
        $packet.ClientAreaServiceID=$serviceId; $packet.InitBuffers(); $packet.WriteImplementation()
        [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "end-$serviceId-$stage.bin"),$packet._stream.ToArray())
    }
}
$allocator = $assembly.GetType('NexusToRServer.NET.Packets.Server.AreaAbilityEffectReplication',$true).GetMethod('NextNodeID',[Reflection.BindingFlags]'Static,NonPublic')
$ids = @(); for ($i=0; $i -lt 20; $i++) { $ids += $allocator.Invoke($null,@()) }
if (@($ids | Select-Object -Unique).Count -ne 20) { throw 'Shared runtime node allocator repeated an identity' }
'PASS: interaction and both end selectors; truncations/trailing data; active-controller ownership guards; start/end packets at area8/19; shared node allocator.'
