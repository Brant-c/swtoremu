$ErrorActionPreference = 'Stop'
$watcher = Join-Path $PSScriptRoot 'PhaseLifecycle-20260930\Watch-PhaseLifecycle.ps1'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($watcher,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
# Load only the pure readiness function. Never execute the watcher or open a
# process in this offline regression test.
$definition = $ast.Find({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-PhaseBaseline'
},$true)
if (!$definition) { throw 'Readiness function is missing.' }
. ([scriptblock]::Create($definition.Extent.Text))
$kinds = @('GnarlsControlId','PhaseInfoId','ParentInstanceId','PlayerPhaseDataId')
$valid = @($kinds | ForEach-Object { [pscustomobject]@{Kind=$_;IsHeroNode=$true} })
if (@(Assert-PhaseBaseline $valid).Count -ne 4) { throw 'Valid baseline was rejected.' }
$rejections = 0
foreach ($kind in $kinds) {
    foreach ($scenario in @('missing','duplicate','non-HeroNode')) {
        $objects = @($valid | Where-Object Kind -ne $kind)
        if ($scenario -eq 'duplicate') {
            $objects += @([pscustomobject]@{Kind=$kind;IsHeroNode=$true},[pscustomobject]@{Kind=$kind;IsHeroNode=$true})
        } elseif ($scenario -eq 'non-HeroNode') {
            $objects += [pscustomobject]@{Kind=$kind;IsHeroNode=$false}
        }
        $rejected = $false
        try { [void](Assert-PhaseBaseline $objects) } catch {
            if (!$_.Exception.Message.Contains("$kind HeroNode")) { throw }
            $rejected = $true
        }
        if (!$rejected) { throw "Invalid baseline accepted: $kind / $scenario" }
        $rejections++
    }
}
'PASS lifecycle readiness: valid four-identity baseline accepted; all 12 missing, duplicate and non-HeroNode cases rejected; observer parses without execution.'
