$ErrorActionPreference = 'Stop'
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class AreaObjectMemory {
 [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@
foreach ($client in Get-Process swtor-emu -ErrorAction SilentlyContinue) {
 $handle=[AreaObjectMemory]::OpenProcess(0x410,$false,$client.Id)
 if ($handle -eq [IntPtr]::Zero) { continue }
 try {
  function Read-Bytes([long]$address,[int]$length) {
   $data=New-Object byte[] $length; $read=[UIntPtr]::Zero
   if(-not [AreaObjectMemory]::ReadProcessMemory($handle,[IntPtr]::new($address),$data,[UIntPtr]::new([uint32]$length),[ref]$read)){throw ('Cannot read {0:X8}' -f $address)}
   return ,$data
  }
  function Read-U32([long]$address) { [BitConverter]::ToUInt32((Read-Bytes $address 4),0) }
  $base=$client.MainModule.BaseAddress.ToInt64()
  $manager=$base+0x1096DF8
  $area=Read-U32 ($manager+0x28)
  'PID={0} base={1:X8} manager={2:X8} area={3:X8}' -f $client.Id,$base,$manager,$area
  if(!$area){continue}
  $object=Read-Bytes $area 192
  'Object[0..BF]={0}' -f [BitConverter]::ToString($object)
  $vtable=[BitConverter]::ToUInt32($object,0)
  'vtable={0:X8} rva={1:X8}' -f $vtable,($vtable-$base)
  $slots=Read-Bytes $vtable 256
  for($offset=0;$offset -lt $slots.Length;$offset+=4) {
   $method=[BitConverter]::ToUInt32($slots,$offset)
   'slot+{0:X2}={1:X8} rva={2:X8}' -f $offset,$method,($method-$base)
  }
 } finally {[void][AreaObjectMemory]::CloseHandle($handle)}
}
