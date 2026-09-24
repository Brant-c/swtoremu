# CRT3 fixture file existence + hash (read-only)
$f = 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT\tython_blockout-4611686019869492753-1.3.acrt'
if (!(Test-Path $f)) {
    Write-Output "MISSING: $f"
    Write-Output 'CRT dir contents:'
    gci 'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT' | select Name, @{n='LWT';e={$_.LastWriteTimeUtc}}, @{n='Len';e={$_.Length}} | Out-String
} else {
    Write-Output "EXISTS: $f"
    $bytes = [IO.File]::ReadAllBytes($f)
    $hash = (Get-FileHash -InputStream ([IO.MemoryStream]::new($bytes)) -Algorithm SHA256).Hash
    Write-Output "SHA256: $hash"
    Write-Output "len: $($bytes.Length)"
    Write-Output "head32 hex: $([BitConverter]::ToString($bytes,0,4).Replace('-',' '))"
    Write-Output "head32 uint32: 0x$([BitConverter]::ToUInt32($bytes,0).ToString('X8'))"
}
