param(
    [string]$CrtDirectory = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\AreaServer\CRT'),
    [string]$ServerLog = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug\NexusToR.log')
)

$ErrorActionPreference = 'Stop'

# This is the TransportVersion 5 unsigned-integer grammar from
# Parser/SWTORParser/Hero/PackedStream.cs. Multi-byte values are stored
# most-significant byte first by PackedStream.ReadPacked.
function Read-PackedUInt64 {
    param([byte[]]$Data, [ref]$Offset)

    if ($Offset.Value -ge $Data.Length) { throw 'end of payload' }
    [int]$start = $Offset.Value
    [int]$token = $Data[$Offset.Value++]
    if ($token -lt 192) {
        return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=$token; Value=[uint64]$token }
    }
    if ($token -lt 200 -or $token -gt 207) {
        throw ('invalid v5 packed token 0x{0:X2} at offset {1}' -f $token,$start)
    }
    [int]$count = $token - 199
    if ($Offset.Value + $count -gt $Data.Length) { throw 'truncated packed integer' }
    [uint64]$value = 0
    for ($i=0; $i -lt $count; $i++) {
        $value = ($value -shl 8) -bor $Data[$Offset.Value++]
    }
    return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=$token; Value=$value }
}

function Format-Hex([byte[]]$Data) {
    return [BitConverter]::ToString($Data).Replace('-', ' ')
}

function Decode-RpcBlob {
    param([string]$Direction, [byte[]]$Blob)

    # The repository's old AreaHandler tried to feed this entire object to the
    # packed-integer reader. That works for CF (an eight-byte packed target
    # reference), but C7 is a reserved RPC-object marker followed by a
    # four-byte little-endian call identifier. Treat the two shapes separately
    # so target identity is not confused with procedure/correlation identity.
    if ($Blob.Length -ge 5 -and $Blob[0] -eq 0xC7) {
        return [pscustomobject]@{
            Direction = $Direction
            Length = $Blob.Length
            Shape = 'C7 call'
            Target = ''
            Call = ('0x{0:X8}' -f [BitConverter]::ToUInt32($Blob,1))
            Arguments = if ($Blob.Length -gt 5) { Format-Hex $Blob[5..($Blob.Length-1)] } else { '' }
            Status = 'decoded-rpc-object'
        }
    }

    $offset = 0
    try {
        $target = Read-PackedUInt64 $Blob ([ref]$offset)
        [pscustomobject]@{
            Direction = $Direction
            Length = $Blob.Length
            Shape = 'packed target'
            Target = ('0x{0:X16}' -f $target.Value)
            Call = ''
            Arguments = if ($offset -lt $Blob.Length) { Format-Hex $Blob[$offset..($Blob.Length-1)] } else { '' }
            Status = 'decoded-v5'
        }
    } catch {
        [pscustomobject]@{
            Direction = $Direction
            Length = $Blob.Length
            Shape = 'unknown'
            Target = ''
            Call = ''
            Arguments = Format-Hex $Blob
            Status = $_.Exception.Message
        }
    }
}

$serverRpcHex = @(
    'CF2B7E42022E10030D0600',
    'CF75DCE5C30311A4C8',
    'C74F7741BDE7FF953902050205',
    'C775A11AAF776506240301',
    'C70C19E0BE7ADB8173',
    'CF65F1369130110385080202000007020000080204000008020600000802070000',
    'C707E54B657A208683',
    'C707E54B654836A3C60801030000',
    'CF057743E1C6B9C09A0200'
)

$rpcRows = [System.Collections.Generic.List[object]]::new()
foreach ($hex in $serverRpcHex) {
    [byte[]]$blob = for ($i=0; $i -lt $hex.Length; $i+=2) { [Convert]::ToByte($hex.Substring($i,2),16) }
    $rpcRows.Add((Decode-RpcBlob 'server->client' $blob))
}

# Pull the distinct client RPC frames from the existing diagnostic log. The
# packet body begins after the area component and starts with a little-endian
# Int32 blob length.
if (Test-Path -LiteralPath $ServerLog) {
    $seen = @{}
    foreach ($line in Get-Content -LiteralPath $ServerLog) {
        if ($line -notmatch 'AREA-POLL CMsg(?:F96DCDB0|4A765897).*head=([0-9A-F-]+)') { continue }
        $head = $Matches[1]
        if ($seen.ContainsKey($head)) { continue }
        $seen[$head] = $true
        [byte[]]$body = $head.Split('-') | ForEach-Object { [Convert]::ToByte($_,16) }
        if ($body.Length -lt 5) { continue }
        [int]$length = [BitConverter]::ToInt32($body,0)
        if ($length -lt 0 -or 4+$length -gt $body.Length) { continue }
        [byte[]]$blob = $body[4..(3+$length)]
        $rpcRows.Add((Decode-RpcBlob 'client->server' $blob))
    }
}

$crtRows = Get-ChildItem -LiteralPath $CrtDirectory -Filter '*.acrt' | ForEach-Object {
    [byte[]]$data = [IO.File]::ReadAllBytes($_.FullName)
    [pscustomobject]@{
        Fixture = $_.Name
        Bytes = $data.Length
        Stream = if ($data.Length -ge 4) { '0x{0:X8}' -f [BitConverter]::ToUInt32($data,0) } else { '' }
        CapturedClassRefs = ([regex]::Matches(([BitConverter]::ToString($data).Replace('-','')), 'CF4000010E218A839C')).Count
    }
} | Sort-Object { [int]([regex]::Match($_.Fixture,'\.(\d+)\.acrt$').Groups[1].Value) }

'=== RPC blobs through the repository PackedStream v5 grammar ==='
$rpcRows | Sort-Object Direction,Shape,Target,Call,Length,Arguments -Unique | Format-Table -AutoSize
''
'=== CRT fixture inventory ==='
$crtRows | Format-Table -AutoSize
''
'Interpretation: CF introduces an eight-byte packed target reference. C7 is a reserved RPC-object marker followed by a four-byte little-endian call identifier. Neither complete blob is a string result key.'
