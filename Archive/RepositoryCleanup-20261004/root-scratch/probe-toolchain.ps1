# locate .NET build toolchain on this machine (safe .NET IO writes to TEMP, hardcoded)
$log = 'C:\Users\brant\AppData\Local\Temp\_toolchain_locate.txt'
$lines = New-Object System.Collections.Generic.List[string]
$null = $lines.Add('=== toolchain locate ===')
$null = $lines.Add('[begin] ' + [DateTimeOffset]::UtcNow.ToString('o'))

function probeDir($label, $root) {
    $null = $lines.Add('')
    $null = $lines.Add('--- ' + $label + ': ' + $root + ' ---')
    if (-not (Test-Path $root)) { $null = $lines.Add('[dir missing]'); return }
    try {
        $items = Get-ChildItem -Path $root -ErrorAction Stop
        $null = $lines.Add('[ok] items count=' + $items.Count)
        foreach ($i in $items) {
            $len = if ($i.PSIsContainer) { '[dir]' } else { $i.Length }
            $null = $lines.Add('   ' + $i.Name + '  LWT=' + $i.LastWriteTimeUtc.ToString('o') + '  len=' + $len)
        }
    } catch {
        $null = $lines.Add('[FAIL] Get-ChildItem: ' + $_.Exception.Message)
    }
}

probeDir 'VS2022 Community root' 'C:\Program Files\Microsoft Visual Studio\2022\Community'
probeDir 'VS2022 Professional root' 'C:\Program Files\Microsoft Visual Studio\2022\Professional'
probeDir 'VS2022 BuildTools root' 'C:\Program Files\Microsoft Visual Studio\2022\BuildTools'
probeDir 'VS2019 root' 'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community'
probeDir 'dotnet installs (Program Files)' 'C:\Program Files\dotnet'
probeDir 'dotnet installs (Program Files x86)' 'C:\Program Files (x86)\dotnet'

# search for msbuild/csc/devenv/dotnet underneath VS2022 Community (shallow, top 5 levels)
$null = $lines.Add('')
$null = $lines.Add('--- search VS2022 Community for executables ---')
$searchRoot = 'C:\Program Files\Microsoft Visual Studio\2022\Community'
if (Test-Path $searchRoot) {
    try {
        $exeList = @('MSBuild.exe','csc.exe','devenv.exe','vbc.exe','dotnet.exe')
        $hits = New-Object System.Collections.Generic.List[string]
        $queue = New-Object System.Collections.Generic.Queue[System.IO.DirectoryInfo]
        $queue.Enqueue((Get-Item $searchRoot))
        $visited = New-Object System.Collections.Generic.HashSet[string]
        while ($queue.Count -gt 0 -and $hits.Count -lt 200) {
            $dir = $queue.Dequeue()
            if (-not ($visited.Add($dir.FullName))) { continue }
            foreach ($exe in $exeList) {
                $f = Join-Path $dir.FullName $exe
                if (Test-Path $f) { $null = $hits.Add($f + '  LWT=' + (Get-Item $f).LastWriteTimeUtc.ToString('o')) }
            }
            if ($dir.FullName.Length -lt 60) {
                try {
                    foreach ($sub in $dir.GetDirectories()) {
                        $queue.Enqueue($sub)
                    }
                } catch {}
            }
        }
        $null = $lines.Add('[ok] hits count=' + $hits.Count)
        foreach ($h in $hits) { $null = $lines.Add('   ' + $h) }
    } catch {
        $null = $lines.Add('[FAIL] search: ' + $_.Exception.Message)
    }
} else {
    $null = $lines.Add('[dir missing] cannot search')
}

[System.IO.File]::WriteAllText($log, ($lines -join "`r`n"), [System.Text.Encoding]::UTF8)
