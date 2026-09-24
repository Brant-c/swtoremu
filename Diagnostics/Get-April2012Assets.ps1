$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$target=Join-Path $root 'Assets2012April'
New-Item -ItemType Directory -Force -Path $target | Out-Null
$index=[Net.WebUtility]::HtmlDecode((Get-Content (Join-Path $PSScriptRoot 'jedipedia-patch-index-current.html') -Raw))
$token=[regex]::Match($index,'current download token is ([a-f0-9]+)').Groups[1].Value
if (!$token) { throw 'Public archive download token not found.' }
$files=@(
    @('d3-retailclient_swtor',37,'swtor.exe','c2fc455757121ca4ba36caf30428eafe'),
    @('d3-assets_swtor_main',48,'swtor_main_gamedata_1.tor','df89680fb3b81c7bb4fbd239b936230a'),
    @('d3-assets_swtor_main',48,'swtor_main_systemgenerated_gom_1.tor','9c2d6b62a66713599f59c95b65563408'),
    @('d3-assets_swtor_main',48,'swtor_main_global_1.tor','dc60ddb488d05fcd81a279611971620a'),
    @('d3-assets_swtor_en_us',48,'swtor_en-us_global_1.tor','9421eff3f67a4d0717e4284c05d89349'),
    @('d3-assets_swtor_main',48,'swtor_main_gfx_1.tor','0adfa4edd4a1eca524e84720724b8744'),
    @('d3-assets_swtor_main',48,'swtor_main_art_misc_1.tor','fe738d44c267d728a39160b90ca8b9c7'),
    @('d3-assets_swtor_main',48,'swtor_main_art_creature_a_1.tor','8ae3a23f909aec9bda9fc017e1aa5a63'),
    @('d3-assets_swtor_main',48,'swtor_main_zed_1.tor','105291db85437dd7d4e8ac4c848d9c2d'),
    @('d3-assets_swtor_main',48,'swtor_main_art_zed_1.tor','24411dc574e4b49193cf1aa4cbb47e75'),
    @('d3-assets_swtor_main',48,'swtor_main_anim_misc_1.tor','eb92c07a21a62d27ddfb5676628b59d3')
)
# The public archive asks for one download at a time.
foreach ($file in $files) {
    $path=Join-Path $target $file[2]
    if (!(Test-Path $path)) {
        $url='https://swtor.jedipedia.net/ajax/getPatchFile.php?product={0}&release={1}&file={2}&auth={3}' -f $file[0],$file[1],$file[2],$token
        Write-Output ('Downloading {0}' -f $file[2])
        Invoke-WebRequest -Uri $url -OutFile ($path+'.partial')
        $hash=(Get-FileHash ($path+'.partial') -Algorithm MD5).Hash
        if ($hash -ne $file[3]) { throw ('Checksum mismatch: '+$file[2]) }
        Move-Item -LiteralPath ($path+'.partial') -Destination $path
    }
    if ((Get-FileHash $path -Algorithm MD5).Hash -ne $file[3]) { throw ('Checksum mismatch: '+$file[2]) }
    Write-Output ('Verified {0} ({1} bytes)' -f $file[2],(Get-Item $path).Length)
}
