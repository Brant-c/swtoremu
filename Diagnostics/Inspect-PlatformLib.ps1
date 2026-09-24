$assemblyPath = (Resolve-Path (Join-Path $PSScriptRoot '..\nexusclient\nexusclient\PlatformLib.dll')).Path
$assembly = [Reflection.Assembly]::LoadFile($assemblyPath)
$assembly.FullName
$assembly.ImageRuntimeVersion
$assembly.GetCustomAttributesData() | ForEach-Object { $_.ToString() }
$assembly.GetReferencedAssemblies() | Format-Table Name, Version
$flags = [Reflection.BindingFlags]'Public,NonPublic,Static,Instance,DeclaredOnly'
$assembly.GetTypes() | ForEach-Object {
    $_.FullName
    $_.GetMethods($flags) | ForEach-Object { '  ' + $_.ToString() }
}
