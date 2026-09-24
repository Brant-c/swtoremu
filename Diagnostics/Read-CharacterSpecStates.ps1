Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class StartupMemory {
 [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@
foreach($client in Get-Process swtor-emu) {
 $handle=[StartupMemory]::OpenProcess(0x410,$false,$client.Id)
 if($handle -eq [IntPtr]::Zero){continue}
 try {
  function Read-Memory([long]$address,[int]$length) {
   $bytes=New-Object byte[] $length
   $read=[UIntPtr]::Zero
   if(-not [StartupMemory]::ReadProcessMemory($handle,[IntPtr]::new($address),$bytes,[UIntPtr]::new([uint32]$length),[ref]$read)){return $null}
   return ,$bytes
  }
  $imageBase=$client.MainModule.BaseAddress.ToInt64()
  'PID={0} base={1:X8}' -f $client.Id,$imageBase
  foreach($entry in @(@('GUI',0xF41CD4,0x228),@('CharacterSpecs',0x10929DC,0x60),@('Game',0x10926F0,0x40))) {
   $pointerBytes=Read-Memory ($imageBase+$entry[1]) 4
   if($null -eq $pointerBytes){continue}
   $pointer=[BitConverter]::ToUInt32($pointerBytes,0)
   if(-not $pointer){continue}
   $data=Read-Memory $pointer $entry[2]
   if($null -eq $data){continue}
   '{0}={1:X8} {2}' -f $entry[0],$pointer,[BitConverter]::ToString($data)
   if($entry[0] -eq 'CharacterSpecs') {
    $stack=New-Object 'System.Collections.Generic.Stack[uint32]'
    $seen=New-Object 'System.Collections.Generic.HashSet[uint32]'
    $stack.Push([BitConverter]::ToUInt32($data,0x28))
    while($stack.Count -and $seen.Count -lt 4096) {
     $node=$stack.Pop()
     if(-not $node -or $node -eq $pointer+0x20 -or -not $seen.Add($node)){continue}
     $nodeBytes=Read-Memory $node 24
     if($null -eq $nodeBytes){continue}
     $object=[BitConverter]::ToUInt32($nodeBytes,0x10)
     $objectBytes=Read-Memory $object 464
     if($null -ne $objectBytes) {
      'Spec object={0:X8} state={1}' -f $object,[BitConverter]::ToUInt32($objectBytes,12)
      for($offset=0x160;$offset -le 0x160;$offset+=4) {
       $candidate=[BitConverter]::ToUInt32($objectBytes,$offset)
       if($candidate -lt 65536){continue}
       $textBytes=Read-Memory $candidate 160
       if($null -eq $textBytes){continue}
       $value=[Text.Encoding]::Unicode.GetString($textBytes).Split([char]0)[0]
       if($value -match '^[\x20-\x7e]{5,}$') {'  +{0:X2} wide={1}' -f $offset,$value}
       $value=[Text.Encoding]::ASCII.GetString($textBytes).Split([char]0)[0]
       if($value -match '^[\x20-\x7e]{5,}$' -and $value -match '[a-zA-Z]{4}' -and $value -notmatch '\?') {'  +{0:X2} ascii={1}' -f $offset,$value}
      }
     }
     $stack.Push([BitConverter]::ToUInt32($nodeBytes,0))
     $stack.Push([BitConverter]::ToUInt32($nodeBytes,4))
    }
   }
  }
 } finally { [void][StartupMemory]::CloseHandle($handle) }
}
