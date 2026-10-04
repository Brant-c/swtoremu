param(
    [Parameter(Mandatory=$true)][string]$OutputCsv,
    [int]$WaitSeconds = 180,
    [int]$ObserveSeconds = 900,
    [int]$IntervalMilliseconds = 20
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputCsv) { throw 'Refusing to overwrite an existing timeline.' }
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class RoomStateMemory {
 [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@
function Open-ActiveClient {
    foreach ($client in Get-Process swtor-emu -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending) {
        $handle=[RoomStateMemory]::OpenProcess(0x410,$false,$client.Id)
        if ($handle -eq [IntPtr]::Zero) { continue }
        $base=$client.MainModule.BaseAddress.ToInt64()
        $data=New-Object byte[] 4; $read=[UIntPtr]::Zero
        $ok=[RoomStateMemory]::ReadProcessMemory($handle,[IntPtr]::new($base+0x1096E20),$data,[UIntPtr]::new(4),[ref]$read)
        $area=if($ok){[BitConverter]::ToUInt32($data,0)}else{0}
        if($area){return [pscustomobject]@{Process=$client;Handle=$handle;Base=$base}}
        [void][RoomStateMemory]::CloseHandle($handle)
    }
    return $null
}
$started=[Diagnostics.Stopwatch]::StartNew()
$target=$null
while(!$target -and $started.Elapsed.TotalSeconds -lt $WaitSeconds) {
    $target=Open-ActiveClient
    if(!$target){Start-Sleep -Milliseconds 100}
}
if(!$target){throw 'No swtor-emu process with a non-null travel-area pointer appeared.'}
Write-Output ('observer-target PID={0} module-base=0x{1:X8} global-area-pointer=0x{2:X8}' -f
    $target.Process.Id,[uint32]$target.Base,[uint32]($target.Base+0x1096E20))
$writer=[IO.StreamWriter]::new($OutputCsv,$false,[Text.UTF8Encoding]::new($false))
try {
    $writer.WriteLine('LocalTime,ElapsedMs,Event,PID,Area,RootState,RootAux,PrimaryRoom,PrimaryState,PrimaryAux,SecondaryRoom,SecondaryState,SecondaryAux,TreeSentinel,TreeBegin')
    $last=''; $lastHeartbeat=-1000L; $clock=[Diagnostics.Stopwatch]::StartNew()
    function Read-U32([long]$address) {
        $data=New-Object byte[] 4; $read=[UIntPtr]::Zero
        if(-not [RoomStateMemory]::ReadProcessMemory($target.Handle,[IntPtr]::new($address),$data,[UIntPtr]::new(4),[ref]$read)){return $null}
        return [BitConverter]::ToUInt32($data,0)
    }
    while($clock.Elapsed.TotalSeconds -lt $ObserveSeconds -and -not $target.Process.HasExited) {
        $area=Read-U32 ($target.Base+0x1096E20)
        if($null -eq $area){break}
        $rootState=if($area){Read-U32 ($area+0x8C)}else{$null}
        $rootAux=if($area){Read-U32 ($area+0x90)}else{$null}
        $primary=if($area){Read-U32 ($area+0x2A0)}else{$null}
        $secondary=if($area){Read-U32 ($area+0x400)}else{$null}
        $primaryState=if($primary){Read-U32 ($primary+0x8C)}else{$null}
        $primaryAux=if($primary){Read-U32 ($primary+0x90)}else{$null}
        $secondaryState=if($secondary){Read-U32 ($secondary+0x8C)}else{$null}
        $secondaryAux=if($secondary){Read-U32 ($secondary+0x90)}else{$null}
        $sentinel=if($area){$area+0x3DC}else{$null}
        $begin=if($area){Read-U32 ($area+0x3E0)}else{$null}
        $signature=@($area,$rootState,$rootAux,$primary,$primaryState,$primaryAux,$secondary,$secondaryState,$secondaryAux,$begin) -join ':'
        $elapsed=[long]$clock.Elapsed.TotalMilliseconds
        $event=if($signature -ne $last){'change'}elseif($elapsed-$lastHeartbeat -ge 1000){'heartbeat'}else{''}
        if($event){
            $hex={param($v) if($null -eq $v){''}else{'0x{0:X8}' -f [uint32]$v}}
            $writer.WriteLine(('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}' -f
                (Get-Date -Format o),$elapsed,$event,$target.Process.Id,(& $hex $area),$rootState,$rootAux,
                (& $hex $primary),$primaryState,$primaryAux,(& $hex $secondary),$secondaryState,$secondaryAux,
                (& $hex $sentinel),(& $hex $begin)))
            $writer.Flush(); $lastHeartbeat=$elapsed
        }
        $last=$signature
        Start-Sleep -Milliseconds $IntervalMilliseconds
    }
    $writer.WriteLine(('{0},{1},observer-end,{2},,,,,,,,,,,,' -f (Get-Date -Format o),[long]$clock.Elapsed.TotalMilliseconds,$target.Process.Id))
    $writer.Flush()
} finally {
    $writer.Dispose()
    [void][RoomStateMemory]::CloseHandle($target.Handle)
}
