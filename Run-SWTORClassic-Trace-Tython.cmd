@echo off
REM ===========================================================================
REM Instrumented world-entry run for tython. Use this INSTEAD OF
REM Run-SWTORClassic-With-Status.cmd.
REM
REM The servers must NOT already be running, otherwise their environment was
REM fixed when they started and these switches will be ignored.
REM
REM Configuration is grouped:
REM   1. ACTIVE       what this run actually does
REM   2. ALTERNATIVES measured variants, all OFF, never enable more than one
REM   3. DISABLED     deliberately off, with the reason
REM   4. ECHO         startup summary
REM
REM Investigation history: Diagnostics\Ability-Gate-Findings-20260925.md
REM ===========================================================================

REM --- 1. ACTIVE -------------------------------------------------------------
REM All tracing below is read-only: no value is written, no accessor invoked.

REM AREA_PAYLOADS   plaintext of every area packet, plus each CRT's length and
REM                 SHA256, so emitted bytes can be diffed against the .acrt
REM                 fixtures on disk.
REM RPC_CALLS       client hook on the outbound CMsgF96DCDB0 wrapper; records
REM                 the C7 call id, payload and caller address to
REM                 nexusclient\nexusclient\nexus_hook.log.
REM EVENT_DISPATCH  the common world/event dispatcher: event class, payload
REM                 fingerprint, concrete handler RVA, rate-limited bytes.
REM LOADING_SCREEN  only guiGFxLoadingScreen's GOM class/field definition
REM                 lookups, filtered to ids decoded from client.gom.
REM ABILITY_GATE    the proven "not ready yet" chain: chrPlayerLoaded (the
REM                 replicated input), ablUserCacheIsFrozen (the cached gate
REM                 result), ablUserCacheIsLucid and
REM                 ablUserCacheGlobalTimerRunning. It also resolves three
REM                 control fields whose values are independently known
REM                 (chrIsMe, chrCharacterPlayMode, chrCharacterPhaseMode), so
REM                 a "3 pass" verdict means the gate readings can be believed.
REM                 Source: _JPEXTRACT\ablUserComponentClassMethods.txt.
set SWTOR_TRACE_AREA_PAYLOADS=1
set SWTOR_TRACE_RPC_CALLS=1
set SWTOR_TRACE_EVENT_DISPATCH=1
set SWTOR_TRACE_LOADING_SCREEN=1
REM set SWTOR_TRACE_ABILITY_GATE=1  (no handler in the current source; probe removed)
REM ABILITY_EFFECTS reads chrPlayerCharacter.f148 (ablContainer,
REM 0x400000118A7E6088 -- note gom_type_names.xml also names 0x40000002F8C347F1
REM "ablContainer" but the player does not have that one), follows the ClassRef to
REM the live container node, and dumps its conContents raw bytes so the live read
REM can be diffed against the 208-byte capture that Decode-CrtValues.py now
REM decodes exactly (count 27, then 27x slot+CC+5, then 2x CF+8 shared refs).
REM Read-only. A mismatch means the node reference is wrong, not the field -- the
REM probe reports which of the three failure modes it hit rather than going silent.
REM Investigation: Diagnostics\Ability-Gate-Findings-20260925.md, phase (2).
REM set SWTOR_TRACE_ABILITY_EFFECTS=1  (no handler in the current source; probe removed)
REM A missing .acrt suppresses the whole transaction instead of sending a
REM zero-length one. CRT3 is disabled, so this decides whether the remaining
REM problem is caused by the empty packet or by something unrelated to CRT
REM traffic.
set SWTOR_CRT_MISSING_MODE=skip
REM ABILITY_CONTAINER is intentionally OFF. The probe that read it walked the
REM player field chain inside the travel-start breakpoint and stalled the client
REM before character select. The question it answered (does the live
REM ablContainer hold entries?) is still open, but it must be re-asked from a
REM passive breakpoint, not inline on the travel path.
REM set SWTOR_TRACE_ABILITY_CONTAINER=1

REM Replication shaping. Measured record shapes for the player node
REM 0x4000010E218A839C (structure 26, 215 fields):
REM
REM   {100}          captured; accepted, changes nothing
REM   {129}          chrPlayerLoaded=1  frozen=0  abilities fire
REM   {100, 129}     chrPlayerLoaded=1  frozen=0  abilities fire
REM   {9, 129}       chrPlayerLoaded=0  frozen=1
REM   {9, 100, 129}  chrPlayerLoaded=0  frozen=1
REM
REM staMobility is the one field that poisons a shared record, so it travels
REM alone in CRT16 while CRT17 carries the stat map and the load flag. The two
REM together are the first configuration observed to give movement AND an
REM unlocked ability bar at the same time.
set SWTOR_MOBILITY_IN_CRT16=1
set SWTOR_STATMAP_AND_LOADED=1
REM CRT2 create still suppresses the Safe Login Immunity effect, and CRT17
REM still carries the schema-derived mobility and chrPlayerLoaded merge.
set SWTOR_REMOVE_SAFE_LOGIN_EFFECT=1
REM Effect fixture 1 reports Safe Login Immunity. Suppression is retained for
REM isolation, although a prior run proved the effect is created elsewhere;
REM omitting this replicated notification alone does not release mobility.
set SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT=1

REM 2026-09-25: switched back from "echo" to "swallow" for the ability work.
REM "echo" answers an ability activation with AreaRPCPollAck -- the poll-ack
REM shape that belongs to AreaModulesList -- carrying the request body. The
REM client most likely misreads that as a result, and OnAbilityResult's failure
REM branch calls _InternalAbilityCancel, which fits "animation plays, then no
REM cast bar and no buff". "swallow" sends nothing, so the client's own cast
REM timer (ablCastTimeEnd, set client-side by SetClientCastingTime) is the only
REM thing in play. If a cast bar appears under swallow, the echo was the poison.
REM   SWTOR_RPC_REPLY_MODE  mirror (default) | results | echo | swallow | ack
REM   SWTOR_RPC_RESULT_A    result name  (results mode; default "true")
REM   SWTOR_RPC_RESULT_B    result value (both modes; default "true")
REM mirror/results send SMSG_RESULTS, which native tracing showed reaches the
REM route map but is NOT the response contract for these packed RPC calls.
REM "ack" sends an empty poll-ack and is the next thing to try if swallow gets
REM a cast bar but never completes it.
REM
REM Two request shapes now reach us and neither has a real response yet:
REM   sub=29  ability activation. ablOracle.RequestAbilityActivate sends
REM            server untrustedMethods:OnRequestAbilityActivate(abilitySpec,
REM            requestId, syncTime, int, bool). Byte 29 of the body is a clean
REM            1,2,3... counter and is ablActiveRequestId, so replies can be
REM            correlated. OnAbilityResult only runs on FAILURE, so a successful
REM            ability cannot be signalled by an RPC reply at all - it has to
REM            arrive as a replicated effect in the positive effContainer. That
REM            is server behaviour still to be written.
REM   sub=10  area-object request for node 0x1AC6F6DC6D, which is structure
REM            62 chrNonPlayerCharacter. CRT12 is the only struct-62 record in
REM            the captures and it is an empty shell (inner=0, only staEnterIdle
REM            reset to default), so the client re-requests it ~21 times. This
REM            is missing content, not a protocol bug: re-sending the same
REM            bytes cannot populate an NPC.
set SWTOR_RPC_REPLY_MODE=swallow
set SWTOR_RPC_RESULT_A=true
set SWTOR_RPC_RESULT_B=true

REM Area polls. AreaModulesList remains the readiness gate. The others are
REM client character-sync traffic, not verified request/reply pairs, and must
REM not be reflected back: the old echo was experimental, non-canonical, and
REM was active immediately before the MemoryMan failure.
set SWTOR_AREA_POLL_MODE=AreaModulesList=Echo;CMsg61116AD5=Swallow;CMsg7CB9A193=Swallow;CMsgC26464A9=Swallow;CMsgCCACB51D=Swallow
REM The captured packet carries an empty state string, which leaves the local
REM character/NPCs absent and world assets only partially initialized.
REM "AreaServer" is the narrow client compatibility state that produced a
REM fully rendered world.
set SWTOR_AREA_ENTER_STATE=AreaServer
set SWTOR_POST_STATE_ON_ENTER=0
set SWTOR_NO_STATUS_PAUSE=1

REM --- 2. ALTERNATIVES -------------------------------------------------------
REM Record-shape bisects used to isolate the staMobility behaviour. All OFF.
REM The active configuration above is the combination that worked; the rest
REM are kept so a future regression can be re-bisected without re-deriving it.
REM   PLAYERLOADED_ONLY    CRT17 = {129} only. Proved the field applies alone.
REM   MOBILITY_AND_LOADED  CRT17 = {9, 129}. Proved field 9 breaks a record.
REM   (SWTOR_MOBILITY_IN_CRT16 and SWTOR_STATMAP_AND_LOADED above are the
REM   two active shapes; do not enable these alongside them.)
set SWTOR_PLAYERLOADED_ONLY=
set SWTOR_MOBILITY_AND_LOADED=

REM --- 3. DISABLED -----------------------------------------------------------
REM Leave the verified local fade-in fallback enabled. A diagnostic run with
REM the fallback disabled proved the original phase path stalls before it
REM constructs a CheckPhaseNeedsContinue RPC, so there is no captured request
REM to answer.
set SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK=
REM The 2026-09-24 schema-matched candidate is intentionally disabled. The
REM client rejected its authored CRT1 schema with "Unable to read field count".
REM Keep the files as offline evidence, but do not transmit them again until
REM the native type-description grammar has been reconstructed.
set SWTOR_CRT_OVERRIDE_DIRECTORY=
REM CRT3 is known-incomplete; only useful for decoder experiments.
set SWTOR_ENABLE_UNVERIFIED_CRT3=
REM The readiness values and the full Replication_Create path are verified, so
REM their breakpoint observers are off in favour of ABILITY_GATE.
set SWTOR_TRACE_PLAYER_FIELDS=
set SWTOR_TRACE_PLAYER_LOADED_ACCESS=
set SWTOR_TRACE_REPLICATION_CREATE=

REM --- 4. ECHO ---------------------------------------------------------------
echo [trace] === ACTIVE ===
echo [trace] SWTOR_TRACE_AREA_PAYLOADS=%SWTOR_TRACE_AREA_PAYLOADS%
echo [trace] SWTOR_TRACE_RPC_CALLS=%SWTOR_TRACE_RPC_CALLS%
echo [trace] SWTOR_TRACE_EVENT_DISPATCH=%SWTOR_TRACE_EVENT_DISPATCH%
echo [trace] SWTOR_TRACE_LOADING_SCREEN=%SWTOR_TRACE_LOADING_SCREEN%
echo [trace] SWTOR_CRT_MISSING_MODE=%SWTOR_CRT_MISSING_MODE%
echo [trace] SWTOR_MOBILITY_IN_CRT16=%SWTOR_MOBILITY_IN_CRT16%
echo [trace] SWTOR_STATMAP_AND_LOADED=%SWTOR_STATMAP_AND_LOADED%
echo [trace] SWTOR_REMOVE_SAFE_LOGIN_EFFECT=%SWTOR_REMOVE_SAFE_LOGIN_EFFECT%
echo [trace] SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT=%SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT%
echo [trace] SWTOR_RPC_REPLY_MODE=%SWTOR_RPC_REPLY_MODE%
echo [trace] SWTOR_AREA_POLL_MODE=%SWTOR_AREA_POLL_MODE%
echo [trace] SWTOR_AREA_ENTER_STATE=%SWTOR_AREA_ENTER_STATE%
echo [trace] SWTOR_POST_STATE_ON_ENTER=%SWTOR_POST_STATE_ON_ENTER%
echo [trace] SWTOR_NO_STATUS_PAUSE=%SWTOR_NO_STATUS_PAUSE%
echo [trace] === ALTERNATIVES (all off) ===
echo [trace] SWTOR_PLAYERLOADED_ONLY=%SWTOR_PLAYERLOADED_ONLY%
echo [trace] SWTOR_MOBILITY_AND_LOADED=%SWTOR_MOBILITY_AND_LOADED%
echo [trace] === DISABLED ===
echo [trace] SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK=%SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK%
echo [trace] SWTOR_CRT_OVERRIDE_DIRECTORY=%SWTOR_CRT_OVERRIDE_DIRECTORY%
echo [trace] SWTOR_ENABLE_UNVERIFIED_CRT3=%SWTOR_ENABLE_UNVERIFIED_CRT3%
echo [trace] SWTOR_TRACE_PLAYER_FIELDS=%SWTOR_TRACE_PLAYER_FIELDS%
echo [trace] SWTOR_TRACE_PLAYER_LOADED_ACCESS=%SWTOR_TRACE_PLAYER_LOADED_ACCESS%
echo [trace] SWTOR_TRACE_REPLICATION_CREATE=%SWTOR_TRACE_REPLICATION_CREATE%
echo.
echo.
echo [trace] SERVER readiness marker: when the log shows
echo [trace]   "AreaStartupBundle: area startup sent"
echo [trace] the server has emitted the area startup packet sequence. If the
echo [trace] client is still on the load screen after that, grab the CLIENT log:
echo [trace]   %%USERPROFILE%%\Documents\SWTOR*\swtor_*\swtor.log
echo [trace] and paste its tail (the last 60 lines) so we can see whether the
echo [trace] client reached CS_INGAME or stalled at CS_GAME_LAUNCHING. DO NOT
echo [trace] close the client before capturing its tail â€” the client must stay
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

REM scriptDef.list only registers script identities. The actual April SCPT
REM bodies live in this archive and are loaded by hash through the native TOR
REM repository. The stripped diagnostic client did not contain it, which left
REM guiGFxLoadingScreen registered but unable to load its cleanUp code.
set "SCRIPT_ARCHIVE_SOURCE=%~dp0Assets2012April\swtor_main_systemgenerated_gom_1.tor"
set "SCRIPT_ARCHIVE_CLIENT=%CLIENT_DIR%\swtor_main_systemgenerated_gom_1.tor"
if not exist "%SCRIPT_ARCHIVE_SOURCE%" (
    echo [trace] ERROR: Matching April script archive is missing: %SCRIPT_ARCHIVE_SOURCE%
    pause & exit /b 1
)
set "INSTALL_SCRIPT_ARCHIVE=0"
if not exist "%SCRIPT_ARCHIVE_CLIENT%" set "INSTALL_SCRIPT_ARCHIVE=1"
if exist "%SCRIPT_ARCHIVE_CLIENT%" for %%A in ("%SCRIPT_ARCHIVE_CLIENT%") do if not "%%~zA"=="9766441" set "INSTALL_SCRIPT_ARCHIVE=1"
if "%INSTALL_SCRIPT_ARCHIVE%"=="1" (
    copy /Y "%SCRIPT_ARCHIVE_SOURCE%" "%SCRIPT_ARCHIVE_CLIENT%" >nul
    if errorlevel 1 (
        echo [trace] ERROR: Could not install the April script archive.
        pause & exit /b 1
    )
    echo [trace] Installed the matching April native script archive.
) else (
    echo [trace] Matching April native script archive is already installed.
)

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

REM Start the shard-list server (idempotent â€” Run-SWTORClassic.cmd does this too,
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

REM NexusToR.server.out â€” the area-startup marker + client disconnect line land
REM in that file, no copy/paste needed.
if not exist "%~dp0SharpServer\bin\Debug\NexusToRServer.exe" (
    echo [trace] ERROR: NexusToRServer.exe not found. Run a build first.
    pause & exit /b 1
)
REM Rotate the append-only server log before starting this run. This keeps the
REM post-run analyzer from mistaking evidence from an older experiment for the
REM current attempt while preserving the previous file for comparison.
set "SERVER_LOG=%~dp0SharpServer\bin\Debug\NexusToR.log"
if exist "%SERVER_LOG%" (
    copy /Y "%SERVER_LOG%" "%~dp0Diagnostics\nexus-server.before-latest.log" >nul
    if errorlevel 1 (
        echo [trace] ERROR: Could not preserve the previous server log.
        pause & exit /b 1
    )
    del /Q "%SERVER_LOG%"
)
start "SWTORClassic server" /D "%~dp0SharpServer\bin\Debug" /LOW ^
  "%~dp0SharpServer\bin\Debug\NexusToRServer.exe" > "%USERPROFILE%\NexusToR.server.out" 2>&1

REM Give the server a moment to bind before the client tries to connect.
timeout /t 2 /nobreak >nul

call "%~dp0Run-Old-Client-Compatible.cmd"
set "CLIENT_RESULT=%errorlevel%"

REM Run-Old-Client-Compatible starts the game asynchronously. Wait briefly for
REM swtor.exe to appear, then keep this trace launcher alive until the client
REM closes so the snapshots below describe this run rather than the prior one.
set /a CLIENT_WAIT_TRIES=0
:wait_for_client_start
tasklist /FI "IMAGENAME eq swtor.exe" | find /I "swtor.exe" >nul
if not errorlevel 1 goto wait_for_client_exit
set /a CLIENT_WAIT_TRIES+=1
if %CLIENT_WAIT_TRIES% GEQ 30 goto collect_trace
timeout /t 1 /nobreak >nul
goto wait_for_client_start

:wait_for_client_exit
tasklist /FI "IMAGENAME eq swtor.exe" | find /I "swtor.exe" >nul
if errorlevel 1 goto collect_trace
timeout /t 2 /nobreak >nul
goto wait_for_client_exit

REM Collect stable workspace copies for post-run analysis.
:collect_trace
if exist "%HOOK_LOG%" powershell -NoProfile -Command "Copy-Item -LiteralPath '%HOOK_LOG%' -Destination '%~dp0Diagnostics\last-nexus-hook.log' -Force"
if exist "%USERPROFILE%\NexusToR.server.out" powershell -NoProfile -Command "Copy-Item -LiteralPath '%USERPROFILE%\NexusToR.server.out' -Destination '%~dp0Diagnostics\last-server-out.log' -Force"
if exist "%~dp0SharpServer\bin\Debug\NexusToR.log" powershell -NoProfile -Command "Copy-Item -LiteralPath '%~dp0SharpServer\bin\Debug\NexusToR.log' -Destination '%~dp0Diagnostics\last-server-full.log' -Force"

if exist "%HOOK_LOG%" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnostics\Analyze-TythonTrace.ps1" -HookLog "%HOOK_LOG%" -ServerLog "%SERVER_LOG%"
)

echo.
echo [trace] Post-run logs:
echo [trace]   %~dp0Diagnostics\last-nexus-hook.log
echo [trace]   %~dp0Diagnostics\last-server-out.log
echo [trace]   %~dp0Diagnostics\last-compatibility-run.log
exit /b %CLIENT_RESULT%
