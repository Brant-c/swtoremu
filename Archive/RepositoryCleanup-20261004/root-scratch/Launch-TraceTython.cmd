@echo off
REM Launch the trace run in the background, capturing console output.
REM Use start /B to detach so this cmd returns immediately.
start /B cmd /c "\"D:\SWTORClassic\swtoremu\Run-SWTORClassic-Trace-Tython.cmd\" > "D:\SWTORClassic\swtoremu\Diagnostics\TraceTython-20260918-0214-console.log" 2>&1"
echo launched pid %ERRORLEVEL%
