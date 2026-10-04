@echo off
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\TaxiDevelopment-20261001\Launch.ps1"
if errorlevel 1 (
    echo Taxi preparation failed. Do not start another client.
    pause
    exit /b 1
)
