# Probe CRT3 fixture state (read-only, correct positional arg)
$script = 'D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1'
if (!(Test-Path $script)) { throw 'Set-Crt3Variant.ps1 missing' }
& $script Status
