param([Parameter(Mandatory=$true)][string]$AssemblyPath)
$ErrorActionPreference='Stop'
if ([Environment]::Is64BitProcess) { throw 'Run with SysWOW64 Windows PowerShell (x86).' }
$path=(Resolve-Path $AssemblyPath).Path
[Reflection.Assembly]::LoadFrom($path) | Out-Null
$provider=New-Object Microsoft.CSharp.CSharpCodeProvider
$parameters=New-Object System.CodeDom.Compiler.CompilerParameters
$parameters.GenerateInMemory=$true
$parameters.CompilerOptions='/platform:x86'
[void]$parameters.ReferencedAssemblies.Add($path)
[void]$parameters.ReferencedAssemblies.Add('System.dll')
$compiled=$provider.CompileAssemblyFromFile($parameters, (Join-Path $PSScriptRoot 'PacketDecoderRegression.cs'))
if($compiled.Errors.HasErrors) { throw (($compiled.Errors | ForEach-Object {$_.ToString()}) -join "`n") }
[byte[]]$fixture=((Get-Content (Join-Path $PSScriptRoot 'Fixtures/Movement/C5-20260929.hex') -Raw).Trim() -split '\s+' | ForEach-Object {[Convert]::ToByte($_,16)})
[byte[]]$c7=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'TriggerCollision-20260930/live-20260930-172807/movement-c7-first.bin'))
$compiled.CompiledAssembly.GetType('PacketDecoderRegression').GetMethod('Run').Invoke($null,[object[]]@($fixture,$c7)) | Out-Null
$provider.Dispose()
'PASS: captured C5/C7 decode, correct C7 end-position offsets and raw preservation; all 100 truncations; unsupported masks/opcode/trailers; dispatcher rejection logs and no gameplay entry; Read/Run gate; Hero v5 bounds.'
'No native-client acceptance or room-loading claim is made.'
