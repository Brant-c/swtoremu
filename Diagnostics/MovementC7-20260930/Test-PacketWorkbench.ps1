$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PacketWorkbench.psm1') -Force

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) {
        throw "$Message expected=[$Expected] actual=[$Actual]"
    }
}

[byte[]]$movement = ConvertFrom-PacketHex 'D5 6A 11 61 08 00 B3 65 C5 00 00 00 00 00 80 3F 00 00 00 C0 00 00 40 40'
$report = Get-RoutedPacketReport -Bytes $movement
Assert-Equal $true $report.Valid 'movement validity'
Assert-Equal '0x61116AD5' $report.Opcode 'little-endian opcode check'
Assert-Equal 'CMsg61116AD5' $report.Name 'movement registry check'
Assert-Equal '0x65B30008' $report.Component 'component check'
Assert-Equal '0x65B3' $report.SourceHandle 'source handle check'
Assert-Equal '0x0008' $report.DestinationHandle 'destination handle check'
Assert-Equal 8 $report.BodyOffset 'body offset check'
Assert-Equal 16 $report.BodyLength 'body length check'

[byte[]]$known = ConvertFrom-PacketHex 'B0 CD 6D F9 08 00 B3 65 01'
$knownReport = Get-RoutedPacketReport -Bytes $known
Assert-Equal '0xF96DCDB0' $knownReport.Opcode 'known opcode check'
Assert-Equal 'CMsgF96DCDB0' $knownReport.Name 'registry lookup check'
Assert-Equal 'Captured' $knownReport.Confidence 'registry confidence check'

$rows = @(Import-ProtocolEvidence)
$allowedConfidence = @('Captured','Client-derived','Behavior-verified','Hypothesis')
foreach ($row in $rows) {
    if ($row.Confidence -notin $allowedConfidence) {
        throw "Registry row $($row.Opcode) has invalid confidence $($row.Confidence)."
    }
}
$duplicates = @($rows | Group-Object Opcode,Direction | Where-Object Count -gt 1)
Assert-Equal 0 $duplicates.Count 'registry opcode/direction uniqueness'

$offset = 0
[byte[]]$packed = ConvertFrom-PacketHex '05 C8 C0 C9 01 00 CF 01 02 03 04 05 06 07 08'
$v1 = Read-HeroPackedUnsigned -Bytes $packed -Offset ([ref]$offset)
$v2 = Read-HeroPackedUnsigned -Bytes $packed -Offset ([ref]$offset)
$v3 = Read-HeroPackedUnsigned -Bytes $packed -Offset ([ref]$offset)
$v4 = Read-HeroPackedUnsigned -Bytes $packed -Offset ([ref]$offset)
Assert-Equal 5 $v1.Value 'inline packed value'
Assert-Equal 192 $v2.Value 'one-byte packed value'
Assert-Equal 256 $v3.Value 'two-byte packed value'
Assert-Equal ([uint64]0x0102030405060708) $v4.Value 'eight-byte packed value'
Assert-Equal $packed.Length $offset 'packed cursor completion'

$truncatedRejected = $false
try {
    $truncatedOffset = 0
    $null = Read-HeroPackedUnsigned -Bytes ([byte[]](0xCF,0x01)) -Offset ([ref]$truncatedOffset)
} catch { $truncatedRejected = $true }
Assert-Equal $true $truncatedRejected 'truncated packed value rejection'

$signedOffset = 0
[byte[]]$signed = ConvertFrom-PacketHex 'C0 05 C8 05 D0'
$s1 = Read-HeroPackedSigned -Bytes $signed -Offset ([ref]$signedOffset)
$s2 = Read-HeroPackedSigned -Bytes $signed -Offset ([ref]$signedOffset)
$s3 = Read-HeroPackedSigned -Bytes $signed -Offset ([ref]$signedOffset)
Assert-Equal -5 $s1.Value 'negative packed value'
Assert-Equal 5 $s2.Value 'positive packed value'
Assert-Equal ([int64]::MinValue) $s3.Value 'minimum packed value'

$comparison = Compare-PacketBytes -Left ([byte[]](1,2,3)) -Right ([byte[]](1,9,3,4))
Assert-Equal $false $comparison.Equal 'comparison equality'
Assert-Equal 2 $comparison.DifferenceCount 'comparison count'
Assert-Equal 1 $comparison.Differences[0].Offset 'first comparison offset'
Assert-Equal 3 $comparison.Differences[1].Offset 'length comparison offset'

'PASS: packet hex, routed envelope, registry integrity, Hero packed unsigned/signed bounds, and byte comparison.'


