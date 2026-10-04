param([string]$AssemblyPath=(Join-Path $PSScriptRoot '..\..\SharpServer\bin\Debug\NexusToRServer.exe'))
$ErrorActionPreference='Stop'
$assembly=[Reflection.Assembly]::LoadFrom($AssemblyPath)
$npcType=$assembly.GetType('NexusToRServer.NET.Packets.Server.AreaTaxiAwareness',$true)
$interactionType=$assembly.GetType('NexusToRServer.NET.Packets.Server.AreaTaxiInteraction',$true)
$nodes=[uint64[]]@(0x1AC7002000,0x1AC7002001,0x1AC7002002,0x1AC7002003,0x1AC7002004)
foreach($area in @([uint16]8,[uint16]19)) {
    $argsNpc=New-Object object[] 1; $argsNpc[0]=$nodes
    $packet=[Activator]::CreateInstance($npcType,$argsNpc)
    $packet.ClientAreaServiceID=$area; $packet.InitBuffers(); $packet.WriteImplementation()
    [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "awareness-$area.bin"),$packet._stream.ToArray())
    foreach($stage in @('known','clear','open')) {
        $target=if($stage -eq 'open') {$nodes[0]} else {[uint64]0}
        $packet=[Activator]::CreateInstance($interactionType,[object[]]@([uint64]0x4000010E218A839B,[uint64]$target,[bool]($stage -ne 'known')))
        $packet.ClientAreaServiceID=$area; $packet.InitBuffers(); $packet.WriteImplementation()
        [IO.File]::WriteAllBytes((Join-Path $PSScriptRoot "$stage-$area.bin"),$packet._stream.ToArray())
    }
}
foreach($bad in @([uint64[]]@(1,2,3,4,5),[uint64[]]@(0x1AC7002000,0x1AC7002000,0x1AC7002002,0x1AC7002003,0x1AC7002004))) {
    $argsNpc=New-Object object[] 1; $argsNpc[0]=$bad; $rejected=$false
    try { [Activator]::CreateInstance($npcType,$argsNpc) | Out-Null } catch {$rejected=$true}
    if(!$rejected) {throw 'Invalid fixture identities accepted'}
}
'PASS: embedded NPC fixture, runtime identity remapping, invalid identities rejected, packets emitted for areas 8/19.'
