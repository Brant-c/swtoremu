@echo off
rem Build the x86 Debug NexusToRServer used by the taxi launcher.
setlocal
set MSB=C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe
if not exist "%MSB%" (
  echo MSBuild not found at %MSB%
  exit /b 2
)
cd /d D:\SWTORClassic\swtoremu
"%MSB%" SharpServer\NexusToRServer.csproj /p:Configuration=Debug /p:Platform=x86 /v:minimal /nologo
echo MSBUILD_EXIT=%ERRORLEVEL%
exit /b %ERRORLEVEL%