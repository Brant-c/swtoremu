@echo off
REM ---------------------------------------------------------------------------
REM Instrumented world-entry run for the tython area-load crash.
REM
REM Use this INSTEAD OF Run-SWTORClassic-With-Status.cmd for the next attempt.
REM It behaves exactly like Run-SWTORClassic.cmd except that it first sets the
REM trace switches, which are inherited by the servers it starts.
REM
REM The servers must NOT already be running, otherwise their environment was
REM fixed when they started and these switches will be ignored.
REM
REM Switches:
REM   SWTOR_TRACE_AREA_PAYLOADS=1   Log every area packet's plaintext bytes
REM                                 plus each CRT's length and SHA256, so the
REM                                 emitted bytes can be compared against the
REM                                 .acrt fixtures on disk.
REM   SWTOR_CRT_MISSING_MODE=skip   A missing .acrt suppresses the whole
REM                                 AreaClientReplicationTransaction instead of
REM                                 sending a zero-length one. CRT3 is currently
REM                                 disabled, so this decides whether the
REM                                 current crash is caused by the empty packet
REM                                 or by something unrelated to CRT traffic.
REM   SWTOR_TRACE_RPC_CALLS=1       Enable the diagnostic client hook for the
REM                                 outbound CMsgF96DCDB0 wrapper. It records
REM                                 the C7 call ID, payload, and caller address
REM                                 to nexusclient\nexusclient\nexus_hook.log.
REM   SWTOR_TRACE_EVENT_DISPATCH=1  Trace the common world/event dispatcher,
REM                                 including event class, payload fingerprint,
REM                                 concrete handler RVA, and rate-limited bytes.
REM ---------------------------------------------------------------------------

set SWTOR_TRACE_AREA_PAYLOADS=1
set SWTOR_CRT_MISSING_MODE=skip
set SWTOR_TRACE_RPC_CALLS=1
set SWTOR_TRACE_EVENT_DISPATCH=1

REM --- RPC replies (RpcReply): the client re-fires CMsgF96DCDB0 / CMsg4A765897
REM --- as script RPC requests; answering with SMSG_RESULTS (0xD5280283) is what
REM --- lets the pending call complete. Read at send time.
REM   SWTOR_RPC_REPLY_MODE  mirror (default) | results | echo | swallow | ack
REM   SWTOR_RPC_RESULT_A    result name  (results mode; default "true")
REM   SWTOR_RPC_RESULT_B    result value (both modes; default "true")
set SWTOR_RPC_REPLY_MODE=mirror
set SWTOR_RPC_RESULT_A=true
set SWTOR_RPC_RESULT_B=true

REM --- Area polls: AreaModulesList remains the readiness gate. The saved
REM --- world-entry capture showed that echoing CMsg61116AD5 (character sync)
REM --- was the one useful area handshake reply; keep the other experimental
REM --- poll replies swallowed so this run changes only that variable.
set SWTOR_AREA_POLL_MODE=AreaModulesList=Echo;CMsg61116AD5=Echo;CMsg7CB9A193=Swallow;CMsgC26464A9=Swallow;CMsgCCACB51D=Swallow
set SWTOR_AREA_ENTER_STATE=AreaServer

echo [trace] SWTOR_TRACE_AREA_PAYLOADS=%SWTOR_TRACE_AREA_PAYLOADS%
echo [trace] SWTOR_CRT_MISSING_MODE=%SWTOR_CRT_MISSING_MODE%
echo [trace] SWTOR_TRACE_RPC_CALLS=%SWTOR_TRACE_RPC_CALLS%
echo [trace] SWTOR_TRACE_EVENT_DISPATCH=%SWTOR_TRACE_EVENT_DISPATCH%
echo [trace] SWTOR_RPC_REPLY_MODE=%SWTOR_RPC_REPLY_MODE%
echo [trace] SWTOR_RPC_RESULT_A=%SWTOR_RPC_RESULT_A%
echo [trace] SWTOR_RPC_RESULT_B=%SWTOR_RPC_RESULT_B%
echo [trace] SWTOR_AREA_POLL_MODE=%SWTOR_AREA_POLL_MODE%
echo [trace] SWTOR_AREA_ENTER_STATE=%SWTOR_AREA_ENTER_STATE%
echo.
echo [trace] SERVER readiness marker: when the log shows
echo [trace]   "AreaStartupBundle: area startup sent"
echo [trace] the server has emitted the area startup packet sequence. If the
echo [trace] client is still on the load screen after that, grab the CLIENT log:
echo [trace]   %%USERPROFILE%%\Documents\SWTOR*\swtor_*\swtor.log
echo [trace] and paste its tail (the last 60 lines) so we can see whether the
echo [trace] client reached CS_INGAME or stalled at CS_GAME_LAUNCHING. DO NOT
echo [trace] close the client before capturing its tail — the client must stay
echo [trace] alive past the resource-worker idle lines to prove readiness.
echo.
echo [trace] SERVER console captured to: %USERPROFILE%\NexusToR.server.out
echo [trace] After the run, check that file for:
echo [trace]   "AreaStartupBundle: area startup sent" <- area bundle emitted
echo [trace]   "Client '...' disconnected" <- client session ended
echo.

REM Install the freshly built, workspace-local diagnostic hook. Preserve the
REM previously installed DLL once so this run is reversible. Also rotate the
REM append-only hook log so the post-run capture contains only this attempt.
set "HOOK_BUILD=%~dp0Client\Hook\Bin\x86\MemoryMan.dll"
set "CLIENT_DIR=%~dp0nexusclient\nexusclient"
set "CLIENT_HOOK=%CLIENT_DIR%\MemoryMan.dll"
set "HOOK_LOG=%CLIENT_DIR%\nexus_hook.log"

tasklist /FI "IMAGENAME eq swtor.exe" | find /I "swtor.exe" >nul
if not errorlevel 1 (
    echo [trace] ERROR: swtor.exe is already running. Close it before installing the trace hook.
    pause & exit /b 1
)
if not exist "%HOOK_BUILD%" (
    echo [trace] ERROR: Diagnostic MemoryMan.dll not found. Run build-hook.cmd first.
    pause & exit /b 1
)
if not exist "%CLIENT_DIR%\Nexus.dll" (
    echo [trace] ERROR: Client Nexus.dll not found; refusing to replace MemoryMan.dll.
    pause & exit /b 1
)
if exist "%CLIENT_HOOK%" if not exist "%CLIENT_HOOK%.before-rpc-trace.bak" (
    copy /Y "%CLIENT_HOOK%" "%CLIENT_HOOK%.before-rpc-trace.bak" >nul
    if errorlevel 1 (
        echo [trace] ERROR: Could not back up the installed MemoryMan.dll.
        pause & exit /b 1
    )
)
copy /Y "%HOOK_BUILD%" "%CLIENT_HOOK%" >nul
if errorlevel 1 (
    echo [trace] ERROR: Could not install the diagnostic MemoryMan.dll.
    pause & exit /b 1
)
if exist "%HOOK_LOG%" (
    copy /Y "%HOOK_LOG%" "%~dp0Diagnostics\nexus_hook.before-latest.log" >nul
    if errorlevel 1 (
        echo [trace] ERROR: Could not preserve the previous hook log.
        pause & exit /b 1
    )
    del /Q "%HOOK_LOG%"
)
echo [trace] Diagnostic hook installed; previous DLL/log preserved.
echo.

REM Start the shard-list server (idempotent — Run-SWTORClassic.cmd does this too,
REM but we inline it so the trace cmd is self-standing).
tasklist /FI "IMAGENAME eq ShardListServer.exe" | find /I "ShardListServer.exe" >nul
if errorlevel 1 (
  start "SWTORClassic shard list" /D "%~dp0SharpServer\ShardListServer\bin\Debug" "%~dp0SharpServer\ShardListServer\bin\Debug\ShardListServer.exe"
)

REM Never launch a second world server over an existing process. Its inherited
REM environment and locked executable would make this run silently stale.
tasklist /FI "IMAGENAME eq NexusToRServer.exe" | find /I "NexusToRServer.exe" >nul
if not errorlevel 1 (
    echo [trace] ERROR: NexusToRServer.exe is already running. Stop it and rerun this launcher.
    pause & exit /b 1
)

REM NexusToR.server.out — the area-startup marker + client disconnect line land
REM in that file, no copy/paste needed.
if not exist "%~dp0SharpServer\bin\Debug\NexusToRServer.exe" (
    echo [trace] ERROR: NexusToRServer.exe not found. Run a build first.
    pause & exit /b 1
)
start "SWTORClassic server" /D "%~dp0SharpServer\bin\Debug" /LOW ^
  "%~dp0SharpServer\bin\Debug\NexusToRServer.exe" > "%USERPROFILE%\NexusToR.server.out" 2>&1

REM Give the server a moment to bind before the client tries to connect.
timeout /t 2 /nobreak >nul

call "%~dp0Run-Old-Client-Compatible.cmd"
set "CLIENT_RESULT=%errorlevel%"

REM Collect stable workspace copies for post-run analysis.
if exist "%HOOK_LOG%" copy /Y "%HOOK_LOG%" "%~dp0Diagnostics\last-nexus-hook.log" >nul
if exist "%USERPROFILE%\NexusToR.server.out" copy /Y "%USERPROFILE%\NexusToR.server.out" "%~dp0Diagnostics\last-server-out.log" >nul
if exist "%~dp0SharpServer\bin\Debug\NexusToR.log" copy /Y "%~dp0SharpServer\bin\Debug\NexusToR.log" "%~dp0Diagnostics\last-server-full.log" >nul

if exist "%~dp0Diagnostics\last-nexus-hook.log" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\Analyze-TythonTrace.ps1"
)

echo.
echo [trace] Post-run logs:
echo [trace]   %~dp0Diagnostics\last-nexus-hook.log
echo [trace]   %~dp0Diagnostics\last-server-out.log
echo [trace]   %~dp0Diagnostics\last-compatibility-run.log
exit /b %CLIENT_RESULT%
