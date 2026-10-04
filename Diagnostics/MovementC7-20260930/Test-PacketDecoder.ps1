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
$compiled.CompiledAssembly.GetType('PacketDecoderRegression').GetMethod('Run').Invoke($null,[object[]]@(,$fixture)) | Out-Null
$provider.Dispose()
'PASS: captured C5 decode and field preservation; all 44 truncations; wrong variant/opcode; trailing byte; actual dispatcher rejection logs and no gameplay entry; Read/Run gate; Hero v5 unsigned/signed token bounds.'
'No native-client acceptance or room-loading claim is made.'
