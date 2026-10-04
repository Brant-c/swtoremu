@echo off
REM Separate CRT3 ablation. This changes only the reconstructed CRT3 gate from
REM the lifecycle-observer baseline; the normal Tython trace launcher supplies
REM the same startup, tracing, packet, and movement configuration.
set SWTOR_ENABLE_UNVERIFIED_CRT3=0
call "%~dp0Run-SWTORClassic-Trace-Tython.cmd"
