@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /EHsc /MT CompatibilityLauncher.cpp /link user32.lib psapi.lib iphlpapi.lib ws2_32.lib dbghelp.lib
