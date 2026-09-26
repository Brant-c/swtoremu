param(
    [string]$DefinitionList = (Join-Path $PSScriptRoot 'GomCompatibility\ResourceCacheApril2012\systemgenerated\scriptdef.list'),
    [string]$ScriptDirectory = (Join-Path $PSScriptRoot 'GomCompatibility\ResourceCacheApril2012\scripts'),
    [string]$ScriptHash
)

$ErrorActionPreference = 'Stop'

function Read-PackedUInt64 {
    param([byte[]]$Data, [ref]$Offset)
    $token = $Data[$Offset.Value]
    $Offset.Value++
    if ($token -lt 192) { return [uint64]$token }
    if ($token -lt 200 -or $token -gt 207) {
        throw ('Invalid packed-stream token 0x{0:X2} at 0x{1:X}' -f $token, ($Offset.Value - 1))
    }
    $length = $token - 199
    [uint64]$value = 0
    for ($index = 0; $index -lt $length; $index++) {
        $value = ($value -shl 8) -bor $Data[$Offset.Value]
        $Offset.Value++
    }
    return $value
}

$data = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $DefinitionList))
if ($data.Length -lt 9 -or [Text.Encoding]::ASCII.GetString($data, 0, 4) -ne 'SDEF') {
    throw 'The input is not an SDEF resource.'
}
$contentVersion = [BitConverter]::ToUInt16($data, 4)
$transportVersion = [BitConverter]::ToUInt16($data, 6)
if ($transportVersion -ne 5) { throw "Unsupported SDEF transport version $transportVersion." }

$offset = 8
$count = Read-PackedUInt64 $data ([ref]$offset)
$records = for ($index = 0; $index -lt $count; $index++) {
    $definitionId = Read-PackedUInt64 $data ([ref]$offset)
    $reserved = Read-PackedUInt64 $data ([ref]$offset)
    $key = Read-PackedUInt64 $data ([ref]$offset)
    $variant = $data[$offset]
    $offset++
    [pscustomobject]@{
        Index = $index
        DefinitionId = $definitionId
        Reserved = $reserved
        Key = $key
        Variant = $variant
    }
}

$scripts = @{}
Get-ChildItem -LiteralPath $ScriptDirectory -Filter '*.scpt' | ForEach-Object {
    $header = [IO.File]::ReadAllBytes($_.FullName)
    if ($header.Length -lt 22 -or [Text.Encoding]::ASCII.GetString($header, 0, 4) -ne 'SCPT') { return }
    # The six-byte SCPT checksum is serialized little-endian into the low 48
    # bits of the SDEF id. Script definitions add the D000 prefix.
    [uint64]$checksum = 0
    for ($i = 21; $i -ge 16; $i--) { $checksum = ($checksum -shl 8) -bor $header[$i] }
    $scriptPrefix = [Convert]::ToUInt64('D000000000000000', 16)
    $id = $scriptPrefix -bor $checksum
    $scripts[$id] = $_
}

$selected = $records
if ($ScriptHash) {
    $target = Get-Item -LiteralPath (Join-Path $ScriptDirectory ($ScriptHash + '.scpt'))
    $selected = $records | Where-Object { $scripts.ContainsKey($_.DefinitionId) -and $scripts[$_.DefinitionId].FullName -eq $target.FullName }
}

'SDEF content={0} transport={1} records={2} unique-definitions={3}' -f `
    $contentVersion, $transportVersion, $records.Count, @($records.DefinitionId | Sort-Object -Unique).Count
'SCPT files={0} matched-definitions={1} unmatched-definitions={2}' -f `
    $scripts.Count, @($records.DefinitionId | Sort-Object -Unique | Where-Object { $scripts.ContainsKey($_) }).Count,
    @($records.DefinitionId | Sort-Object -Unique | Where-Object { -not $scripts.ContainsKey($_) }).Count

$selected | ForEach-Object {
    [pscustomobject]@{
        Index = $_.Index
        DefinitionId = '0x{0:X16}' -f $_.DefinitionId
        Key = '0x{0:X8}' -f $_.Key
        Variant = $_.Variant
        Script = if ($scripts.ContainsKey($_.DefinitionId)) { $scripts[$_.DefinitionId].Name } else { '(not extracted)' }
    }
} | Format-Table -AutoSize

if ($offset + 1 -eq $data.Length -and $data[$offset] -eq 0xD3) {
    $offset++ # PackedStream end marker.
}
if ($offset -ne $data.Length) {
    Write-Warning ('Parser stopped at 0x{0:X}; file length is 0x{1:X}.' -f $offset, $data.Length)
}
