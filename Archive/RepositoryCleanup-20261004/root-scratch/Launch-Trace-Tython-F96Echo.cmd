@echo off
cd /d "D:\SWTORClassic\swtoremu"
echo [launcher] Starting SWTORClassic F96-echo run at %date% %time%
call "Run-SWTORClassic-Trace-Tython-F96Echo.cmd"
echo [launcher] Run-SWTORClassic-Trace-Tython-F96Echo.cmd exited with %errorlevel%
