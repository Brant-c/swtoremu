[CmdletBinding(DefaultParameterSetName='Hex')]
param(
    [Parameter(Mandatory=$true,ParameterSetName='Hex')][string]$Hex,
    [Parameter(Mandatory=$true,ParameterSetName='Path')][string]$Path,
    [string]$CompareHex,
    [string]$ComparePath,
    [int]$PackedOffset = -1,
    [ValidateSet('Unsigned','Signed')][string]$PackedKind = 'Unsigned',
    [ValidateSet(1,5)][int]$TransportVersion = 5,
    [switch]$AsJson,
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'Protocol-Evidence.csv')
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PacketWorkbench.psm1') -Force

if ($PSCmdlet.ParameterSetName -eq 'Path') {
    [byte[]]$bytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path).Path)
    $source = (Resolve-Path -LiteralPath $Path).Path
} else {
    [byte[]]$bytes = ConvertFrom-PacketHex $Hex
    $source = '<hex>'
}

$report = Get-RoutedPacketReport -Bytes $bytes -RegistryPath $RegistryPath
$result = [ordered]@{ Source=$source; Packet=$report }

if ($PackedOffset -ge 0) {
    $result.Packed = Get-HeroPackedSequence -Bytes $bytes -Offset $PackedOffset -Kind $PackedKind -TransportVersion $TransportVersion
}

if ($ComparePath) {
    [byte[]]$compare = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $ComparePath).Path)
    $result.CompareSource = (Resolve-Path -LiteralPath $ComparePath).Path
    $result.Comparison = Compare-PacketBytes -Left $bytes -Right $compare
} elseif ($CompareHex) {
    [byte[]]$compare = ConvertFrom-PacketHex $CompareHex
    $result.CompareSource = '<compare-hex>'
    $result.Comparison = Compare-PacketBytes -Left $bytes -Right $compare
}

if ($AsJson) {
    [pscustomobject]$result | ConvertTo-Json -Depth 8
    exit 0
}

"Source: $source"
if (!$report.Valid) {
    "INVALID: $($report.Error)"
    "Length: $($report.Length)"
    "Hex: $($report.Hex)"
    exit 2
}
"Length: $($report.Length)"
"Opcode: $($report.Opcode) $($report.Name)"
"Registry: $($report.Direction) / $($report.Family) / $($report.Confidence)"
if ($report.Component) {
    "Component: $($report.Component) source=$($report.SourceHandle) destination=$($report.DestinationHandle)"
}
if ($report.Evidence) { "Evidence: $($report.Evidence)" }
if ($report.BodySchema) { "Body schema: $($report.BodySchema)" }
"Body: offset=$($report.BodyOffset) length=$($report.BodyLength)"
"Body hex: $($report.BodyHex)"

if ($result.Packed) {
    $packed = $result.Packed
    "Packed: kind=$($packed.Kind) transport=$($packed.TransportVersion) start=$($packed.StartOffset) end=$($packed.EndOffset) remaining=$($packed.Remaining) complete=$($packed.Complete)"
    foreach ($value in $packed.Values) {
        ('  @{0}: token={1} bytes={2} value={3} (0x{3:X})' -f $value.Offset,$value.Token,$value.Length,$value.Value)
    }
    if ($packed.Failure) { "  stopped: $($packed.Failure)" }
}

if ($result.Comparison) {
    $comparison = $result.Comparison
    "Compare: $($result.CompareSource) left=$($comparison.LeftLength) right=$($comparison.RightLength) differences=$($comparison.DifferenceCount)"
    foreach ($difference in $comparison.Differences) {
        ('  @{0}: {1} -> {2}' -f $difference.Offset,$difference.Left,$difference.Right)
    }
}

