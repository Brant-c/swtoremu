$ErrorActionPreference = 'Stop'
$a = [Reflection.Assembly]::LoadFrom('D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToRServer.exe')
$t = $a.GetType('NexusToRServer.TorArchive')
$paths = @(
    '/art/defaultassets/white.tex',
    '/art/dynamic/spec/bfanew_skeleton.gr2',
    '/bnk2/init.bnk',
    '/art/fx/fxspec/0.fxspec'
)
# Expected hashes from python tor_hash (extract-tor-paths.py)
$expected = @{
    '/art/defaultassets/white.tex'        = 0x6C5AAAF57984613C
    '/art/dynamic/spec/bfanew_skeleton.gr2' = 0x5E1C59555A852AA1
    '/bnk2/init.bnk'                      = 0x12134B1C6BD30E91
    '/art/fx/fxspec/0.fxspec'             = 0x9C2FB7753172857D
}
$mHash = $t.GetMethod('Hash')
$mTry = $t.GetMethod('TryRead')
$mProbe = $t.GetMethod('Probe')
foreach ($p in $paths) {
    Write-Host ('--- ' + $p)
    Write-Host ($mProbe.Invoke($null, @($p)))
}
