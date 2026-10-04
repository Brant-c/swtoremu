# Doorway control preparation — experiment 2026-09-30-01

Status: PREPARED, NOT LAUNCHED. No native client result exists for this build.
Local preparation began on September 29 Toronto time; the experiment uses the
September 30 UTC date. Snapshot filenames retain local time and timezone files.

## Single change and fixture provenance

The bounded decoder is the baseline. The only additional gameplay/wire change
is removal of the unverified CRT18 send after the existing phase-info destroy.
The destroy serializer, startup order, hook binary, C5 decoder and unsupported
C7 rejection policy are unchanged. No new packet was added. The dormant
awareness/RPC helpers were not invoked or expanded.

Before the change, PhaseExit.OnMove called SendRoomStream. CRT.Has and CRT.Get
both used the filename `{area}-{areaID}-{areaCode}.18.acrt`, checking
SWTOR_CRT_OVERRIDE_DIRECTORY first and `AreaServer\CRT` relative to the server's
working directory second. The frozen launcher selects
`D:\SWTORClassic\swtoremu\Diagnostics\GeneratedPhaseCandidate`; the runtime
working directory remains `SharpServer\bin\Debug`.

The override is 97 bytes, SHA256
`6752695E7BCCA4139D9488E56B35F95D4B37DC0750064B88166B52374CCB9A09`.
Generate-PhaseInstanceDuplicate.py constructs it from CRT1's phase-instance
record and CRT11 framing, replacing the packed node with 0x1AC688C981.
It is generated replication data, not a captured room stream. The actual first
four bytes are stream 0x001B502E; PhaseExit previously logged 0x001B502F without
changing the payload. The destroy also uses 0x001B502E. Fixture-set uniqueness
claims in the generator do not prove runtime stream uniqueness or acceptance.
The generator was read, not run, and no candidate was modified. The saved hex
and PacketWorkbench report document inspection; the report's 8-byte S2C header
is explicitly synthesized, not evidence of a production packet.

## Build and checks

Fresh before and after builds: Debug/x86, .NET Framework 4.8, MSBuild
18.10.1, exit 0 with existing warnings. Output/intermediates are isolated here;
the installed server executable was not replaced.

Candidate: `build/NexusToRServer.exe`, SHA256
`FF454DC4CCAE09980DF558FC214CA85188605B3CA9433655DEBC0D6F12926880`.
`identity.csv` pins the executable, config, hook, launch inputs and fixtures.
`commit.txt`, `dirty-before.txt`, `tracked-before.patch`, `PhaseExit.before.cs`
and `PhaseExit.after.cs` preserve the starting identity and this change.

All assembly tests used Windows SysWOW64 PowerShell with -NoProfile,
-ExecutionPolicy Bypass and -AssemblyPath pointing at before-build or build.
PacketWorkbench has no AssemblyPath parameter.

| Check | Before | After |
|---|---|---|
| AreaRouting | PASS exit 0 | PASS exit 0, 11 classes / handles 8 and 19 |
| AreaBlobFraming | PASS exit 0 | PASS exit 0, 38 bodies |
| AreaWireRoundTrip | PASS exit 0 | PASS exit 0, 54 packets |
| PacketWorkbench | PASS exit 0 | PASS exit 0 |
| PacketDecoder | PASS exit 0 | PASS exit 0 |
| CapturedCharacterRemap | PASS exit 0 | PASS exit 0 |
| AreaEnterSignals | PASS exit 0 | PASS exit 0 |
| WorldEntryOffline | FAIL exit 1 | Same FAIL exit 1 |

WorldEntryOffline stops at "Opt-in RequestWorldFadeIn gate observer is missing."
Later assertions were not reached. The test was not changed. Complete logs are
before-Test-*.log and Test-*.log. No complete-suite or native acceptance claim.

## Run exactly one crossing

From a fresh PowerShell terminal with no inherited SWTOR_* switches, after
closing old game/server processes, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\SWTORClassic\swtoremu\Diagnostics\DoorwayControl-20260930\Launch-Control.ps1
```

This validates pinned files, preserves current latest/before-latest and runtime
logs again, and launches a frozen copy of the existing trace launcher using the
isolated executable. It does not install that executable. The original launcher
is unchanged. The hook installation/archive handling is the original trace
workflow, not a new hook experiment. A one-run marker prevents accidental reuse.
The frozen launcher writes `effective-server-switches.txt` immediately before
server launch; `planned-effective-switches.txt` is a preparation-only preview.
The retry interval and spawn override remain unset. Existing ability switches
remain as in the baseline; do not activate abilities during this crossing.

1. Enter the same Jedi Knight in the Masters' Retreat. Wait until the world and
   character render; record the story-area/owner UI and the local clock time.
2. Walk normally toward and through the visible exit once. Do not teleport,
   jump, use abilities, change characters, or restart. Continue forward briefly
   if movement permits. Record when movement hits a wall or reaches outside.
3. Stop. Note the story-area banner/owner state, any loading-screen change,
   exterior geometry and whether the floor is traversable. Screenshots/video
   with local times are useful. Visual appearance alone is not room residency.
4. Leave the client alive and report that the crossing attempt is finished, so
   its evidence can be collected before exit. In a second PowerShell terminal,
   preserve the current logs with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\SWTORClassic\swtoremu\Diagnostics\DoorwayControl-20260930\Preserve-Logs.ps1 -Label after-crossing
```

The launcher also preserves logs on client exit, but that is not a substitute
for an alive-client observation. No automation can perform native movement in
this session. No timeout or absence of user input will be treated as a result.

## Evidence and limits

Preparation snapshots preserve existing latest/before-latest files, runtime
server/hook logs and any discovered Documents/SWTOR* client logs. Their CSV
manifests contain original paths and saved hashes. The first snapshot completed
file copies but process inventory failed because CIM access was denied; the
next snapshot completed using Get-Process. Neither is a live run.

`Export-Movement.ps1` reuses the bounded decoder (Read only, never Run) and the
PacketWorkbench hex parser. Use x86 PowerShell with -ServerLog <saved log> and
-OutputCsv <new path>. It preserves rejected historical variants as rejected
rows, without XYZ, and marks crossings between accepted C5 samples using the
same X=-63 detector. This does not prove a continuous trajectory. A historical
validation found two accepted C5 samples and ten rejected C7 samples; these
are historical data, not this experiment. The initial exporter validation
stopped on C7; the final exporter preserves rejection rows and passes.

Server log timestamps are asynchronous writer time, to seconds, not packet
receipt time. Preserve raw ordering and compare hook times conservatively.
Nearby inbound dumps and AREA-PAYLOAD outbound prefixes remain in full saved
logs. Short destroy packets fit the 256-byte outbound prefix; larger prefixes
must not be represented as complete packet captures. Use PacketWorkbench on
extracted plaintext, retaining source line/time/direction.

Require separate evidence for: (a) server destroy serialization/send,
(b) native receipt and relevant apply callback, (c) phase-info node removal or
phase-field/UI change. A generic CRT "applied" log alone is not proof that this
specific child was removed. Record the matching stream/node and callback/field
evidence. Missing evidence is inconclusive.

The existing hook has ParseInboundFrame, CrtApplyHook, loading GOM and player
field observations. It has no verified native loading-state write watcher or
room/collision-residency observer found in this audit. The older [obj+0x8C]
loading-state notes are leads, not live observations. Do not infer residency
from gnarls_new strings, absence of errors, loading UI, or missing responses.
Capture any real native state/residency observation separately with its method
and timestamp; otherwise label it unavailable. Adding a new hook/watchpoint or
enabling a suspend/dump probe would require a separate experiment record.

## Next evidence

One manual crossing using this prepared build, with the client left alive for
collection. Classify the result only after reviewing the movement, destroy and
native evidence. If native state/residency remains unobserved, the next isolated
instrumentation question is how to independently observe those state changes;
it is not permission to send AssetCreated, InstanceCreated or another guess.

## Final preparation validation

All 50 pinned identities match; PowerShell helper syntax passed. The movement
exporter passes against historical logs (two C5 accepted / ten C7 rejected).
The final PacketWorkbench registry check passes, exit 0, in
registry-final-Test-PacketWorkbench.log. An intermediate duplicate-opcode row
failed its uniqueness check; that draft is preserved in registry-duplicate-draft.csv
and the failure in final-Test-PacketWorkbench.log. The final registry updates
only the existing replication row's warning; no test or registry uniqueness
rule was weakened. No confidence level changed.

The executable is launched from the isolated build with the original runtime
working directory. The installed hook and build hook hashes match exactly
(E15771F7FEC2978B3C4F6FE81B1F8D730FCE4FC9EF753838CB5AFF0C4E681DB1).
No hook build or native instrumentation change was made. The native executable
here is swtor-emu.exe; the preflight checks both swtor and swtor-emu. The frozen
legacy launcher's later tasklist checks mention swtor.exe, so always use the
explicit after-crossing snapshot while the client is alive; do not rely on
those tasklist checks to establish native process completion.

Files changed this session: SharpServer/AreaServer/PhaseExit.cs;
Diagnostics/Protocol-Evidence.csv; Diagnostics/GeneratedPhaseCandidate/README.md;
Diagnostics/Experiments/INDEX.md; the prior pending 2026-09-29-01 record (follow-up
link only); the new 2026-09-30-01 record; and this new DoorwayControl-20260930
folder containing isolated builds, logs, snapshots, manifests and three
PowerShell helpers plus frozen launch/switch-preview commands. Prior files and
fixtures were preserved. The original trace launcher and installed executable
were not edited. No live run occurred; effective-server-switches.txt and the
launch-requested marker do not exist until a launch is requested.

Live update: a run has now occurred. See live-analysis/RESULTS.md; the PREPARED/NOT LAUNCHED statements above describe preparation history.
