$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$target=Join-Path $root 'Assets2012April'
$index=[Net.WebUtility]::HtmlDecode([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'jedipedia-patch-index-20260916.html')))
$token=[regex]::Match($index,'current download token is ([a-f0-9]+)').Groups[1].Value
if (!$token) { throw 'Public archive download token not found.' }
$files=Get-Content (Join-Path $PSScriptRoot 'april-asset-manifest.json') -Raw | ConvertFrom-Json
foreach($file in $files) {
    $path=Join-Path $target $file.name
    if(Test-Path -LiteralPath $path) {
        if((Get-Item -LiteralPath $path).Length -ne $file.size -or (Get-FileHash -LiteralPath $path -Algorithm MD5).Hash -ne $file.md5) {
            throw ('Existing file differs from manifest; preserved: '+$file.name)
        }
        Write-Output ('Verified existing '+$file.name)
        continue
    }
    $url='https://swtor.jedipedia.net/ajax/getPatchFile.php?product={0}&release={1}&file={2}&auth={3}' -f $file.product,$file.release,$file.name,$token
    Write-Output ('Downloading '+$file.name+' ('+$file.size+' bytes)')
    # Sequential downloads as requested by the public archive. Never replace a final file.
    for($attempt=1; $attempt -le 15; $attempt++) {
        try {
            Invoke-WebRequest -Uri $url -OutFile ($path+'.partial')
            break
        } catch {
            if($attempt -eq 15) { throw }
            Write-Output ('Download deferred by archive or network; retry '+$attempt+' in 60 seconds: '+$file.name)
            Start-Sleep -Seconds 60
        }
    }
    if((Get-Item -LiteralPath ($path+'.partial')).Length -ne $file.size -or (Get-FileHash -LiteralPath ($path+'.partial') -Algorithm MD5).Hash -ne $file.md5) {
        throw ('Downloaded file failed verification: '+$file.name)
    }
    Move-Item -LiteralPath ($path+'.partial') -Destination $path
    Write-Output ('Verified downloaded '+$file.name)
}
Write-Output ('Verified complete manifest: '+$files.Count+' archives.')
