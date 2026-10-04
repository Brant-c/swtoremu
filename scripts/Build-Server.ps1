param([string]$MSBuildPath, [string]$ValidationOutput)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (!$MSBuildPath) {
    $candidate = Get-Command MSBuild.exe -ErrorAction SilentlyContinue
    if ($candidate) { $MSBuildPath = $candidate.Source }
    else {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
        if (Test-Path -LiteralPath $vswhere) {
            $MSBuildPath = @(& $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild/**/Bin/MSBuild.exe' | Select-Object -First 1)[0]
        }
    }
}
if (!$MSBuildPath -or !(Test-Path -LiteralPath $MSBuildPath)) { throw 'MSBuild is required; install the VS .NET desktop build tools / Framework 4.8 targeting pack, or pass -MSBuildPath.' }
$projects = @(
    @{Name='server';Path='SharpServer/NexusToRServer.csproj'},
    @{Name='shard-list';Path='SharpServer/ShardListServer/ShardListServer.csproj'}
)
foreach ($project in $projects) {
    $buildArgs = @((Join-Path $root $project.Path),'/t:Build','/p:Configuration=Debug','/p:Platform=x86','/nologo','/verbosity:minimal')
    if ($ValidationOutput) {
        $outputRoot = [IO.Path]::GetFullPath((Join-Path $root $ValidationOutput))
        if (!$outputRoot.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Validation output must stay within this repository.' }
        $buildArgs += '/p:OutputPath=' + (Join-Path $outputRoot ($project.Name + '/'))
        $buildArgs += '/p:IntermediateOutputPath=' + (Join-Path $outputRoot ($project.Name + '-obj/'))
    }
    & $MSBuildPath @buildArgs
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $($project.Name) (exit $LASTEXITCODE)" }
}
if (!$ValidationOutput) {
    Copy-Item -LiteralPath (Join-Path $root 'SharpServer/ShardListServer/Shards.xml') -Destination (Join-Path $root 'SharpServer/ShardListServer/bin/Debug/Shards.xml')
}
Write-Output 'Both server components built. No servers or client launched.'
