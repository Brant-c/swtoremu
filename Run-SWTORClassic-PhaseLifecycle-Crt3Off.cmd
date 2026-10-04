@echo off
REM CRT3-off comparison using the same verified log-only launcher as baseline.
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\PhaseLifecycle-20260930\Launch-Crt3Off.ps1"
if errorlevel 1 (
    echo CRT3-off preparation failed. Do not launch another client or cross the doorway.
    pause
    exit /b 1
)
