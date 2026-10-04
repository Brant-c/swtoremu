@echo off
REM Corrected CRT3-on lifecycle baseline. Launch.ps1 verifies pinned inputs,
REM explicitly enables CRT3 and launches the client/servers with named callback
REM logging. No full-memory observer is started.
REM Run from the desktop; do not use the CRT3-off ablation launcher yet.
"%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\PhaseLifecycle-20260930\Launch.ps1"
if errorlevel 1 (
    echo Lifecycle preparation failed. Do not launch another client or cross the doorway.
    pause
    exit /b 1
)
