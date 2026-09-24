@echo off
REM F96 echo experiment run (Run B).
REM Same servers as Run-SWTORClassic.cmd plus SWTOR_F96_ECHO=1.
REM Keep CRT3 skip + area payload trace from the trace-tython launcher.
set SWTOR_TRACE_AREA_PAYLOADS=1
set SWTOR_CRT_MISSING_MODE=skip
set SWTOR_F96_ECHO=1

echo [f96echo] SWTOR_TRACE_AREA_PAYLOADS=%SWTOR_TRACE_AREA_PAYLOADS%
echo [f96echo] SWTOR_CRT_MISSING_MODE=%SWTOR_CRT_MISSING_MODE%
echo [f96echo] SWTOR_F96_ECHO=%SWTOR_F96_ECHO%
echo.

call "%~dp0Run-SWTORClassic.cmd"
