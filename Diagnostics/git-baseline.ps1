# swtoremu: baseline capture (read-only)
$out = "D:\SWTORClassic\swtoremu\Diagnostics\GitBaseline.txt"
"=== git status ===" | Out-File -FilePath $out -Encoding utf8
git status 2>&1 | Out-File -Append -FilePath $out
"" | Out-File -Append -FilePath $out
"=== git log -5 --oneline ===" | Out-File -Append -FilePath $out
git log -5 --oneline 2>&1 | Out-File -Append -FilePath $out
"" | Out-File -Append -FilePath $out
"=== tracked files count ===" | Out-File -Append -FilePath $out
(git ls-files -z 2>&1 | Measure-Object -Line -ErrorAction SilentlyContinue).Count | Out-File -Append -FilePath $out
"" | Out-File -Append -FilePath $out
"=== untracked count (heuristic) ===" | Out-File -Append -FilePath $out
(git ls-files --others --exclude-standard -z 2>&1 | Measure-Object -Line -ErrorAction SilentlyContinue).Count | Out-File -Append -FilePath $out
