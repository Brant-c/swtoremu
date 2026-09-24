param(
    [string]$AssemblyPath = (Join-Path $PSScriptRoot 'AreaWireBuild\NexusToRServer.exe'),
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug'),
    [string]$Crt3OutputPath
)
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) {
    throw 'Run this test with C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe (the server assembly is x86).'
}
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path $AssemblyPath).Path)
$dataRoot = (Resolve-Path $DataDirectory).Path
$previousDirectory = [Environment]::CurrentDirectory
$zType = $assembly.GetType('ComponentAce.Compression.Libs.zlib.ZStream', $true)
$cases = @(
    @{ Name='AreaClientReplicationTransaction'; Folder='CRT'; Extension='acrt'; Count=17; Header=8 },
    @{ Name='AreaAwarenessEntered'; Folder='Awareness'; Extension='aaw'; Count=2; Header=8 },
    @{ Name='AreaEffEventMessage'; Folder='EffectEvent'; Extension='aeff'; Count=8; Header=12 }
)
$checked = 0
try {
    [Environment]::CurrentDirectory = $dataRoot
    foreach ($handle in @([uint16]8, [uint16]19)) {
        # A connection retains compression history across successive packets.
        $deflater = [Activator]::CreateInstance($zType)
        $inflater = [Activator]::CreateInstance($zType)
        if ($deflater.deflateInit(-1, -15) -ne 0 -or $inflater.inflateInit(-15) -ne 0) {
            throw 'Unable to initialize raw compression streams'
        }
        try {
            foreach ($case in $cases) {
                $type = $assembly.GetType('NexusToRServer.NET.Packets.Server.' + $case.Name, $true)
                foreach ($id in 1..$case.Count) {
                    $file = Join-Path $dataRoot ('AreaServer\{0}\tython_blockout-4611686019869492753-1.{1}.{2}' -f $case.Folder,$id,$case.Extension)
                    $fixture = [IO.File]::ReadAllBytes($file)
                    if (!$fixture.Length) { throw "Empty fixture: $file" }
                    $packet = [Activator]::CreateInstance($type, [object[]]@('tython_blockout','4611686019869492753','1',[int]$id))
                    $packet.ClientAreaServiceID = $handle
                    $packet.SetModule([byte]8)
                    $packet.Encrypted = $false # Test framing/compression, not session cipher keys.
                    $packet.InitBuffers()
                    try {
                        $packet.WriteImplementation()
                        $plain = $packet._stream.ToArray()
                        if ($plain.Length -ne $fixture.Length + $case.Header) { throw 'Plaintext length mismatch' }
                        if ([BitConverter]::ToUInt16($plain,4) -ne 0x65B3 -or [BitConverter]::ToUInt16($plain,6) -ne $handle) { throw 'Routing mismatch' }
                        if ($case.Header -eq 12 -and [BitConverter]::ToInt32($plain,8) -ne $fixture.Length) { throw 'Effect frame length mismatch' }
                        for ($i=0; $i -lt $fixture.Length; $i++) {
                            if ($plain[$i+$case.Header] -ne $fixture[$i]) { throw "Fixture changed at $i in $file" }
                        }
                        $wire = $packet.Construct($null, $deflater)
                        if ($deflater.avail_in -ne 0 -or $deflater.avail_out -eq 0) { throw 'Compression buffer exhausted' }
                        if ($wire[0] -ne 8 -or [BitConverter]::ToUInt32($wire,1) -ne $wire.Length) { throw 'Transport frame length/module mismatch' }
                        [byte]$checksum = 0
                        foreach ($i in 0..4) { $checksum = $checksum -bxor $wire[$i] }
                        if ($wire[5] -ne $checksum) { throw 'Transport checksum mismatch' }
                        # Construct omits the Z_SYNC_FLUSH suffix; restore it for decoding.
                        $compressed = New-Object byte[] ($wire.Length - 6 + 4)
                        [Array]::Copy($wire,6,$compressed,0,$wire.Length-6)
                        $compressed[$compressed.Length-2] = 255
                        $compressed[$compressed.Length-1] = 255
                        $inflater.next_in = $compressed
                        $inflater.next_in_index = 0
                        $inflater.avail_in = $compressed.Length
                        $inflater.next_out = New-Object byte[] ($plain.Length+1)
                        $inflater.next_out_index = 0
                        $inflater.avail_out = $plain.Length+1
                        $status = $inflater.inflate(2)
                        if ($status -ne 0 -or $inflater.avail_in -ne 0 -or $inflater.next_out_index -ne $plain.Length) { throw "Inflate failed: $status $($inflater.msg)" }
                        for ($i=0; $i -lt $plain.Length; $i++) {
                            if ($plain[$i] -ne $inflater.next_out[$i]) { throw "Round-trip mismatch at $i in $file" }
                        }
                        if ($Crt3OutputPath -and $handle -eq 8 -and $case.Extension -eq 'acrt' -and $id -eq 3) {
                            [IO.File]::WriteAllBytes([IO.Path]::GetFullPath($Crt3OutputPath), $plain)
                        }
                        $checked++
                    } finally { $packet._stream.Dispose() }
                }
            }
        } finally {
            $null = $deflater.deflateEnd()
            $null = $inflater.inflateEnd()
        }
    }
    "PASS: $checked fixture packets, dynamic handles 8/19, byte-exact raw-deflate round trips and transport headers."
    'Scope: fixture preservation and compression only; not native style-7 decoding, encryption, full startup ordering, or world-entry success.'
} finally { [Environment]::CurrentDirectory = $previousDirectory }
