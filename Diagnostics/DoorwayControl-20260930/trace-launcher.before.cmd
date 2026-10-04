@echo off
REM ===========================================================================
REM Instrumented world-entry run for tython. Use this INSTEAD OF
REM Run-SWTORClassic-With-Status.cmd.
REM
REM The servers must NOT already be running, otherwise their environment was
REM fixed when they started and these switches will be ignored.
REM
REM This file only sets configuration and launches. It does not record the
REM history behind each switch; that lives in:
REM   Diagnostics\WorldEntry-Checkpoint-20260924.md
REM   Diagnostics\Ability-Gate-Findings-20260925.md
REM   Diagnostics\Ability-Result-Contract-20260926.md
REM ===========================================================================

REM --- 1. ACTIVE -------------------------------------------------------------
REM All tracing is read-only: no value is written, no accessor invoked.

REM Verbose logging. AREA_PAYLOADS also prints each CRT's length and SHA256 so
REM emitted bytes can be diffed against the .acrt fixtures on disk.
set SWTOR_TRACE_AREA_PAYLOADS=1
set SWTOR_TRACE_RPC_CALLS=1
set SWTOR_TRACE_EVENT_DISPATCH=1
set SWTOR_TRACE_LOADING_SCREEN=1

REM World entry. A missing .acrt suppresses its whole transaction rather than
REM sending a zero-length one.
set SWTOR_CRT_MISSING_MODE=skip

REM Player-state spoofing. Together these let the character move and load:
REM   MOBILITY_IN_CRT16        staMobility travels alone in CRT16, because field 9
REM                            poisons any record it shares and freezes the client.
REM   STATMAP_AND_LOADED      modMetaStatComputed_Shared + chrPlayerLoaded in CRT17.
REM   REMOVE_SAFE_LOGIN_EFFECT  strips the immobilizing /0/2 effect from CRT2.
REM The client has no timeout: without chrPlayerLoaded=true the cast never
REM completes, so all three are required together.
set SWTOR_MOBILITY_IN_CRT16=1
set SWTOR_STATMAP_AND_LOADED=1
set SWTOR_REMOVE_SAFE_LOGIN_EFFECT=1

REM Kept for isolation only. A prior run proved the effect is created elsewhere
REM and that omitting this notification alone does not release mobility.
set SWTOR_SUPPRESS_SAFE_LOGIN_EFFECT=1

REM Area entry. "AreaServer" is the narrow compatibility state that produced a
REM fully rendered world; the captured packet's empty state string leaves the
REM local character and NPCs absent and world assets partially initialised.
set SWTOR_AREA_ENTER_STATE=AreaServer
set SWTOR_POST_STATE_ON_ENTER=0

REM --- 2. ALTERNATIVES (measured variants, all OFF) --------------------------
REM Record-shape bisects used to isolate the staMobility behaviour. Enabling more
REM than one makes the result uninterpretable.
REM   PLAYERLOADED_ONLY    CRT17 = {129} only. Proved the field applies alone.
REM   MOBILITY_AND_LOADED  CRT17 = {9, 129}. Proved field 9 breaks a record.
set SWTOR_PLAYERLOADED_ONLY=
set SWTOR_MOBILITY_AND_LOADED=

REM --- 3. DISABLED (deliberately off) ---------------------------------------
REM Probes removed after they stalled the client. Both walked the player field
REM chain inline on the travel-start breakpoint; the container probe prevented
REM reaching character select at all. The question they addressed (does the live
REM ablContainer hold entries?) is unanswered and must be re-asked from a
REM passive breakpoint.
REM set SWTOR_TRACE_ABILITY_GATE=1
REM set SWTOR_TRACE_ABILITY_EFFECTS=1
REM set SWTOR_TRACE_ABILITY_CONTAINER=1

REM Overrides the ability activation reply (selector 1279C371:001703D5)
REM independently of the
REM 30-second keepalive sharing the same opcode. Unset = inherit
REM SWTOR_RPC_REPLY_MODE, which is the current behaviour.
REM ECHO TEST RESULT: NEGATIVE, reverted. A controlled run (37 presses, 37
REM ability:echo-reply-sent decisions, no in-game effect, no regressions) showed
REM AreaRPCPollAck cannot work: GetType() returns PacketType.CMsgF96DCDB0, a
REM client-to-server opcode, and its body is the request blob rather than a
REM typed argument block. Prior notes blamed echo for making casts worse, but
REM that was a global echo run before the sub=29 dispatch existed.
REM set SWTOR_ABILITY_REPLY_MODE=echo

REM Native inbound-dispatch and the April ablOracle SCPT now identify the exact
REM typed completion RPC. "complete" replies with OnQueuedAbilityResult using
REM the ability-spec and request id decoded from this activation.
set SWTOR_ABILITY_REPLY_MODE=complete

REM First authoritative effect-event experiment. The JP effEvent exports map
REM the queued activation to effEventActivateRequestId, caster, and effectSpec.
REM This sends an action-bearing self-target root event for both abilities. For
REM Force Might it also sends the dependent /3/4 AddEffect event. In the capture,
REM byte 0x2C is AbilityActivate and the following UInt32 is string length 19.
set SWTOR_ABILITY_EFFECT_EXPERIMENT=1

REM The accepted effEvent packets expire after two seconds and do not populate
REM effContainerPositive. This opt-in transaction creates the real /3/4 Force
REM Might, Shii-Cho, or Sprint effEffect instance and inserts it into
REM positive-container slots 2-4. Sprint and Shii-Cho also update the player's
REM replicated modal-active list so their quickbar state follows the buff.
set SWTOR_ABILITY_EFFECT_REPLICATION=1

REM Until NPC combat ownership is implemented, a hostile-target ability marks
REM the player in combat and ten seconds without another hostile activation
REM clears it. This exercises Sprint's real IsNotInCombat condition path.
set SWTOR_ABILITY_COMBAT_EXPERIMENT=1

REM Optional timed-effect expiry override for short diagnostics. Empty uses
REM the effect's real duration (Force Might is 3600000 ms).
set SWTOR_ABILITY_TIMED_TEST_MS=

REM Lets CheckContinue issue its genuine CheckPhaseNeedsContinue RPC instead of
REM the local fallback. This is the original world-entry stall: the legacy
REM server has no matching RPC, so the native loading screen's final
REM phase-confirmation step never completes. The launcher routes it to the
REM engine's own no-player fallback (PhaseNeedsContinue(false) -> FadeIn),
REM preserving asset and string-table waits. Empty keeps the fallback default.
set SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK=

REM Supply the reconstructed player phase-data object (CRT3) and deliver the
REM captured phase-info child in CRT1, before CRT2 creates the local player
REM character. chrCharacter.Replication_Create fires OnPlayerCharacterNodeReady
REM -> phsoracle.OnPhasedInstanceUpdated exactly once, and that method returns
REM early when the player has no phase-info child, so the child must already
REM exist when CRT2 is applied. Without that the phase banner never appears and
REM pc.GetPhasedInstance() stays invalid, which also blocks phsCanExit.
REM See Diagnostics/Phase-Mechanics-20260928.md.
REM Still outstanding for the doorway itself: the captured session schema
REM declares no engine trigger class at all - its 61 base classes are all GOM
REM game classes, with hydTriggerEntity the only trigger among them - so no
REM INSTANCE_GATEWAY trigger is ever replicated and GetTriggersByType(4) cannot
REM match one from the replication stream. Whether the client materialises the
REM doorway trigger from its own area data is what the probe below now tests.
REM Keeping the loading fallback enabled isolates this exit-path experiment.
set SWTOR_ENABLE_UNVERIFIED_CRT3=1
set SWTOR_CRT_OVERRIDE_DIRECTORY=%~dp0Diagnostics\GeneratedPhaseCandidate
rem Phase-exit probe: CORRECTED - ready to run, disabled by default.
rem The first version of this probe was invalid three ways at once, so its
rem "the client answered with nothing" result proves nothing:
rem   1. its "fresh" node ID 0x1AC688C980 is a live CRT1 object (record 4), so
rem      the transaction was an update and OnReplicationNodeCreate never re-ran;
rem   2. it reused CRT11's stream id 0x001B5023, which the startup bundle had
rem      already delivered, so the client can discard it as a duplicate stream;
rem   3. re-sending an existing instance node cannot re-fire the create handler.
rem The regenerated CRT18 is proven rather than asserted: node 0x1AC688C981 has
rem zero references across all 20 .acrt files, and stream 0x001B502E is the next
rem id after the capture's 0x001B5012..0x001B502D range. The payload is CRT1
rem object 3 (the captured instance) with only its 6-byte packed node ID changed.
rem Run by giving the interval a value, e.g.:
rem   set SWTOR_PHASE_INSTANCE_RETRY=40
rem Then watch the phase doorway. If the client holds the INSTANCE_GATEWAY
rem trigger, the create handler attaches a gateway and a phsGatewayFx portal
rem appears at the phase door. Nothing appearing means the trigger is absent
rem client-side and must come from server-side area-object streaming.
rem Regenerate the fixture with:
rem   python Diagnostics/Generate-PhaseInstanceDuplicate.py
rem Preset SWTOR_PHASE_INSTANCE_RETRY before calling this script to run the
rem probe; see Run-SWTORClassic-PhaseExitProbe.cmd. An empty value keeps it off.
if not defined SWTOR_PHASE_INSTANCE_RETRY set SWTOR_PHASE_INSTANCE_RETRY=
if not defined SWTOR_PHASE_INSTANCE_RETRY_START set SWTOR_PHASE_INSTANCE_RETRY_START=25
if not defined SWTOR_PHASE_INSTANCE_RETRY_CRT set SWTOR_PHASE_INSTANCE_RETRY_CRT=18
if not defined SWTOR_PHASE_INSTANCE_RETRY_MAX set SWTOR_PHASE_INSTANCE_RETRY_MAX=1

rem Spawn placement. Keep this empty to use the captured Masters' Retreat
rem doorway (inside the phase): the level-1 Jedi Knight is supposed to start
rem inside the story area and exit by walking out the door. A value here only
rem overrides the placement for diagnostics (e.g. the Gnarls arrival trigger at
rem -16.0,-2.2,-99.5); leaving the character in-phase while placed outside is an
rem invalid state, not a movement bug.
rem
rem [ROOM-LOAD EXPERIMENT] Spawn past the doorway wall (world X=-62.92) into
rem gnarls_new to test whether the client loads the exterior room's collision on
rem its own (position-driven) or requires a server signal. Outcome: standing on a
rem floor = client-position-driven; falling / nothing renders = server-signal.
rem NOTE: -60,-6.9,-127.67 turned out to be the Tython medcenter (not gnarls_new)
rem and produced an invalid in-phase/outside state (immobilized). Left OFF below.
rem Set back to -64.87,-6.9,-127.67 to restore the normal in-phase spawn.
set SWTOR_SPAWN_POSITION=
REM Extra client-side probes, normally off. The filtered Hero getter observer
REM cannot see ablUserModalActiveSpecs because this script path uses compiled
REM field offsets rather than the generic getter.
REM The phase scripts access their fields through compiled offsets, so the
REM generic getter observer cannot see the doorway path.
set SWTOR_TRACE_PLAYER_FIELDS=1
set SWTOR_TRACE_PLAYER_LOADED_ACCESS=
set SWTOR_TRACE_REPLICATION_CREATE=

REM --- 4. ECHO --------------------------------------------------------------
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
echo [trace] SWTOR_AREA_ENTER_STATE=%SWTOR_AREA_ENTER_STATE%
echo [trace] SWTOR_POST_STATE_ON_ENTER=%SWTOR_POST_STATE_ON_ENTER%
echo [trace] SWTOR_NO_STATUS_PAUSE=%SWTOR_NO_STATUS_PAUSE%
echo [trace] SWTOR_AREA_POLL_MODE=%SWTOR_AREA_POLL_MODE%
echo [trace] SWTOR_RPC_REPLY_MODE=%SWTOR_RPC_REPLY_MODE%
echo [trace] SWTOR_RPC_RESULT_A=%SWTOR_RPC_RESULT_A%
echo [trace] SWTOR_RPC_RESULT_B=%SWTOR_RPC_RESULT_B%
echo [trace] SWTOR_ABILITY_REPLY_MODE=%SWTOR_ABILITY_REPLY_MODE%
echo [trace] SWTOR_ABILITY_EFFECT_EXPERIMENT=%SWTOR_ABILITY_EFFECT_EXPERIMENT%
echo [trace] SWTOR_ABILITY_EFFECT_REPLICATION=%SWTOR_ABILITY_EFFECT_REPLICATION%
echo [trace] SWTOR_ABILITY_COMBAT_EXPERIMENT=%SWTOR_ABILITY_COMBAT_EXPERIMENT%
echo [trace] SWTOR_ABILITY_TIMED_TEST_MS=%SWTOR_ABILITY_TIMED_TEST_MS%
echo [trace] SWTOR_ENABLE_UNVERIFIED_CRT3=%SWTOR_ENABLE_UNVERIFIED_CRT3%
echo [trace] SWTOR_CRT_OVERRIDE_DIRECTORY=%SWTOR_CRT_OVERRIDE_DIRECTORY%
echo [trace] SWTOR_PHASE_INSTANCE_RETRY=%SWTOR_PHASE_INSTANCE_RETRY% - empty means probe disabled
echo [trace] === ALTERNATIVES (all off) ===
echo [trace] SWTOR_PLAYERLOADED_ONLY=%SWTOR_PLAYERLOADED_ONLY%
echo [trace] SWTOR_MOBILITY_AND_LOADED=%SWTOR_MOBILITY_AND_LOADED%
echo [trace] === DISABLED ===
echo [trace] SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK=%SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK%
echo [trace] SWTOR_TRACE_PLAYER_FIELDS=%SWTOR_TRACE_PLAYER_FIELDS%
echo [trace] SWTOR_TRACE_PLAYER_LOADED_ACCESS=%SWTOR_TRACE_PLAYER_LOADED_ACCESS%
echo [trace] SWTOR_TRACE_REPLICATION_CREATE=%SWTOR_TRACE_REPLICATION_CREATE%

set SWTOR_NO_STATUS_PAUSE=1

REM Area poll policy. AreaModulesList is the readiness gate and must be echoed.
REM The others are client character-sync traffic, not verified request/reply
REM pairs, and must not be reflected back.
set SWTOR_AREA_POLL_MODE=AreaModulesList=Echo;CMsg61116AD5=Swallow;CMsg7CB9A193=Swallow;CMsgC26464A9=Swallow;CMsgCCACB51D=Swallow

REM Script RPC replies. "swallow" sends nothing, leaving the client's own cast
REM timer in play. Echo and ack send a client-to-server opcode, and SMsgResults
REM frames two strings where a typed argument block is required. Ability
REM activation is handled independently by SWTOR_ABILITY_REPLY_MODE above. The remaining
REM sub=10 struct-62 NPC request still has only an empty captured shell.
REM See Diagnostics\Ability-Result-Contract-20260926.md.
set SWTOR_RPC_REPLY_MODE=swallow
set SWTOR_RPC_RESULT_A=true
set SWTOR_RPC_RESULT_B=true

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
