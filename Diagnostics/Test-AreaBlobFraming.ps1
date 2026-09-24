param(
    [string]$AssemblyPath = (Join-Path $PSScriptRoot 'AreaFramingBuild\NexusToRServer.exe'),
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\SharpServer\bin\Debug')
)
$ErrorActionPreference = 'Stop'
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path $AssemblyPath).Path)
$dataRoot = (Resolve-Path $DataDirectory).Path
$previousDirectory = [Environment]::CurrentDirectory
$cases = @(
    @{ Name = 'AreaClientReplicationTransaction'; Folder = 'CRT'; Extension = 'acrt'; Count = 17; Opcode = [uint32]0x0D446E80 },
    @{ Name = 'AreaAwarenessEntered'; Folder = 'Awareness'; Extension = 'aaw'; Count = 2; Opcode = [Convert]::ToUInt32('A1D9E226', 16) }
)
$checked = 0
try {
    # The existing loaders resolve paths against the process working directory.
    [Environment]::CurrentDirectory = $dataRoot
    foreach ($case in $cases) {
        $type = $assembly.GetType('NexusToRServer.NET.Packets.Server.' + $case.Name, $true)
        foreach ($id in 1..$case.Count) {
            $file = Join-Path $dataRoot ('AreaServer\{0}\tython_blockout-4611686019869492753-1.{1}.{2}' -f $case.Folder, $id, $case.Extension)
            $blob = [IO.File]::ReadAllBytes($file)
            if ($blob.Length -eq 0) { throw "Empty fixture: $file" }
            foreach ($handle in @([uint16]8, [uint16]19)) {
                $packet = [Activator]::CreateInstance($type, [object[]]@('tython_blockout', '4611686019869492753', '1', [int]$id))
                $packet.ClientAreaServiceID = $handle
                $packet.InitBuffers()
                $packet.WriteImplementation()
                $bytes = $packet._stream.ToArray()
                if ($bytes.Length -ne (8 + $blob.Length)) {
                    throw "$($case.Name) $id has unexpected outer framing: $($bytes.Length) bytes"
                }
                if ([BitConverter]::ToUInt32($bytes, 0) -ne $case.Opcode) { throw 'Opcode mismatch' }
                if ([BitConverter]::ToUInt16($bytes, 4) -ne 0x65B3 -or [BitConverter]::ToUInt16($bytes, 6) -ne $handle) {
                    throw 'Area routing mismatch'
                }
                for ($offset = 0; $offset -lt $blob.Length; $offset++) {
                    if ($bytes[$offset + 8] -ne $blob[$offset]) {
                        throw "$($case.Name) $id payload mismatch at offset $offset"
                    }
                }
                $packet._stream.Dispose()
                $checked++
            }
        }
    }
    "PASS: $checked packet bodies; all 17 CRTs and 2 awareness blobs preserved byte-for-byte after the 8-byte opcode/component header, with dynamic handles 8/19."
    'Scope: serializer regression only; fixture compatibility with the client and successful world loading are not established by this test.'
}
finally {
    [Environment]::CurrentDirectory = $previousDirectory
}