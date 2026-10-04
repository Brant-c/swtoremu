param([Parameter(Mandatory=$true)][string]$CaptureDirectory)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$source=[IO.File]::ReadAllText((Join-Path $root 'Client\Hook\Src\ToR.cpp'))
$start=$source.IndexOf('static bool MatchesLifecyclePattern(')
$end=$source.IndexOf('static DWORD FindExecutablePattern(',$start)
if($start -lt 0 -or $end -le $start){throw 'Native matcher source not found.'}
$matcher=$source.Substring($start,$end-$start)
$names=@('phaseInfoDestroyPattern','updateGatewayPattern','playerPhaseCreatePattern','playerPhaseDestroyPattern')
$arrays=foreach($name in $names){
    $match=[regex]::Match($source,('static const BYTE '+$name+'\[\]\s*=\s*\{[^}]+\};'))
    if(!$match.Success){throw "Missing pattern: $name"};$match.Value
}
$capture=(Resolve-Path -LiteralPath $CaptureDirectory).Path
$files=@(Get-ChildItem -LiteralPath $capture -Filter '*.bin')
if($files.Count -ne 11){throw 'Expected the preserved 11 candidate code captures.'}
$known=@('40024-PhaseInfoDestroy-0xF092D6B0.bin','40024-UpdateGateway-0xEC712670.bin','40024-PlayerPhaseCreate-0xEC57C810.bin','40024-PlayerPhaseDestroy-0xEC57CB00.bin')
$checks=foreach($file in $files){
    $kind=if($file.Name -like '*-PhaseInfoDestroy-*'){0}elseif($file.Name -like '*-UpdateGateway-*'){1}elseif($file.Name -like '*-PlayerPhaseCreate-*'){2}else{3}
    $path=$file.FullName.Replace('\','\\')
    $expected=if($file.Name -in $known){'true'}else{'false'}
    "if (!checkFile(`"$path`", $kind, $expected)) return 1;"
}
$build=Join-Path $PSScriptRoot 'PhaseLifecycleDiscoveryBuild'
New-Item -ItemType Directory -Path $build -Force | Out-Null
$native=@'
#include <windows.h>
#include <stdio.h>
#include <fstream>
#include <vector>
'@ + "`r`n" + $matcher + ($arrays -join "`r`n") + @'

struct Case { const BYTE* bytes; SIZE_T length; };
static Case cases[] = {
 {phaseInfoDestroyPattern, sizeof(phaseInfoDestroyPattern)},
 {updateGatewayPattern, sizeof(updateGatewayPattern)},
 {playerPhaseCreatePattern, sizeof(playerPhaseCreatePattern)},
 {playerPhaseDestroyPattern, sizeof(playerPhaseDestroyPattern)}
};
static bool checkFile(const char* path, int index, bool expected) {
 std::ifstream input(path, std::ios::binary);
 std::vector<BYTE> bytes((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
 if (bytes.size() < cases[index].length) return false;
 bool actual = MatchesLifecyclePattern(&bytes[0], cases[index].bytes, cases[index].length);
 if (actual != expected) { printf("FAIL candidate: %s\n", path); return false; }
 return true;
}
int main() {
 unsigned checks = 0;
 for (int c = 0; c < 4; ++c) {
  const Case& item = cases[c];
  bool mask[56] = {};
  for (SIZE_T i = 0; i + 4 < item.length; ++i)
   if (item.bytes[i] == 0xE8 && item.bytes[i+1] == 0xFC && item.bytes[i+2] == 0xFF && item.bytes[i+3] == 0xFF && item.bytes[i+4] == 0xFF)
    for (SIZE_T j = 1; j <= 4; ++j) mask[i+j] = true;
  for (SIZE_T i = 0; i < item.length; ++i) {
   std::vector<BYTE> changed(item.bytes, item.bytes + item.length);
   changed[i] ^= 1;
   if (MatchesLifecyclePattern(&changed[0], item.bytes, item.length) != mask[i]) {
    printf("FAIL mutation: case=%d offset=%u\n", c, (unsigned)i); return 1;
   }
   ++checks;
  }
 }
'@ + "`r`n" + ($checks -join "`r`n") + @'

 printf("PASS native lifecycle matcher: %u fixed/relocation-byte mutations; four genuine captured prefixes accepted; seven unrelated short-signature candidates rejected.\n", checks);
 return 0;
}
'@
[IO.File]::WriteAllText((Join-Path $build 'Matcher.cpp'),$native)
$batch=@'
@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat" >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /EHsc /MT Matcher.cpp /Fe:Matcher.exe
if errorlevel 1 exit /b %errorlevel%
Matcher.exe
'@
[IO.File]::WriteAllText((Join-Path $build 'Run.cmd'),$batch)
& (Join-Path $build 'Run.cmd')
if($LASTEXITCODE -ne 0){throw 'Native lifecycle matcher regression failed.'}
