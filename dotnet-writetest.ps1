# minimal write test using raw .NET IO (no Out-File pipes)
$path = 'D:\SWTORClassic\swtoremu\_dotnet_wtest.txt'
[System.IO.File]::WriteAllText($path, 'written-via-dotnet', [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($path + '.latin1', 'written-via-dotnet-latin1', [System.Text.Encoding]::Default)
