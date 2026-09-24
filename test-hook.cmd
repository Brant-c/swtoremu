@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0Client\Hook\Tests"
cl /nologo /MT /Od /I"..\..\..\Dependencies\Detours\include" DetoursSmoke.cpp /link /LIBPATH:"..\..\..\Dependencies\Detours\lib.X86" detours.lib
if errorlevel 1 exit /b %errorlevel%
DetoursSmoke.exe
