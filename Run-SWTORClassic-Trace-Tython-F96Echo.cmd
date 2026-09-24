@echo off
REM F96 echo experiment (Run B) on the trace-tython path.
REM Identical to Run-SWTORClassic-Trace-Tython.cmd plus SWTOR_F96_ECHO=1.
set SWTOR_TRACE_AREA_PAYLOADS=1
set SWTOR_CRT_MISSING_MODE=skip
set SWTOR_F96_ECHO=1

echo [trace-f96echo] SWTOR_TRACE_AREA_PAYLOADS=%SWTOR_TRACE_AREA_PAYLOADS%
echo [trace-f96echo] SWTOR_CRT_MISSING_MODE=%SWTOR_CRT_MISSING_MODE%
echo [trace-f96echo] SWTOR_F96_ECHO=%SWTOR_F96_ECHO%
echo.

call "%~dp0Run-SWTORClassic.cmd"
