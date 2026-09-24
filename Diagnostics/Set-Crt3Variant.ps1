<#
.SYNOPSIS
    Reversibly writes one candidate variant of the tython CRT3 area fixture.

.DESCRIPTION
    The tython CRT3 fixture
    (SharpServer/bin/Debug/AreaServer/CRT/tython_blockout-...-1.3.acrt)
    is the input the client is reading when world entry throws
    G::SerializationException("Incorrect token found in input stream").

    The reference server calls File.ReadAllBytes for each CRT it sends
    (AreaServer/CRT.cs), so a fixture change takes effect on the next
    world-entry attempt with no server rebuild and no server restart.

    Variants
      Status          Report current bytes and hash. Changes nothing.
      Restore         Write the recorded original byte-for-byte.
      HeaderSequence  Original, then set the leading 32-bit replication
                      sequence to the in-sequence value 0x001B5014
                      (CRT2 = 0x001B5013, CRT4 = 0x001B5015). CRT3 currently
                      holds 0x000DAB37, far outside that run.

    Scope: this tool rewrites only this one fixture. It never touches the
    client, the server executable, or any other fixture, and Restore never
    depends on an external backup file.
#>
[CmdletBinding()]
param(
    [ValidateSet('Status', 'Restore', 'HeaderSequence', 'VectorComplete', 'TailToken00')]
    [string]$Variant = 'Status'
)

$ErrorActionPreference = 'Stop'

$FixtureDir = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT'
$FixtureName = 'tython_blockout-4611686019869492753-1.3.acrt'
$FixturePath = Join-Path $FixtureDir $FixtureName

# Recorded original of this fixture, verified against the pre-experiment backup.
$OriginalHex = '37 ab 0d 00 00 00 00 00 01 01 cc 17 bf ad f6 ac aa cf 40 00 00 12 33 8b 5a cb 00 05 07 19 01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00 cf 40 00 01 0e 21 8a 83 9c c0'
$OriginalSha256 = '3E79B4C94FADFAD09DB854B2979027BB2187D230CC2CB37493DD140D86C3CFBA'

# In-sequence value CRT3 is missing: CRT2 = 0x001B5013, CRT4 = 0x001B5015.
$HeaderSequenceBytes = [byte[]]@(0x14, 0x50, 0x1b, 0x00)

function Get-OriginalBytes {
    (($OriginalHex -split '\s+') | ForEach-Object { [Convert]::ToByte($_, 16) })
}

function Get-Hex([byte[]]$Bytes) {
    (($Bytes | ForEach-Object { $_.ToString('x2') }) -join ' ')
}

function Show-State([string]$Label) {
    $bytes = [IO.File]::ReadAllBytes($FixturePath)
    $hash = (Get-FileHash $FixturePath -Algorithm SHA256).Hash
    $original = (Get-OriginalBytes)
    $isOriginal = ((Get-Hex $bytes) -eq (Get-Hex $original))
    $u32 = [BitConverter]::ToUInt32($bytes, 0)
    $tag = if ($isOriginal) { 'recorded original' } else { 'MODIFIED' }
    "{0,-16} len={1,-3} sha={2}" -f $Label, $bytes.Length, $hash
    "{0,-16} head32={1}  seq32=0x{2:X8} ({2})  {3}" -f '', (Get-Hex $bytes[0..3]), $u32, $tag
}

if (-not (Test-Path $FixturePath)) {
    throw "Fixture not found: $FixturePath"
}

$original = Get-OriginalBytes
if ($original.Length -ne 55) { throw 'Recorded original is not 55 bytes.' }
if ((Get-FileHash -InputStream ([IO.MemoryStream]::new($original)) -Algorithm SHA256).Hash -ne $OriginalSha256) {
    throw 'Recorded original does not match its known SHA256.'
}

if ($Variant -eq 'Status') {
    Show-State 'status'
    'No file was written.'
    return
}

$target = [byte[]]$original
if ($Variant -eq 'HeaderSequence') {
    [Array]::Copy($HeaderSequenceBytes, 0, $target, 0, 4)
}

# VectorComplete: the world-entry dump shows the style-7 reader starting a
# 12-byte 3-component value at payload offset 15 with only 10 bytes left
# (cursor 25/25, remaining=10, needed=12). Its third component was latched
# as 9c c0 00 00. The capture therefore lost exactly the final 2 bytes.
# Complete the payload with those 2 bytes and bump the declared length
# 0x19 (25) -> 0x1B (27). All other bytes stay original.
if ($Variant -eq 'VectorComplete') {
    if ($target[29] -ne 0x19) { throw ("Unexpected payload length byte: {0:X2}" -f $target[29]) }
    $target[29] = 0x1B
    $target = $target + [byte[]]@(0x00, 0x00)
}

# TailToken00: the style-7 reader consumes all 25 bytes and throws on the
# final token c0 (=192), which is in the invalid token gap (192-199) of the
# TransportVersion-5 PackedStream grammar. The same payload's earlier class
# reference (cf ff 5f 18 ...) is followed by 00 and parses cleanly; no healthy
# fixture contains the class id followed by c0. Replace the illegal tail
# token with the legal terminator 00. Length stays 25.
if ($Variant -eq 'TailToken00') {
    if ($target[54] -ne 0xC0) { throw ("Unexpected tail byte: {0:X2}" -f $target[54]) }
    $target[54] = 0x00
}


if (-not (Test-Path $FixturePath)) {
    $disabled = "$FixturePath.disabled"
    if (Test-Path $disabled) {
        Rename-Item $disabled $FixturePath
        Write-Host "Re-enabled: $FixtureName"
    }
}

[IO.File]::WriteAllBytes($FixturePath, $target)
Show-State $Variant
"Written: $FixturePath"
