# Native room log — experiment 08, prepared, not yet run

Purpose: distinguish failure to select gnarls_new from failure to activate
its content. Diagnostic only, no server/packet changes, no doorway fix yet.

## Native derivation

Primary confidence: Client-derived. April listing excerpts verified against
pinned PE bytes: ../PhaseLifecycle-20260930/native-room-offline/.

| Target | Contract | Evidence |
| --- | --- | --- |
| B90CF0 registration/lookup | ECX area, one stack pointer, EAX returned room, ret4 | area-register.txt: argument D0E, first word used in UTF16 _everywhere_ comparison DB6, existing/new return D31/DF5, ret E08 |
| B91AE0 selection change | ECX area, one stack room pointer, ret4 | room-selection-change.txt: area+298 compared B0B, written B60, activation B7C, ret DEC |
| B7C390 activation | ECX room, three stack slots, ret0C | room-activate.txt: arguments +8/+C/+10, already-active +8C==3 branch, otherwise immediate +90==6 branch, deferred C55B, returns C3DA/C595 |

+8C/+90 are numeric states; neither proves full asset/collision readiness.
Already-active +8C==3 can take the content-apply path regardless of +90.
Area+298 selection alone does not prove player+98 association or the wall cause.
EnviroScheme room+1BC/area+400 is separate from physical destination selection.
No inferred missing packet is introduced.

Three exact 48-byte prefixes at known RVAs, adjusting embedded SEH handler VA
for the loaded image base. Any mismatch disables all three with UNSUPPORTED.
INSTALLED is emitted only after the existing Detours transaction commits.
Live installation still needs confirmation.

## Bounded logging

Opt-in SWTOR_TRACE_ROOM_SELECTION=1. Default startup leaves it unset.
Existing hook log, process IDs on every room event. Names max127characters;
512 registration events, 256 selection-change enter/return pairs, 256
activation enter/return pairs. Same-room selections are passed through without
logging. Explicit limit marker; absence after that limit is inconclusive.
SEH-protected reads of event argument names and named fields only. FFFFFFFF
means failed read; null object states are 0. No scans, full dumps, extra native
calls, game-object writes, retries or network messages. Each original call
forwarded once even after cap. Incoming/outgoing Win32 LastError preserved.

## Checks passed

Release Win32 hook build. DLL SHA256:
1B30BFD4DE2C822C83E36B23EF7C62624F7CBDA0589D1A130BD1AD154511E0DD.
Verify-Prefixes.py: all144 exact bytes match pinned April PE.
Test-RoomTrace.exe: local x86 ABI forwarding/return,1542 original calls including
capped events, LastError, fault reads, relocation acceptance,144 mutations
rejected. Native stubs are not live Detours proof.
Dedicated VerifyOnly: no processes launched; all28 prior CRT3-off settings
identical, only additional ROOM_SELECTION=1. See config-comparison.json.
Server hash unchanged; no protocol changes, so protocol tests not repeated.

## Operator run and deciding logs

Use D:\SWTORClassic\swtoremu\Run-SWTORClassic-RoomSelection.cmd.
Old clients/servers must be closed. Load Tython, stand still, no abilities.
Before crossing confirm fresh launch timestamp, installed DLLhash, CRT3
suppressed, NativeRoomHook INSTALLED for mainclientPID, and registration
names/pointers for gnarls_new and retreat rooms in same area. Map initial
selection by pointer. Do not mix secondary-client pointers.
If names/prefixes fail or cap reached, preserve failure; no repeated crossings
without a concrete correction. No external observer READY gate.
Then request one crossing and stop at wall/outside, client still open.
Correlate accepted C5 / unchanged46-byte destroy with native select/activate.
Preserve fresh logs with Preserve-Logs.ps1 before closing/restart.

Logs: SharpServer/bin/Debug/NexusToR.log;
nexusclient/nexusclient/nexus_hook.log;
Diagnostics/RoomSelection-20260930/launcher-console.log, launcher-errors.log,
launch-requested.txt. New identity.csv pins inputs and new header.

Before source/DLL/baselineidentity preserved as ToR.before.cpp,
MemoryMan.before.dll and baseline-identity.csv. Old lifecycle identity unchanged:
old launchers reject changed hook rather than silently alter old baseline.
Verbose base launcher, packet order and reference tree unchanged.
Rollback with processes closed: restore before source/DLL to original paths,
verify old hashes before using old baseline launcher. No need to delete new header.
