# swtoremu: CRT3 variant probe (read-only, no mutation)
$script = "D:\SWTORClassic\swtoremu\Diagnostics\Set-Crt3Variant.ps1"
if (!(Test-Path $script)) { Write-Output "Set-Crt3Variant.ps1 missing"; exit 1 }
Write-Output "--- VariantList (Mode=VariantList) ---"
& $script -Mode VariantList 2>&1
Write-Output ""
Write-Output "--- CurrentVariant (Mode=CurrentVariant) ---"
& $script -Mode CurrentVariant 2>&1
