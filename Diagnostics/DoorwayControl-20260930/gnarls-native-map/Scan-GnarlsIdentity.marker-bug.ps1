param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][string]$MarkerLog,
    [int]$WaitSeconds = 900
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputDirectory){throw 'Refusing to overwrite an existing native-map capture.'}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null

Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class GnarlsMapMemory {
 [StructLayout(LayoutKind.Sequential)] public struct MBI {
   public IntPtr BaseAddress; public IntPtr AllocationBase; public uint AllocationProtect;
   public UIntPtr RegionSize; public uint State; public uint Protect; public uint Type;
 }
 [DllImport("kernel32.dll",SetLastError=true)] public static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern UIntPtr VirtualQueryEx(IntPtr process,IntPtr address,out MBI info,UIntPtr length);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
 public static int[] FindAll(byte[] data, byte[] pattern) {
   var hits=new List<int>();
   if(pattern==null || pattern.Length==0 || data==null) return hits.ToArray();
   for(int i=0;i<=data.Length-pattern.Length;i++) {
     int j=0; for(;j<pattern.Length;j++) if(data[i+j]!=pattern[j]) break;
     if(j==pattern.Length) hits.Add(i);
   }
   return hits.ToArray();
 }
}
'@

function Read-Bytes([IntPtr]$Handle,[long]$Address,[int]$Length){
    $buffer=New-Object byte[] $Length; $read=[UIntPtr]::Zero
    if(-not [GnarlsMapMemory]::ReadProcessMemory($Handle,[IntPtr]::new($Address),$buffer,[UIntPtr]::new($Length),[ref]$read)){return $null}
    $count=[int]$read.ToUInt64()
    if($count -eq $Length){return ,$buffer}
    if($count -le 0){return $null}
    $short=New-Object byte[] $count; [Array]::Copy($buffer,$short,$count); return ,$short
}
function Read-U32([IntPtr]$Handle,[long]$Address){
    $bytes=Read-Bytes $Handle $Address 4
    if($null -eq $bytes -or $bytes.Length -ne 4){return $null}
    [BitConverter]::ToUInt32($bytes,0)
}
function Hex([object]$Value){if($null -eq $Value){''}else{'0x{0:X8}' -f [uint32]$Value}}
function Get-Snippet([byte[]]$Data,[int]$Offset,[int]$PatternLength){
    $start=[Math]::Max(0,$Offset-24);$end=[Math]::Min($Data.Length,$Offset+$PatternLength+24)
    [BitConverter]::ToString($Data[$start..($end-1)])
}

$deadline=(Get-Date).AddSeconds($WaitSeconds);$target=$null;$handle=[IntPtr]::Zero
while((Get-Date) -lt $deadline -and !$target){
    foreach($candidate in Get-Process swtor-emu -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending){
        $candidateHandle=[GnarlsMapMemory]::OpenProcess(0x410,$false,$candidate.Id)
        if($candidateHandle -eq [IntPtr]::Zero){continue}
        try{$base=$candidate.MainModule.BaseAddress.ToInt64()}catch{[void][GnarlsMapMemory]::CloseHandle($candidateHandle);continue}
        $area=Read-U32 $candidateHandle ($base+0x1096E20)
        if($area){$target=$candidate;$handle=$candidateHandle;break}
        [void][GnarlsMapMemory]::CloseHandle($candidateHandle)
    }
    if(!$target){Start-Sleep -Milliseconds 200}
}
if(!$target){throw 'No swtor-emu process with a non-null area pointer appeared.'}

try{
    $base=$target.MainModule.BaseAddress.ToInt64();$stableCount=0;$snapshot=$null
    while((Get-Date) -lt $deadline -and -not $target.HasExited){
        $area=Read-U32 $handle ($base+0x1096E20)
        $primary=if($area){Read-U32 $handle ($area+0x2A0)}else{$null}
        $secondary=if($area){Read-U32 $handle ($area+0x400)}else{$null}
        $pState=if($primary){Read-U32 $handle ($primary+0x8C)}else{$null}
        $sState=if($secondary){Read-U32 $handle ($secondary+0x8C)}else{$null}
        $marker=$false
        if(Test-Path -LiteralPath $MarkerLog){$marker=[IO.File]::ReadAllText($MarkerLog).Contains('gnarls_new')}
        if($marker -and $primary -and $secondary -and $pState -eq 3 -and $sState -eq 3){$stableCount++}else{$stableCount=0}
        if($stableCount -ge 3){
            $snapshot=[pscustomobject]@{Area=$area;Primary=$primary;Secondary=$secondary;PrimaryState=$pState;SecondaryState=$sState}
            break
        }
        Start-Sleep -Seconds 1
    }
    if($null -eq $snapshot){throw 'Stable Tython pointers and emitted gnarls_new marker were not observed before timeout.'}

    $needles=[ordered]@{
        NodeIdLE=[BitConverter]::GetBytes([uint64]0x0000001AC6F6DC94)
        NodeIdPacked=[byte[]](0xCC,0x1A,0xC6,0xF6,0xDC,0x94)
        GnarlsAscii=[Text.Encoding]::ASCII.GetBytes('gnarls_new')
    }
    $matches=New-Object Collections.Generic.List[object]
    $regions=New-Object Collections.Generic.List[object]
    $seen=New-Object 'Collections.Generic.HashSet[string]'
    [long]$address=0x10000;[long]$limit=0x7FFF0000;$mbiSize=[Runtime.InteropServices.Marshal]::SizeOf([type][GnarlsMapMemory+MBI])
    while($address -lt $limit){
        $mbi=New-Object GnarlsMapMemory+MBI
        $queried=[GnarlsMapMemory]::VirtualQueryEx($handle,[IntPtr]::new($address),[ref]$mbi,[UIntPtr]::new($mbiSize)).ToUInt64()
        if($queried -eq 0){break}
        $regionBase=$mbi.BaseAddress.ToInt64();$regionSize=[long]$mbi.RegionSize.ToUInt64();$next=$regionBase+$regionSize
        if($next -le $address){break}
        $basicProtect=$mbi.Protect -band 0xFF
        $readable=($mbi.State -eq 0x1000 -and ($mbi.Protect -band 0x100) -eq 0 -and $basicProtect -in @(0x02,0x04,0x20,0x40,0x80))
        if($readable){
            $regions.Add([pscustomobject]@{Base=(Hex $regionBase);Size=$regionSize;Protect=('0x{0:X}' -f $mbi.Protect);Type=('0x{0:X}' -f $mbi.Type)})
            [long]$cursor=$regionBase;$carry=New-Object byte[] 0;$maxNeedle=10
            while($cursor -lt $next){
                $want=[int][Math]::Min(1048576,$next-$cursor);$part=Read-Bytes $handle $cursor $want
                if($null -eq $part){$cursor+=$want;$carry=New-Object byte[] 0;continue}
                $combined=New-Object byte[] ($carry.Length+$part.Length)
                if($carry.Length){[Array]::Copy($carry,0,$combined,0,$carry.Length)}
                [Array]::Copy($part,0,$combined,$carry.Length,$part.Length)
                $combinedBase=$cursor-$carry.Length
                foreach($entry in $needles.GetEnumerator()){
                    foreach($offset in [GnarlsMapMemory]::FindAll($combined,$entry.Value)){
                        $hit=$combinedBase+$offset;$key="$($entry.Key):$hit"
                        if($seen.Add($key)){$matches.Add([pscustomobject]@{Kind=$entry.Key;Address=(Hex $hit);RegionBase=(Hex $regionBase);RegionSize=$regionSize;Snippet=(Get-Snippet $combined $offset $entry.Value.Length)})}
                    }
                }
                $keep=[Math]::Min($maxNeedle-1,$combined.Length)
                $carry=if($keep){[byte[]]$combined[($combined.Length-$keep)..($combined.Length-1)]}else{New-Object byte[] 0}
                $cursor+=$part.Length
                if($part.Length -lt $want){break}
            }
        }
        $address=$next
    }

    $links=New-Object Collections.Generic.List[object]
    foreach($selected in @(@{Name='Primary';Address=[uint32]$snapshot.Primary},@{Name='Secondary';Address=[uint32]$snapshot.Secondary})){
        $data=Read-Bytes $handle $selected.Address 4096
        if($null -eq $data){continue}
        [IO.File]::WriteAllBytes((Join-Path $OutputDirectory ("selected-{0}.bin" -f $selected.Name.ToLowerInvariant())),$data)
        foreach($entry in $needles.GetEnumerator()){
            foreach($offset in [GnarlsMapMemory]::FindAll($data,$entry.Value)){$links.Add([pscustomobject]@{Selected=$selected.Name;SelectedAddress=(Hex $selected.Address);Relation="contains-$($entry.Key)";Offset=('0x{0:X}' -f $offset);Target=''})}
        }
        foreach($match in $matches){
            $targetAddress=[Convert]::ToUInt32($match.Address.Substring(2),16);$pointer=[BitConverter]::GetBytes($targetAddress)
            foreach($offset in [GnarlsMapMemory]::FindAll($data,$pointer)){$links.Add([pscustomobject]@{Selected=$selected.Name;SelectedAddress=(Hex $selected.Address);Relation="points-to-$($match.Kind)";Offset=('0x{0:X}' -f $offset);Target=$match.Address})}
        }
    }
    $matches | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'matches.csv') -NoTypeInformation -Encoding utf8
    $regions | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'regions.csv') -NoTypeInformation -Encoding utf8
    $links | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'selected-links.csv') -NoTypeInformation -Encoding utf8
    $metadata=[ordered]@{CapturedAt=(Get-Date -Format o);PID=$target.Id;ModuleBase=(Hex $base);GlobalAreaPointer=(Hex ($base+0x1096E20));Area=(Hex $snapshot.Area);Primary=(Hex $snapshot.Primary);PrimaryState=$snapshot.PrimaryState;Secondary=(Hex $snapshot.Secondary);SecondaryState=$snapshot.SecondaryState;ProcessAccess='0x410 query/read';Needles=@{NodeIdLE='94 DC F6 C6 1A 00 00 00';NodeIdPacked='CC 1A C6 F6 DC 94';GnarlsAscii='67 6E 61 72 6C 73 5F 6E 65 77'};MatchCount=$matches.Count;SelectedLinkCount=$links.Count}
    $metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'metadata.json') -Encoding utf8
    Get-ChildItem -LiteralPath $OutputDirectory -File | ForEach-Object {[pscustomobject]@{Path=$_.FullName;Bytes=$_.Length;SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}} | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'manifest.csv') -NoTypeInformation -Encoding utf8
    "Captured native identity map: matches=$($matches.Count) selected-links=$($links.Count)"
} finally {
    if($handle -ne [IntPtr]::Zero){[void][GnarlsMapMemory]::CloseHandle($handle)}
}
