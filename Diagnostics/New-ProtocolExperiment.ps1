[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Question,
    [datetime]$Date = (Get-Date),
    [string]$ExperimentsPath = (Join-Path $PSScriptRoot 'Experiments')
)

$ErrorActionPreference = 'Stop'
$templatePath = Join-Path $ExperimentsPath 'TEMPLATE.md'
$indexPath = Join-Path $ExperimentsPath 'INDEX.md'
if (!(Test-Path -LiteralPath $templatePath) -or !(Test-Path -LiteralPath $indexPath)) {
    throw "Experiment template or index is missing under $ExperimentsPath."
}

$dateText = $Date.ToString('yyyy-MM-dd')
$slug = ($Name.ToLowerInvariant() -replace '[^a-z0-9]+','-').Trim('-')
if (!$slug) { throw 'Name must contain at least one letter or number.' }

$existing = @(Get-ChildItem -LiteralPath $ExperimentsPath -File -Filter "$dateText-*.md" |
    Where-Object { $_.Name -match ('^{0}-(\d{{2}})-' -f [regex]::Escape($dateText)) })
$numbers = @($existing | ForEach-Object {
    if ($_.Name -match ('^{0}-(\d{{2}})-' -f [regex]::Escape($dateText))) { [int]$Matches[1] }
})
$next = if ($numbers.Count) { [int](($numbers | Measure-Object -Maximum).Maximum + 1) } else { 1 }
$id = '{0}-{1:D2}' -f $dateText,$next
$fileName = "$id-$slug.md"
$outputPath = Join-Path $ExperimentsPath $fileName
if (Test-Path -LiteralPath $outputPath) { throw "Experiment already exists: $outputPath" }

$template = [IO.File]::ReadAllText($templatePath)
$body = $template.Replace('Experiment YYYY-MM-DD-NN — short name', "Experiment $id — $Name")
$body = $body.Replace("State one falsifiable question.", $Question.Trim())
[IO.File]::WriteAllText($outputPath, $body, [Text.UTF8Encoding]::new($false))

$escapeCell = {
    param([string]$Value)
    return (($Value -replace '\|','\|') -replace "`r?`n", ' ')
}
$safeQuestion = & $escapeCell $Question.Trim()
$safeName = & $escapeCell $Name.Trim()
$row = "| [$id](./$fileName) | $safeQuestion | $safeName | pending | none | pending |"
$index = [IO.File]::ReadAllText($indexPath)
$emptyRow = '| _none yet_ | | | | | |'
if ($index.Contains($emptyRow)) {
    $index = $index.Replace($emptyRow, $row)
} else {
    $index = $index.TrimEnd() + [Environment]::NewLine + $row + [Environment]::NewLine
}
[IO.File]::WriteAllText($indexPath, $index, [Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    Id = $id
    Path = $outputPath
    Index = $indexPath
}

