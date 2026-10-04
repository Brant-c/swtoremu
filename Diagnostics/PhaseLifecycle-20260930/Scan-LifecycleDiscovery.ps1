param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if ([IntPtr]::Size -ne 8) { throw 'Use 64-bit PowerShell for the full 32-bit address-space scan.' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Refusing to overwrite a discovery scan.' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
# Reuse the existing read-only API and scanning helpers without executing the
# watcher's process-selection, readiness, waiting or capture actions.
$watcher = Join-Path $PSScriptRoot 'Watch-PhaseLifecycle.ps1'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($watcher,[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
$addType=$ast.Find({param($node) $node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -eq 'Add-Type'},$true)
. ([scriptblock]::Create($addType.Extent.Text))
foreach($name in @('Read-Bytes','Hex','Scan-Needles')) {
    $definition=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    if(!$definition){throw "Missing helper: $name"}
    $text=$definition.Extent.Text
    if($name -eq 'Scan-Needles') {
        $text=$text.Replace('[long]$limit=0x7FFF0000','[long]$limit=0x100000000')
        $text=$text.Replace('if($readable) {','if($readable -and $mbi.Type -eq 0x20000 -and $basic -in @(0x20,0x40,0x80)) {')
        $text=$text.Replace('$maxLength=8','$maxLength=15')
    }
    . ([scriptblock]::Create($text))
}
$needles=@{
    PhaseInfoDestroy=[byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x4C,0xC7,0x04,0x24,0x3F,0,0,0,0xE8)
    UpdateGateway=[byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x6C,0xC7,0x04,0x24,0x4A,0x01,0,0,0xE8)
    PlayerPhaseCreate=[byte[]](0x56,0x83,0xEC,0x18,0xC7,0x04,0x24,0x05,0,0,0,0xE8)
    PlayerPhaseDestroy=[byte[]](0x55,0x53,0x57,0x56,0x83,0xEC,0x2C,0xC7,0x04,0x24,0x1B,0,0,0,0xE8)
}
$summaries=foreach($client in Get-Process swtor-emu -ErrorAction Stop) {
    $started=Get-Date -Format o
    $handle=[PhaseLifecycleMemory]::OpenProcess(0x410,$false,$client.Id)
    if($handle -eq [IntPtr]::Zero){throw "Cannot query/read client PID $($client.Id)."}
    try {
        $matches=@(Scan-Needles $handle $needles)
        $matches | Export-Csv (Join-Path $OutputDirectory "$($client.Id)-matches.csv") -NoTypeInformation
        foreach($match in $matches) {
            $address=[Convert]::ToUInt32($match.Address.Substring(2),16)
            $code=Read-Bytes $handle $address 512
            if($null -ne $code){[IO.File]::WriteAllBytes((Join-Path $OutputDirectory "$($client.Id)-$($match.Kind)-$($match.Address).bin"),$code)}
        }
        foreach($kind in $needles.Keys) {
            $hits=@($matches | Where-Object Kind -eq $kind)
            [pscustomobject]@{PID=$client.Id;StartedAt=$started;CompletedAt=(Get-Date -Format o);Kind=$kind;Matches=$hits.Count;Below2GB=@($hits|Where-Object {[Convert]::ToUInt32($_.Address.Substring(2),16) -lt 0x80000000}).Count;Addresses=(($hits|ForEach-Object {$_.Address}) -join ';');Access='0x410 query/read';Scope='Committed readable executable MEM_PRIVATE over the full 32-bit range; short signatures only, not complete method identity.'}
        }
    } finally {[void][PhaseLifecycleMemory]::CloseHandle($handle)}
}
$summaries | Export-Csv (Join-Path $OutputDirectory 'summary.csv') -NoTypeInformation
$summaries | Format-Table PID,Kind,Matches,Below2GB,Addresses -AutoSize
