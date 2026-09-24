@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\Capture-Launch.ps1" -AllowPartialAssets
pause
