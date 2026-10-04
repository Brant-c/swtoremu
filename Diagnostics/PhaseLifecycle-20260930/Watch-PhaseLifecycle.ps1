param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][string]$HookLog,
    [int]$WaitSeconds = 900
)
$ErrorActionPreference = 'Stop'
if ([IntPtr]::Size -ne 8) { throw 'Use 64-bit PowerShell to read the full 32-bit client address space.' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Refusing to overwrite an existing lifecycle capture.' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null

Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class PhaseLifecycleMemory {
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
   for(int i=0;i<=data.Length-pattern.Length;i++) {
     int j=0; for(;j<pattern.Length;j++) if(data[i+j]!=pattern[j]) break;
     if(j==pattern.Length) hits.Add(i);
   }
   return hits.ToArray();
 }
}
'@

function Read-Bytes([IntPtr]$Handle,[long]$Address,[int]$Length) {
    $buffer=New-Object byte[] $Length; $read=[UIntPtr]::Zero
    if(-not [PhaseLifecycleMemory]::ReadProcessMemory($Handle,[IntPtr]::new($Address),$buffer,[UIntPtr]::new($Length),[ref]$read)){return $null}
    $count=[int]$read.ToUInt64(); if($count -eq $Length){return ,$buffer}; if($count -le 0){return $null}
    $short=New-Object byte[] $count; [Array]::Copy($buffer,$short,$count); return ,$short
}
function Read-U32([IntPtr]$Handle,[long]$Address) {
    $bytes=Read-Bytes $Handle $Address 4
    if($null -eq $bytes -or $bytes.Length -ne 4){return $null}
    [BitConverter]::ToUInt32($bytes,0)
}
function Hex([long]$Value) {'0x{0:X8}' -f [uint32]$Value}
function Read-SharedText([string]$Path) {
    if (!(Test-Path -LiteralPath $Path)) { return '' }
    $stream = [IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,
        [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete)
    try {
        $reader = [IO.StreamReader]::new($stream,[Text.Encoding]::UTF8,$true,4096,$true)
        try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
    } finally { $stream.Dispose() }
}

function Scan-Needles([IntPtr]$Handle,[hashtable]$Needles) {
    $results=New-Object Collections.Generic.List[object]
    $seen=New-Object 'Collections.Generic.HashSet[string]'
    [long]$address=0x10000; [long]$limit=0x100000000
    $mbiSize=[Runtime.InteropServices.Marshal]::SizeOf([type][PhaseLifecycleMemory+MBI])
    while($address -lt $limit) {
        $mbi=New-Object PhaseLifecycleMemory+MBI
        if([PhaseLifecycleMemory]::VirtualQueryEx($Handle,[IntPtr]::new($address),[ref]$mbi,[UIntPtr]::new($mbiSize)).ToUInt64() -eq 0){break}
        $regionBase=$mbi.BaseAddress.ToInt64(); $regionSize=[long]$mbi.RegionSize.ToUInt64(); $next=$regionBase+$regionSize
        if($next -le $address){break}
        $basic=$mbi.Protect -band 0xFF
        $readable=$mbi.State -eq 0x1000 -and ($mbi.Protect -band 0x100) -eq 0 -and $basic -in @(0x02,0x04,0x20,0x40,0x80)
        if($readable) {
            [long]$cursor=$regionBase; $carry=New-Object byte[] 0
            # All identities and inferred pointers in this observer are 4 or 8
            # bytes. Avoid piping byte arrays through PowerShell here: pipeline
            # enumeration flattens them into individual bytes and loses Length.
            $maxLength=8
            while($cursor -lt $next) {
                $want=[int][Math]::Min(1048576,$next-$cursor); $part=Read-Bytes $Handle $cursor $want
                if($null -eq $part){$cursor+=$want;$carry=New-Object byte[] 0;continue}
                $combined=New-Object byte[] ($carry.Length+$part.Length)
                if($carry.Length){[Array]::Copy($carry,0,$combined,0,$carry.Length)}
                [Array]::Copy($part,0,$combined,$carry.Length,$part.Length); $combinedBase=$cursor-$carry.Length
                foreach($entry in $Needles.GetEnumerator()) {
                    foreach($offset in [PhaseLifecycleMemory]::FindAll($combined,$entry.Value)) {
                        $hit=$combinedBase+$offset; $key="$($entry.Key):$hit"
                        if($seen.Add($key)){$results.Add([pscustomobject]@{Kind=$entry.Key;Address=(Hex $hit);RegionBase=(Hex $regionBase);RegionSize=$regionSize;Protect=('0x{0:X}' -f $mbi.Protect);Type=('0x{0:X}' -f $mbi.Type)})}
                    }
                }
                $keep=[Math]::Min($maxLength-1,$combined.Length)
                $carry=if($keep){[byte[]]$combined[($combined.Length-$keep)..($combined.Length-1)]}else{New-Object byte[] 0}
                $cursor+=$part.Length; if($part.Length -lt $want){break}
            }
        }
        $address=$next
    }
    return $results
}

function Assert-PhaseBaseline([object[]]$Objects) {
    $status = foreach ($kind in @('GnarlsControlId','PhaseInfoId','ParentInstanceId','PlayerPhaseDataId')) {
        $found = @($Objects | Where-Object { $_.Kind -eq $kind -and $_.IsHeroNode }).Count
        if ($found -ne 1) { throw "Baseline requires exactly one $kind HeroNode; found $found. No doorway attempt is permitted." }
        [pscustomobject]@{Kind=$kind;HeroNodes=$found}
    }
    return $status
}

function Capture([string]$Label,[IntPtr]$Handle,[long]$ModuleBase) {
    $startedAt = Get-Date -Format o
    $ids=[ordered]@{
        GnarlsControlId=[BitConverter]::GetBytes([uint64]0x0000001AC6F6DC94)
        PhaseInfoId=[BitConverter]::GetBytes([uint64]0x0000001AC6F6DC1F)
        ParentInstanceId=[BitConverter]::GetBytes([uint64]0x0000001AC688C97E)
        PlayerPhaseDataId=[BitConverter]::GetBytes([uint64]0x00000017BFADF6AC)
    }
    $idMatches=Scan-Needles $Handle $ids
    $objects=New-Object Collections.Generic.List[object]
    $heroVtable=[uint32]($ModuleBase+0xD25ECC)
    foreach($match in $idMatches) {
        $hit=[Convert]::ToUInt32($match.Address.Substring(2),16); $candidate=[uint32]($hit-0x18)
        $vtable=Read-U32 $Handle $candidate
        $objects.Add([pscustomobject]@{Snapshot=$Label;Kind=$match.Kind;IdAddress=$match.Address;CandidateBase=(Hex $candidate);Vtable=if($null-ne$vtable){Hex $vtable}else{''};IsHeroNode=($vtable -eq $heroVtable);RegionBase=$match.RegionBase;RegionSize=$match.RegionSize})
    }
    $pointers=[ordered]@{}
    foreach($object in $objects | Where-Object IsHeroNode) {
        $pointers["PointerTo_$($object.Kind)_$($object.CandidateBase)"]=[BitConverter]::GetBytes([Convert]::ToUInt32($object.CandidateBase.Substring(2),16))
    }
    $pointerMatches=if($pointers.Count){Scan-Needles $Handle $pointers}else{@()}
    $idMatches | ForEach-Object {[pscustomobject]@{Snapshot=$Label;Kind=$_.Kind;Address=$_.Address;RegionBase=$_.RegionBase;RegionSize=$_.RegionSize;Protect=$_.Protect;Type=$_.Type}} |
        Export-Csv -LiteralPath (Join-Path $OutputDirectory "$Label-id-matches.csv") -NoTypeInformation -Encoding utf8
    $objects | Export-Csv -LiteralPath (Join-Path $OutputDirectory "$Label-objects.csv") -NoTypeInformation -Encoding utf8
    $pointerMatches | ForEach-Object {[pscustomobject]@{Snapshot=$Label;Kind=$_.Kind;Address=$_.Address;RegionBase=$_.RegionBase;RegionSize=$_.RegionSize;Protect=$_.Protect;Type=$_.Type}} |
        Export-Csv -LiteralPath (Join-Path $OutputDirectory "$Label-pointer-matches.csv") -NoTypeInformation -Encoding utf8
    [pscustomobject]@{Label=$Label;StartedAt=$startedAt;CompletedAt=(Get-Date -Format o);Timing='Sequential full-memory scans, not an atomic snapshot; after labels specify minimum delay before scan start.';IdMatches=$idMatches.Count;HeroNodes=@($objects|Where-Object IsHeroNode).Count;PointerMatches=@($pointerMatches).Count} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory "$Label-summary.json") -Encoding utf8
    return $objects
}

$deadline=(Get-Date).AddSeconds($WaitSeconds); $target=$null; $handle=[IntPtr]::Zero
while((Get-Date)-lt$deadline -and !$target) {
    foreach($candidate in Get-Process swtor-emu -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending) {
        $candidateHandle=[PhaseLifecycleMemory]::OpenProcess(0x410,$false,$candidate.Id); if($candidateHandle-eq[IntPtr]::Zero){continue}
        try{$base=$candidate.MainModule.BaseAddress.ToInt64()}catch{[void][PhaseLifecycleMemory]::CloseHandle($candidateHandle);continue}
        $area=Read-U32 $candidateHandle ($base+0x1096E20)
        if($area){$target=$candidate;$handle=$candidateHandle;break}; [void][PhaseLifecycleMemory]::CloseHandle($candidateHandle)
    }
    if(!$target){Start-Sleep -Milliseconds 200}
}
if(!$target){throw 'No active swtor-emu process with a non-null area pointer appeared.'}

try {
    $base=$target.MainModule.BaseAddress.ToInt64()
    while((Get-Date)-lt$deadline -and -not $target.HasExited) {
        if((Read-SharedText $HookLog).Contains('PhaseLifecycleHook: installed')){break}
        Start-Sleep -Milliseconds 200
    }
    if($target.HasExited -or -not (Read-SharedText $HookLog).Contains('PhaseLifecycleHook: installed')){throw 'Named lifecycle hooks were not installed before timeout.'}
    $before=Capture 'before' $handle $base
    $phaseStatus = @(Assert-PhaseBaseline @($before))
    [pscustomobject]@{ReadyAt=(Get-Date -Format o);PID=$target.Id;ModuleBase=(Hex $base);HookLog=$HookLog;ProcessAccess='0x410 query/read';Baseline=$phaseStatus;RemainingGates='Independently confirm genuine non-overlapping private-memory method addresses, CRT3 enabled, corrected launch server hash, CRT18 suppression and retry disabled before authorizing movement.'} |
        ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'ready.json') -Encoding utf8
    Write-Output ('READY: named hooks report installed; exactly one HeroNode per required identity. Baseline: {0}. Await independent method-address and server/switch checks before any doorway attempt.' -f (($phaseStatus | ForEach-Object { "$($_.Kind)=$($_.HeroNodes)" }) -join ', '))
    while((Get-Date)-lt$deadline -and -not $target.HasExited) {
        if((Read-SharedText $HookLog).Contains('method=phsPhaseInfo.OnReplicationNodeDestroy phase=return')){break}
        Start-Sleep -Milliseconds 20
    }
    if($target.HasExited -or -not (Read-SharedText $HookLog).Contains('method=phsPhaseInfo.OnReplicationNodeDestroy phase=return')){throw 'Named phase-info destroy return was not observed before timeout.'}
    Get-Date -Format o | Set-Content -LiteralPath (Join-Path $OutputDirectory 'destroy-return-observed.txt')
    Start-Sleep -Milliseconds 250
    [void](Capture 'after-250ms' $handle $base)
    Start-Sleep -Seconds 2
    [void](Capture 'after-2s' $handle $base)
    Write-Output 'COMPLETE: post-destroy snapshots preserved.'
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $OutputDirectory 'observer-failure.txt') -Encoding utf8
    throw
} finally {
    if($handle-ne[IntPtr]::Zero){[void][PhaseLifecycleMemory]::CloseHandle($handle)}
    # Preserve partial evidence on a rejected baseline or timeout, too. Read
    # through the same shared-access path used while the hook is logging.
    try {
        (Read-SharedText $HookLog) -split '\r?\n' | Where-Object { $_ -match 'PhaseLifecycleHook|CrtApplyHook' } |
            Set-Content -LiteralPath (Join-Path $OutputDirectory 'hook-lifecycle-window.log') -Encoding utf8
    } catch {
        $_ | Out-String | Set-Content -LiteralPath (Join-Path $OutputDirectory 'log-preservation-failure.txt') -Encoding utf8
    }
    Get-ChildItem -LiteralPath $OutputDirectory -File | Where-Object Name -ne 'manifest.csv' | ForEach-Object {
        [pscustomobject]@{Path=$_.FullName;Bytes=$_.Length;SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
    } | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'manifest.csv') -NoTypeInformation -Encoding utf8
}
