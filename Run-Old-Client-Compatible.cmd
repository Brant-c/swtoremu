@echo off
cd /d "%~dp0Diagnostics"
echo Starting old client (single diagnostic attempt)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\Run-Compatibility-With-Transcript.ps1" -ClientDirectory "%~dp0nexusclient\nexusclient" -TimeoutSeconds 1800
set RESULT=%errorlevel%
:finished
echo.
echo The client run finished with code %RESULT%.
echo This window will stay open so you can read the final status.
pause
exit /b %RESULT%
