param([Parameter(Mandatory=$true)][string]$CaptureDirectory)
$ErrorActionPreference='Stop'
$cache=Join-Path (Split-Path $PSScriptRoot -Parent) 'GomCompatibility\ResourceCacheApril2012\scripts'
$cases=@(
    @{Kind='PhaseInfoDestroy';File='65A4399D0102A007.scpt';Offset=0xB78},
    @{Kind='UpdateGateway';File='C10C1F8290BE3551.scpt';Offset=0x32E3},
    @{Kind='PlayerPhaseCreate';File='9308DE76F6AAF774.scpt';Offset=0xB1},
    @{Kind='PlayerPhaseDestroy';File='9308DE76F6AAF774.scpt';Offset=0x3A1}
)
$results=foreach($case in $cases){
    $raw=[IO.File]::ReadAllBytes((Join-Path $cache $case.File))
    $payload=New-Object byte[] ($raw.Length-37);[byte]$key=0x35
    for($i=0;$i -lt $payload.Length;$i++){$payload[$i]=$raw[$i+37] -bxor $key;$key=[byte](($key+0x36) -band 0xFF)}
    $expected=[byte[]]$payload[$case.Offset..($case.Offset+127)]
    $mask=New-Object bool[] 128
    for($i=0;$i -lt 124;$i++){
        # Only mask canonical unresolved external CALL rel32 operands observed
        # in the pinned resource. Do not wildcard all byte differences.
        if($expected[$i] -eq 0xE8 -and $expected[$i+1] -eq 0xFC -and $expected[$i+2] -eq 0xFF -and $expected[$i+3] -eq 0xFF -and $expected[$i+4] -eq 0xFF){
            foreach($j in 1..4){$mask[$i+$j]=$true}
        }
    }
    foreach($file in Get-ChildItem -LiteralPath $CaptureDirectory -Filter "*-$($case.Kind)-*.bin"){
        $actual=[IO.File]::ReadAllBytes($file.FullName)
        $differences=@(for($i=0;$i -lt 128;$i++){if(!$mask[$i] -and $expected[$i] -ne $actual[$i]){'{0:X2}:{1:X2}/{2:X2}' -f $i,$expected[$i],$actual[$i]}})
        [pscustomobject]@{Kind=$case.Kind;Candidate=$file.Name;PrefixBytes=128;MaskedBytes=@($mask|Where-Object {$_}).Count;Mismatches=$differences.Count;FirstDifferences=(($differences|Select-Object -First 12)-join ';')}
    }
}
$results | Export-Csv (Join-Path $CaptureDirectory 'prefix-comparison.csv') -NoTypeInformation
$results | Format-Table -AutoSize
