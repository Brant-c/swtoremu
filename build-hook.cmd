@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0Dependencies\Detours\src"
nmake /nologo "CFLAGS=/W4 /Zi /MT /Gy /Zl /O2 /DWIN32_LEAN_AND_MEAN /D_WIN32_WINNT=0x501"
if errorlevel 1 exit /b %errorlevel%
msbuild "%~dp0Client\Hook\SWToR-Hook.vcxproj" /t:Build /p:Configuration=Release /p:Platform=Win32 /nologo /verbosity:minimal
