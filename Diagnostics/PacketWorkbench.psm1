Set-StrictMode -Version 2.0

function ConvertFrom-PacketHex {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Hex)

    $clean = $Hex -replace '(?i)0x', '' -replace '[^0-9a-fA-F]', ''
    if (($clean.Length % 2) -ne 0) {
        throw 'Hex input contains an incomplete byte.'
    }

    [byte[]]$bytes = New-Object byte[] ($clean.Length / 2)
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        $bytes[$i] = [Convert]::ToByte($clean.Substring($i * 2, 2), 16)
    }
    return $bytes
}

function ConvertTo-PacketHex {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Bytes,
        [int]$Offset = 0,
        [int]$Count = -1
    )

    if ($Offset -lt 0 -or $Offset -gt $Bytes.Length) {
        throw "Offset $Offset is outside a $($Bytes.Length)-byte buffer."
    }
    if ($Count -lt 0) { $Count = $Bytes.Length - $Offset }
    if ($Count -lt 0 -or $Offset + $Count -gt $Bytes.Length) {
        throw "Range $Offset+$Count is outside a $($Bytes.Length)-byte buffer."
    }
    if ($Count -eq 0) { return '' }
    return [BitConverter]::ToString($Bytes, $Offset, $Count).Replace('-', ' ')
}

function Get-UInt32LE {
    param([byte[]]$Bytes, [int]$Offset)
    if ($Offset -lt 0 -or $Offset + 4 -gt $Bytes.Length) {
        throw "Cannot read UInt32 at offset $Offset from $($Bytes.Length) bytes."
    }
    return [uint32](([uint32]$Bytes[$Offset]) -bor
        (([uint32]$Bytes[$Offset + 1]) -shl 8) -bor
        (([uint32]$Bytes[$Offset + 2]) -shl 16) -bor
        (([uint32]$Bytes[$Offset + 3]) -shl 24))
}

function Import-ProtocolEvidence {
    [CmdletBinding()]
    param([string]$Path = (Join-Path $PSScriptRoot 'Protocol-Evidence.csv'))

    if (!(Test-Path -LiteralPath $Path)) {
        throw "Protocol evidence registry not found: $Path"
    }
    return @(Import-Csv -LiteralPath $Path)
}

function Get-RoutedPacketReport {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Bytes,
        [string]$RegistryPath = (Join-Path $PSScriptRoot 'Protocol-Evidence.csv')
    )

    if ($Bytes.Length -lt 4) {
        return [pscustomobject]@{
            Valid = $false
            Error = 'Plaintext packet is shorter than the four-byte opcode.'
            Length = $Bytes.Length
            Hex = ConvertTo-PacketHex $Bytes
        }
    }

    [uint32]$opcode = Get-UInt32LE $Bytes 0
    $opcodeText = ('0x{0:X8}' -f $opcode)
    $evidence = @(Import-ProtocolEvidence -Path $RegistryPath |
        Where-Object { $_.Opcode -ieq $opcodeText })

    $hasRouting = $Bytes.Length -ge 8
    [uint32]$component = 0
    [uint16]$source = 0
    [uint16]$destination = 0
    if ($hasRouting) {
        $component = Get-UInt32LE $Bytes 4
        $source = [uint16]($component -shr 16)
        $destination = [uint16]($component -band 0xFFFF)
    }

    $bodyOffset = if ($hasRouting) { 8 } else { 4 }
    $bodyLength = $Bytes.Length - $bodyOffset
    return [pscustomobject]@{
        Valid = $true
        Length = $Bytes.Length
        Opcode = $opcodeText
        Name = if ($evidence.Count) { $evidence[0].Name } else { 'Unregistered' }
        Direction = if ($evidence.Count) { $evidence[0].Direction } else { 'Unknown' }
        Family = if ($evidence.Count) { $evidence[0].Family } else { 'Unknown' }
        Confidence = if ($evidence.Count) { $evidence[0].Confidence } else { 'Unregistered' }
        Evidence = if ($evidence.Count) { $evidence[0].Evidence } else { '' }
        Envelope = if ($evidence.Count) { $evidence[0].Envelope } else { '' }
        BodySchema = if ($evidence.Count) { $evidence[0].BodySchema } else { '' }
        Component = if ($hasRouting) { '0x{0:X8}' -f $component } else { $null }
        SourceHandle = if ($hasRouting) { '0x{0:X4}' -f $source } else { $null }
        DestinationHandle = if ($hasRouting) { '0x{0:X4}' -f $destination } else { $null }
        BodyOffset = $bodyOffset
        BodyLength = $bodyLength
        BodyHex = ConvertTo-PacketHex $Bytes $bodyOffset $bodyLength
        RawHex = ConvertTo-PacketHex $Bytes
    }
}

function Read-HeroPackedUnsigned {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Bytes,
        [Parameter(Mandatory=$true)][ref]$Offset,
        [ValidateSet(1,5)][int]$TransportVersion = 5
    )

    $start = [int]$Offset.Value
    if ($start -lt 0 -or $start -ge $Bytes.Length) {
        throw "Packed unsigned value starts outside the buffer at offset $start."
    }
    $token = $Bytes[$start]
    $Offset.Value = $start + 1

    $threshold = if ($TransportVersion -gt 1) { 0xC0 } else { 0x80 }
    $base = if ($TransportVersion -gt 1) { 0xC7 } else { 0xAF }
    $max = if ($TransportVersion -gt 1) { 0xCF } else { 0xBF }
    if ($token -lt $threshold) {
        return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=('0x{0:X2}' -f $token); Length=1; Value=[uint64]$token }
    }
    if ($token -lt ($base + 1) -or $token -gt $max) {
        throw ('Invalid transport-version-{0} packed unsigned token 0x{1:X2} at offset {2}.' -f $TransportVersion,$token,$start)
    }

    $length = [int]$token - $base
    if ($length -lt 1 -or $length -gt 8 -or $Offset.Value + $length -gt $Bytes.Length) {
        throw "Packed unsigned token at offset $start requires $length unavailable bytes."
    }
    [uint64]$value = 0
    for ($i = 0; $i -lt $length; $i++) {
        $value = ($value -shl 8) -bor $Bytes[$Offset.Value]
        $Offset.Value++
    }
    return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=('0x{0:X2}' -f $token); Length=(1+$length); Value=$value }
}

function Read-HeroPackedSigned {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Bytes,
        [Parameter(Mandatory=$true)][ref]$Offset,
        [ValidateSet(1,5)][int]$TransportVersion = 5
    )

    $start = [int]$Offset.Value
    if ($start -lt 0 -or $start -ge $Bytes.Length) {
        throw "Packed signed value starts outside the buffer at offset $start."
    }
    $token = $Bytes[$start]
    $Offset.Value = $start + 1
    $threshold = if ($TransportVersion -gt 1) { 0xC0 } else { 0x80 }
    if ($token -lt $threshold) {
        return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=('0x{0:X2}' -f $token); Length=1; Value=[int64]$token }
    }

    if ($TransportVersion -gt 1) {
        if ($token -eq 0xD0) {
            return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token='0xD0'; Length=1; Value=[int64]::MinValue }
        }
        if ($token -ge 0xC8 -and $token -le 0xCF) {
            $length = [int]$token - 0xC7
            $negative = $false
        } elseif ($token -ge 0xC0 -and $token -le 0xC7) {
            $length = [int]$token - 0xBF
            $negative = $true
        } else {
            throw ('Invalid transport-version-5 packed signed token 0x{0:X2} at offset {1}.' -f $token,$start)
        }
    } else {
        throw 'Transport-version-1 signed decoding is not exposed by this workbench; use Tools/Hero directly.'
    }

    if ($length -lt 1 -or $length -gt 8 -or $Offset.Value + $length -gt $Bytes.Length) {
        throw "Packed signed token at offset $start requires $length unavailable bytes."
    }
    [uint64]$magnitude = 0
    for ($i = 0; $i -lt $length; $i++) {
        $magnitude = ($magnitude -shl 8) -bor $Bytes[$Offset.Value]
        $Offset.Value++
    }
    if ($magnitude -gt [uint64][int64]::MaxValue) {
        throw "Packed signed magnitude at offset $start exceeds Int64."
    }
    [int64]$value = [int64]$magnitude
    if ($negative) { $value = -$value }
    return [pscustomobject]@{ Offset=$start; End=$Offset.Value; Token=('0x{0:X2}' -f $token); Length=(1+$length); Value=$value }
}

function Get-HeroPackedSequence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Bytes,
        [int]$Offset = 0,
        [ValidateSet('Unsigned','Signed')][string]$Kind = 'Unsigned',
        [ValidateSet(1,5)][int]$TransportVersion = 5,
        [int]$MaximumValues = 256
    )

    if ($Offset -lt 0 -or $Offset -gt $Bytes.Length) {
        throw "Packed stream offset $Offset is outside $($Bytes.Length) bytes."
    }
    $cursor = $Offset
    $values = @()
    $failure = $null
    while ($cursor -lt $Bytes.Length -and $values.Count -lt $MaximumValues) {
        $before = $cursor
        try {
            if ($Kind -eq 'Signed') {
                $item = Read-HeroPackedSigned -Bytes $Bytes -Offset ([ref]$cursor) -TransportVersion $TransportVersion
            } else {
                $item = Read-HeroPackedUnsigned -Bytes $Bytes -Offset ([ref]$cursor) -TransportVersion $TransportVersion
            }
            $values += $item
        } catch {
            $cursor = $before
            $failure = $_.Exception.Message
            break
        }
    }
    return [pscustomobject]@{
        Kind = $Kind
        TransportVersion = $TransportVersion
        StartOffset = $Offset
        EndOffset = $cursor
        Remaining = $Bytes.Length - $cursor
        Complete = ($cursor -eq $Bytes.Length)
        Failure = $failure
        Values = $values
    }
}

function Compare-PacketBytes {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][byte[]]$Left,
        [Parameter(Mandatory=$true)][byte[]]$Right
    )

    $limit = [Math]::Max($Left.Length, $Right.Length)
    $differences = @()
    for ($i = 0; $i -lt $limit; $i++) {
        $leftValue = if ($i -lt $Left.Length) { '0x{0:X2}' -f $Left[$i] } else { '<missing>' }
        $rightValue = if ($i -lt $Right.Length) { '0x{0:X2}' -f $Right[$i] } else { '<missing>' }
        if ($leftValue -ne $rightValue) {
            $differences += [pscustomobject]@{ Offset=$i; Left=$leftValue; Right=$rightValue }
        }
    }
    return [pscustomobject]@{
        LeftLength = $Left.Length
        RightLength = $Right.Length
        Equal = ($differences.Count -eq 0)
        DifferenceCount = $differences.Count
        Differences = $differences
    }
}

Export-ModuleMember -Function ConvertFrom-PacketHex,ConvertTo-PacketHex,Import-ProtocolEvidence,Get-RoutedPacketReport,Read-HeroPackedUnsigned,Read-HeroPackedSigned,Get-HeroPackedSequence,Compare-PacketBytes

