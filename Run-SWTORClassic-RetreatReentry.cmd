@echo off
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\RetreatReentry-20260930\Launch.ps1"
if errorlevel 1 (
    echo Movement/phase preparation failed. Do not start another client.
    pause
    exit /b 1
)
