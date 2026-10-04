$ErrorActionPreference = 'Stop'

$root = Split-Path $PSScriptRoot -Parent
$cache = Join-Path $PSScriptRoot 'GomCompatibility\ResourceCacheApril2012\scripts'
$source = Join-Path $root 'Client\Hook\Src\ToR.cpp'

$cases = @(
    [pscustomobject]@{
        Name = 'phsPhaseInfo.OnReplicationNodeDestroy'
        Pattern = 'phaseInfoDestroyPattern'
        PrefixLength = 54
        File = '65A4399D0102A007.scpt'
        SHA256 = '76B92E207918FC458B26554264A71A6D78A7EA8DAC29D8AD05F7E3D15AE5A60E'
        Offset = 0x0B78
        Bytes = [byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x4C,0xC7,0x04,0x24,0x3F,0x00,0x00,0x00,0xE8)
    },
    [pscustomobject]@{
        Name = 'phsOracle.UpdateGatewayForInstance'
        Pattern = 'updateGatewayPattern'
        PrefixLength = 54
        File = 'C10C1F8290BE3551.scpt'
        SHA256 = '1DFA9168BDBD3A1B5267586B97AB7AEFCA9B5D715015ED43FD2188F849DE1F04'
        Offset = 0x32E3
        Bytes = [byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x6C,0xC7,0x04,0x24,0x4A,0x01,0x00,0x00,0xE8)
    },
    [pscustomobject]@{
        Name = 'phsPlayerPhaseData.OnReplicationNodeCreate'
        Pattern = 'playerPhaseCreatePattern'
        PrefixLength = 56
        File = '9308DE76F6AAF774.scpt'
        SHA256 = 'E40D0EC5C65A14BCC5E980720831778318FF1DC7B43C2D9277AFE51365393F1F'
        Offset = 0x00B1
        Bytes = [byte[]](0x56,0x83,0xEC,0x18,0xC7,0x04,0x24,0x05,0x00,0x00,0x00,0xE8)
    },
    [pscustomobject]@{
        Name = 'phsPlayerPhaseData.OnReplicationNodeDestroy'
        Pattern = 'playerPhaseDestroyPattern'
        PrefixLength = 56
        File = '9308DE76F6AAF774.scpt'
        SHA256 = 'E40D0EC5C65A14BCC5E980720831778318FF1DC7B43C2D9277AFE51365393F1F'
        Offset = 0x03A1
        Bytes = [byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x2C,0xC7,0x04,0x24,0x1B,0x00,0x00,0x00,0xE8)
    }
)

function Get-DecryptedPayload([string]$Path) {
    $raw = [IO.File]::ReadAllBytes($Path)
    if ($raw.Length -le 37) { throw "SCPT is too short: $Path" }
    $payload = New-Object byte[] ($raw.Length - 37)
    [byte]$key = 0x35
    for ($i = 0; $i -lt $payload.Length; $i++) {
        $payload[$i] = $raw[$i + 37] -bxor $key
        $key = [byte](($key + 0x36) -band 0xFF)
    }
    return ,$payload
}

$sourceText = [IO.File]::ReadAllText($source)
$sourceCompact = $sourceText -replace '\s',''
foreach ($case in $cases) {
    $path = Join-Path $cache $case.File
    $actualHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($actualHash -ne $case.SHA256) { throw "$($case.Name): resource hash changed ($actualHash)" }
    $payload = Get-DecryptedPayload $path
    if ($case.Offset + $case.Bytes.Length -gt $payload.Length) { throw "$($case.Name): offset is outside payload" }
    $actual = [byte[]]$payload[$case.Offset..($case.Offset + $case.Bytes.Length - 1)]
    if ([BitConverter]::ToString($actual) -ne [BitConverter]::ToString($case.Bytes)) {
        throw "$($case.Name): decrypted bytes differ at 0x$('{0:X}' -f $case.Offset)"
    }
    $initializer = ($case.Bytes | ForEach-Object { '0x{0:X2}' -f $_ }) -join ','
    if (-not $sourceCompact.Contains($initializer)) { throw "$($case.Name): pinned bytes are absent from ToR.cpp" }
    $prefix = [byte[]]$payload[$case.Offset..($case.Offset + $case.PrefixLength - 1)]
    $array = [regex]::Match($sourceText, ('static const BYTE ' + $case.Pattern + '\[\]\s*=\s*\{([^}]+)\}'),[Text.RegularExpressions.RegexOptions]::Singleline)
    if (!$array.Success) { throw "$($case.Name): named prefix array is missing" }
    $prefixInitializer = ($prefix | ForEach-Object { '0x{0:X2}' -f $_ }) -join ','
    if (($array.Groups[1].Value -replace '\s','') -ne $prefixInitializer) { throw "$($case.Name): complete relocated prefix differs from the pinned resource" }
    Write-Output ("PASS {0}: {1} +0x{2:X4}" -f $case.Name,$case.File,$case.Offset)
}

Write-Output 'PASS phase lifecycle signatures: pinned April resources, decrypted offsets, and hook patterns agree.'
