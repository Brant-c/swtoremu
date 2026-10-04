@echo off
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\TriggerCollision-20260930\Launch.ps1"
if errorlevel 1 (
    echo Trigger-collision preparation failed. Do not launch another client or cross the doorway.
    pause
    exit /b 1
)
