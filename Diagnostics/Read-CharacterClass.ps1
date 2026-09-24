param([UInt64]$NodeAddress, [UInt64]$MethodAddress, [UInt64]$SignatureAddress)
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class CharacterMemory {
 [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] bytes, UIntPtr size, out UIntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@
foreach ($client in Get-Process swtor-emu) {
    $handle=[CharacterMemory]::OpenProcess(0x410,$false,$client.Id)
    if ($handle -eq [IntPtr]::Zero) { continue }
    try {
        function Read-Bytes([UInt64]$Address,[int]$Length) {
            $data=New-Object byte[] $Length
            $read=[UIntPtr]::Zero
            if (![CharacterMemory]::ReadProcessMemory($handle,[IntPtr]::new([long]$Address),$data,[UIntPtr]::new([uint32]$Length),[ref]$read)) { throw "Cannot read $Address" }
            return ,$data
        }
        function Read-U32([UInt64]$Address) { [BitConverter]::ToUInt32((Read-Bytes $Address 4),0) }
        function Show-Signature([UInt64]$Address) {
            $begin=Read-U32 ($Address+4)
            $end=Read-U32 ($Address+8)
            if ($end -lt $begin -or $end-$begin -gt 1024) { throw 'Invalid signature vector' }
            'Signature vector={0}' -f [BitConverter]::ToString((Read-Bytes $begin ($end-$begin)))
            $type=Read-U32 $Address
            'Signature descriptor {0:X8}={1}' -f $type,[BitConverter]::ToString((Read-Bytes $type 96))
            $typeBegin=Read-U32 $type
            $typeEnd=Read-U32 ($type+4)
            if ($typeEnd -ge $typeBegin -and $typeEnd-$typeBegin -lt 1024) {
                'Signature types={0}' -f [BitConverter]::ToString((Read-Bytes $typeBegin ($typeEnd-$typeBegin)))
            }
        }
        $classHandle=Read-U32 ($NodeAddress+0x48)
        $class=Read-U32 ($classHandle+0x18)
        $definition=Read-U32 ($class+8)
        $record=Read-U32 ($definition+4)
        $data=Read-Bytes $record 64
        'PID={0} node={1:X8} class={2:X8} definition={3:X8} record={4:X8}' -f $client.Id,$NodeAddress,$class,$definition,$record
        'Class ID={0} record={1}' -f [BitConverter]::ToUInt64($data,8),[BitConverter]::ToString($data)
        'Definition={0}' -f [BitConverter]::ToString((Read-Bytes $definition 64))
        'Method cache={0}' -f [BitConverter]::ToString((Read-Bytes ($class+0x60) 64))
        if ($MethodAddress) {
            'Method={0}' -f [BitConverter]::ToString((Read-Bytes $MethodAddress 80))
            $signature=Read-U32 ($MethodAddress+0x24)
            'Expected signature at {0:X8}={1}' -f $signature,[BitConverter]::ToString((Read-Bytes $signature 96))
            Show-Signature $signature
        }
        if ($SignatureAddress) {
            'Actual signature={0}' -f [BitConverter]::ToString((Read-Bytes $SignatureAddress 96))
            Show-Signature $SignatureAddress
        }
    } catch { 'PID={0}: {1}' -f $client.Id,$_ }
    finally { [void][CharacterMemory]::CloseHandle($handle) }
}
