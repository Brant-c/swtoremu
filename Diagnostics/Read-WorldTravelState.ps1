Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class StartupMemory {
 [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@
foreach($client in Get-Process swtor-emu -ErrorAction SilentlyContinue) {
 $handle=[StartupMemory]::OpenProcess(0x410,$false,$client.Id)
 if($handle -eq [IntPtr]::Zero){continue}
 try {
  function Read-Dword([long]$address) {
   $data=New-Object byte[] 4; $read=[UIntPtr]::Zero
   if(-not [StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($address),$data,[UIntPtr]::new(4),[ref]$read)){throw ('Cannot read {0:X8}' -f $address)}
   [BitConverter]::ToUInt32($data,0)
  }
  $imageBase=$client.MainModule.BaseAddress.ToInt64()
  $errorText=Read-Dword ($imageBase+0x1094660)
  $errorEnd=Read-Dword ($imageBase+0x1094664)
  if($errorText -and $errorEnd -gt $errorText -and ($errorEnd-$errorText) -lt 65536){
   $errorBytes=New-Object byte[] ($errorEnd-$errorText); $read=[UIntPtr]::Zero
   [void][StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($errorText),$errorBytes,[UIntPtr]::new($errorBytes.Length),[ref]$read)
   'Script error context: {0}' -f [Text.Encoding]::Unicode.GetString($errorBytes)
  }
  $travelManager=$imageBase+0x1096DF8
  $area=Read-Dword ($travelManager+0x28)
  'Travel manager={0:X8} area={1:X8}' -f $travelManager,$area
  if($area){'Travel area state (+8C)={0}' -f (Read-Dword ($area+0x8C))}
  $destination=Read-Dword ($travelManager+0x74)
  if($destination){
   $text=New-Object byte[] 256; $read=[UIntPtr]::Zero
   [void][StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($destination),$text,[UIntPtr]::new(256),[ref]$read)
   'Deferred destination: {0}' -f [Text.Encoding]::ASCII.GetString($text).Split([char]0)[0]
  }
  $config=Read-Dword ($imageBase+0xF8B000)
  if($config) {
   $world=Read-Dword ($config+0x14)
   if($world){
    foreach($off in 0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60){'world+{0:X2}={1:X8}' -f $off,(Read-Dword ($world+$off))}; $travel=Read-Dword ($world+0x30)
    if($travel){
     $travelVtable=Read-Dword $travel
     'World handler={0:X8} travel target={1:X8} vtableRVA={2:X8} sendToAreaRVA={3:X8}' -f $world,$travel,($travelVtable-$imageBase),((Read-Dword ($travelVtable+0x44))-$imageBase)
    }
   }
   $repository=Read-Dword ($config+0x1C)
   if($repository){
    'Repository service object={0:X8}' -f (Read-Dword ($repository+0x50))
    $route=Read-Dword ($repository+8)
    if($route){'Repository route={0:X8} +28={1:X8} +44={2:X8}' -f $route,(Read-Dword ($route+0x28)),(Read-Dword ($route+0x44))}
   }
   $revision=Read-Dword ($config+0xC0)
   $bytes=New-Object byte[] 80; $read=[UIntPtr]::Zero
   if($revision){[void][StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($revision),$bytes,[UIntPtr]::new(80),[ref]$read)}
   'Resource revision text: {0}' -f [Text.Encoding]::ASCII.GetString($bytes).Split([char]0)[0]
  }
  $adapter=Read-Dword ($imageBase+0x1092900)
  if(-not $adapter){continue}
  $owner=Read-Dword ($adapter+4)
  if(-not $owner){continue}
  'PID={0} adapter={1:X8} owner={2:X8} state={3} workerThread={4} queued={5}' -f $client.Id,$adapter,$owner,(Read-Dword ($owner+0x14)),(Read-Dword ($owner+0x10)),(Read-Dword ($owner+0x2E8))
  $queue=$owner+0x2D8
  $provider=Read-Dword ($owner+8)
  $vtable=Read-Dword $provider
  'Provider sync RVA={0:X8} pump RVA={1:X8}' -f ((Read-Dword ($vtable+4))-$imageBase),((Read-Dword ($vtable+0x18))-$imageBase)
  'Provider={0:X8} revisionGetterRVA={1:X8} pools={2:X8},{3:X8}' -f $provider,((Read-Dword ($vtable+0x10))-$imageBase),(Read-Dword ($owner+0x470)),(Read-Dword ($owner+0x474))
  'Pending resource-read queue={0}' -f (Read-Dword ($owner+0x168))
  # B4ACB0-B4ACA0 is the number of active entries capped at50 by B4632E.
  $active=(Read-Dword ($owner+0x298))+(Read-Dword ($owner+0x2B4))+(Read-Dword ($owner+0x2D0))
  'Active resource reads={0}/50; resource bytes={1}' -f $active,(Read-Dword ($imageBase+0xF41F84))
  $priority=Read-Dword ($queue+0x24)
  if($priority -lt 32) {
   $node=Read-Dword ($queue+0x30+8*$priority)
   for($i=0;$node -and $i -lt 6;$i++) {
    $job=Read-Dword $node
    $path=Read-Dword ($job+8)
    $bytes=New-Object byte[] 256; $read=[UIntPtr]::Zero
    [void][StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($path),$bytes,[UIntPtr]::new(256),[ref]$read)
    ' queued job={0:X8} type={1} path={2}' -f $job,(Read-Dword ($job+4)),[Text.Encoding]::ASCII.GetString($bytes).Split([char]0)[0]
    $node=Read-Dword ($node+8)
   }
  }
 } finally {[void][StartupMemory]::CloseHandle($handle)}
}
