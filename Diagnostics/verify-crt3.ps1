$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt'
$b = [IO.File]::ReadAllBytes($f)
Write-Host ('len=' + $b.Length)
Write-Host ('head32=' + ([BitConverter]::ToString($b, 0, 4)))
Write-Host ('tail=0x' + $b[-1].ToString('X2'))
$sha = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b)).Replace('-', '').ToLowerInvariant()
Write-Host ('sha=' + $sha)
