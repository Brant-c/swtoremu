$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$compiler = 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
$python = 'C:\Users\brant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$sources = @(Get-ChildItem (Join-Path $repo 'Tools\tor_tools\Hero\Hero') -Recurse -Filter '*.cs')
$sources += @(Get-ChildItem (Join-Path $repo 'Tools\Hero\SharpZipLib') -Recurse -Filter '*.cs')
$arguments = @('/nologo', '/target:library', "/out:$PSScriptRoot\LegacyHero.dll", '/r:System.Core.dll') + $sources.FullName
& $compiler $arguments
if ($LASTEXITCODE) { throw 'Legacy reader build failed' }
& $python (Join-Path $PSScriptRoot 'extract-gom.py')
if ($LASTEXITCODE) { throw 'Extraction failed' }
& $compiler /nologo "/r:$PSScriptRoot\LegacyHero.dll" "/out:$PSScriptRoot\Probe.exe" "$PSScriptRoot\Probe.cs"
if ($LASTEXITCODE) { throw 'Probe build failed' }
& "$PSScriptRoot\Probe.exe" "$PSScriptRoot\client.gom" "$PSScriptRoot\client-gom-fixture.tor" | Tee-Object "$PSScriptRoot\result.txt"
if ($LASTEXITCODE) { throw 'Compatibility probe failed' }
