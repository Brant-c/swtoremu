@echo off
cd /d "D:\SWTORClassic\swtoremu"
echo [launcher] Starting SWTORClassic trace run at %date% %time%
call "Run-SWTORClassic-Trace-Tython.cmd"
echo [launcher] Run-SWTORClassic-Trace-Tython.cmd exited with %errorlevel%
