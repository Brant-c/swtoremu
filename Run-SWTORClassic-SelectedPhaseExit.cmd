@echo off
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\SelectedPhaseExit-20260930\Launch.ps1"
if errorlevel 1 (
    echo Selected-player phase exit preparation failed. Do not start another client.
    pause
    exit /b 1
)
