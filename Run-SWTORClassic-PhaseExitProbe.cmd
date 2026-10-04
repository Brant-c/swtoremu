@echo off
REM ===========================================================================
REM Phase-exit probe run.
REM
REM Same as Run-SWTORClassic-Trace-Tython.cmd, but with the corrected
REM duplicate-instance probe enabled, so we can learn whether the client
REM already holds the INSTANCE_GATEWAY trigger for the Masters' Retreat doorway.
REM
REM What it sends: one extra AreaClientReplicationTransaction (CRT 18), 25
REM seconds after world entry, carrying a single phsClassPhasedInstance create
REM for the master-retreat instance on node 0x1AC688C981 with stream id
REM 0x001B502E. Both identifiers are *proven* unused across all .acrt files by
REM Diagnostics/Generate-PhaseInstanceDuplicate.py, which refuses to write
REM otherwise.
REM
REM Why a new node is required: GetTriggersByType(4) is only consulted inside
REM phsPhasedInstance.OnReplicationNodeCreate, and the engine does not re-fire
REM that callback for a node that already exists. The first version of this
REM probe re-sent an existing node ID on an already-delivered stream id, so it
REM could never have shown anything.
REM
REM What to watch: the phase doorway. If the client holds the INSTANCE_GATEWAY
REM trigger, the create handler attaches a gateway and a phsGatewayFx portal
REM appears at the phase door. Nothing appearing means the trigger is absent
REM client-side and has to come from server-side area-object streaming.
REM
REM Expected side effect, NOT a failure: the duplicate instance overwrites
REM phsActiveInstances[phsNameID] while the phase-info child still points at the
REM original node 0x1AC688C97E. The new instance's eligibility therefore reads
REM as not-phsCanExit, which is the transition that writes Collidable=1 on the
REM phase region volumes, so the boundary may become more solid rather than less.
REM
REM Verify the run afterwards with:
REM   Select-String -Path SharpServer\bin\Debug\NexusToR.log -Pattern PhaseInstanceRetry
REM Two lines are expected: "enabled, CRT 18, first delay 25s" and
REM "duplicate-instance create 1/1 sent".
REM
REM See Diagnostics/PhaseExit-Checkpoint-20260928.md.
REM ===========================================================================

REM Seconds after world entry before the probe fires, then only one send.
set SWTOR_PHASE_INSTANCE_RETRY=40
set SWTOR_PHASE_INSTANCE_RETRY_START=25
set SWTOR_PHASE_INSTANCE_RETRY_CRT=18
set SWTOR_PHASE_INSTANCE_RETRY_MAX=1

call "%~dp0Run-SWTORClassic-Trace-Tython.cmd"
exit /b %errorlevel%