param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string[]] $Target = @('0x1279C371'),

    [string] $InputDirectory
)

$ErrorActionPreference = 'Stop'

# $PSScriptRoot is not reliably populated while PowerShell evaluates default
# parameter expressions. Resolve the repository-local archive after binding so
# the scanner works both directly and through the trace launcher.
if ([string]::IsNullOrWhiteSpace($InputDirectory)) {
    $InputDirectory = Join-Path $PSScriptRoot 'Scripts2012'
}

function Convert-Target([string] $Value) {
    $clean = $Value.Trim()
    if ($clean.StartsWith('0x', [StringComparison]::OrdinalIgnoreCase)) {
        return [Convert]::ToUInt32($clean.Substring(2), 16)
    }
    return [Convert]::ToUInt32($clean, 10)
}

function Find-Bytes([byte[]] $Data, [byte[]] $Needle) {
    for ($offset = 0; $offset -le $Data.Length - $Needle.Length; $offset++) {
        $match = $true
        for ($index = 0; $index -lt $Needle.Length; $index++) {
            if ($Data[$offset + $index] -ne $Needle[$index]) {
                $match = $false
                break
            }
        }
        if ($match) { $offset }
    }
}

function Get-ContextStrings([byte[]] $Data, [int] $Offset) {
    $start = [Math]::Max(0, $Offset - 192)
    $end = [Math]::Min($Data.Length - 1, $Offset + 192)
    $text = [Text.Encoding]::ASCII.GetString($Data[$start..$end])
    [regex]::Matches($text, '[\x20-\x7E]{4,}') |
        ForEach-Object Value |
        Select-Object -Unique -First 8
}

function Read-V5Payload([string] $Path) {
    [byte[]] $data = [IO.File]::ReadAllBytes($Path)
    if ($data.Length -lt 37 -or [Text.Encoding]::ASCII.GetString($data, 0, 4) -ne 'SCPT' -or
        $data[4] -ne 5 -or $data[5] -ne 0 -or $data[6] -ne 5 -or $data[7] -ne 0) {
        return $null
    }
    $length = [BitConverter]::ToInt32($data, 33)
    if ($length -lt 0 -or 37 + $length -gt $data.Length) {
        throw "Truncated v5 payload in $Path"
    }
    [byte[]] $payload = New-Object byte[] $length
    [Array]::Copy($data, 37, $payload, 0, $length)
    if ($data[24] -ne 0) {
        for ($index = 0; $index -lt $payload.Length; $index++) {
            $key = (0x35 + $index * 0x36) -band 0xFF
            $payload[$index] = $payload[$index] -bxor $key
        }
    }
    return ,$payload
}

$targets = @($Target | ForEach-Object { Convert-Target $_ })
$files = @(Get-ChildItem -LiteralPath $InputDirectory -Filter '*.scpt' -File | Sort-Object Name)
$scanned = 0
$rejected = 0
$hits = 0

foreach ($file in $files) {
    [byte[]] $payload = Read-V5Payload $file.FullName
    if ($null -eq $payload) {
        $rejected++
        continue
    }
    $scanned++
    foreach ($value in $targets) {
        [byte[]] $little = [BitConverter]::GetBytes([uint32] $value)
        [byte[]] $big = @($little[3], $little[2], $little[1], $little[0])
        foreach ($encoding in @(
            @{ Name = 'little'; Bytes = $little },
            @{ Name = 'big'; Bytes = $big }
        )) {
            foreach ($offset in @(Find-Bytes $payload $encoding.Bytes)) {
                $hits++
                '{0} 0x{1:X8} {2} @ 0x{3:X}' -f $file.Name, $value, $encoding.Name, $offset
                Get-ContextStrings $payload $offset | ForEach-Object { '  ' + $_ }
            }
        }
    }
}

'Scanned {0} v5 SCPT files ({1} non-v5/rejected).' -f $scanned, $rejected
'Targets: ' + (($targets | ForEach-Object { '0x{0:X8}' -f $_ }) -join ', ')
if ($hits -eq 0) { 'No exact 32-bit references found in either byte order.' }
