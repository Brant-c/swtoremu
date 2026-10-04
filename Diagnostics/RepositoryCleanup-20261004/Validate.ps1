$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $root
$host32 = Join-Path $env:WINDIR 'SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
$assembly = Join-Path $PSScriptRoot 'build/server/NexusToRServer.exe'
$checks = foreach ($test in @('Test-AreaRouting.ps1','Test-AreaBlobFraming.ps1','Test-AreaWireRoundTrip.ps1','Test-WorldEntryOffline.ps1','Test-PacketWorkbench.ps1')) {
    $testArgs = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',(Join-Path $root ('Diagnostics/' + $test)))
    if ($test -ne 'Test-PacketWorkbench.ps1') { $testArgs += @('-AssemblyPath',$assembly) }
    $output = & $host32 @testArgs 2>&1
    $exit = $LASTEXITCODE
    $output | Set-Content -LiteralPath (Join-Path $PSScriptRoot ($test + '.after.txt'))
    [pscustomobject]@{Check=$test;Exit=$exit;Assembly=$assembly;Result=if ($exit -eq 0) {'PASS'} else {'FAIL'}}
}
$checks | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot 'validation.csv')
$checks | Format-Table Check,Result,Exit
$errors = @()
foreach ($p in @(Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -Filter '*.ps1')) {
    $tokens = $null; $parseErrors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($p.FullName,[ref]$tokens,[ref]$parseErrors)
    $errors += $parseErrors
}
if ($errors.Count) { throw ($errors -join [Environment]::NewLine) }
& (Join-Path $root 'scripts/Start-Servers.ps1') -CheckOnly
Write-Output 'All three workflow scripts parse; server-only preflight completed.'
# Historical pins remain unchanged: validate exact present inputs, not narratives.
$pins = foreach ($experiment in @('RetreatGateway-20261001','TaxiDevelopment-20261001','WellerStory-20261001')) {
    $identity = Join-Path $root ('Diagnostics/' + $experiment + '/identity.csv')
    if (!(Test-Path -LiteralPath $identity)) { continue }
    foreach ($row in @(Import-Csv -LiteralPath $identity)) {
        $actual = if (Test-Path -LiteralPath $row.Path -PathType Leaf) {(Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash} else {'MISSING'}
        [pscustomobject]@{Experiment=$experiment;Path=$row.Path;Expected=$row.SHA256;Actual=$actual;Matches=($actual -eq $row.SHA256)}
    }
}
$pins | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot 'launcher-pins.csv')
$pins | Group-Object Experiment | ForEach-Object { Write-Output "$($_.Name): $(@($_.Group | Where-Object Matches).Count)/$($_.Count) pins match" }
# Check indexed project item paths without evaluating old tooling installations.
$missing = foreach ($project in @(git ls-files '*.csproj' '*.vcxproj')) {
    [xml]$xml = Get-Content -LiteralPath $project -Raw
    foreach ($item in $xml.SelectNodes('//*[@Include]')) {
        if ($item.LocalName -notin @('Compile','ClCompile','ClInclude','ProjectReference')) { continue }
        $relative = $item.GetAttribute('Include')
        if ($relative -match '\$|\*') { continue }
        $target = Join-Path (Split-Path (Join-Path $root $project) -Parent) $relative
        if (!(Test-Path -LiteralPath $target)) { [pscustomobject]@{Project=$project;Kind=$item.LocalName;Include=$relative} }
    }
}
@($missing) | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $PSScriptRoot 'missing-project-items.csv')
Write-Output "Missing explicit source/project items: $(@($missing).Count) (see CSV; historical projects are not silently repaired)."
& (Join-Path $PSScriptRoot 'Inventory.ps1') -After
$afterHashes = @{}; foreach ($r in Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'runtime-hashes-after.csv')) { $afterHashes[$r.Path] = $r.SHA256 }
$changed = @(foreach ($r in Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'runtime-hashes-before.csv')) { if (!$afterHashes.ContainsKey($r.Path) -or $afterHashes[$r.Path] -ne $r.SHA256) { $r } })
if ($changed.Count) { throw ('Runtime preservation failed: ' + ($changed.Path -join ', ')) }
Write-Output 'All existing hashed runtime inputs are byte-identical to the pre-cleanup snapshot.'
