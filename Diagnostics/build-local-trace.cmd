@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /EHsc /MT TraceLocal.cpp /link dbghelp.lib user32.lib



