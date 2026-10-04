@echo off
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\MovementC7-20260930\Launch.ps1"
if errorlevel 1 (
    echo C7 movement preparation failed. Do not start another client.
    pause
    exit /b 1
)
