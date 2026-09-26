# SWTOR Tython world-entry checkpoint — 2026-09-24

This checkpoint is for a fresh agent resuming investigation in
`D:\SWTORClassic\swtoremu`. Work in this repository only. Treat
`D:\SWTORClassic\swtoremu2` as a read-only historical reference.

The user has paused work. Do not request another client run until an offline
analysis produces a specific question that existing logs cannot answer.

## Current outcome

The April 2012 client reaches character selection, selects the test character,
connects to the Tython area service, consumes the startup replication stream,
and remains on the Tython loading screen. It then emits the same packed
operation every 30 seconds. The process remains responsive and exits normally
when the user closes it.

No successful in-world render or controllable character has been observed.

## Facts established by logs, code, or byte-level tests

### Startup and transport

1. Repository synchronization completes in the native client.
2. All 74 character-spec resources eventually become ready.
3. Local area loading reaches the active-area transition and connects to the
   destination area service.
4. `AreaModulesList` is received before the area startup bundle is sent.
5. The latest client sync packet, `CMsg61116AD5`, contains replication stream
   `0x001B502D`, the stream ID in CRT17. Thus the client consumed through the
   last fixture sent; this does not prove that every embedded field had the
   intended semantic value.
6. The latest run sent `CharacterSetRendezvousPoint` followed by
   `CharacterChangeState("AreaServer")` after character sync.
7. No serialization exception, script error, abnormal disconnect, or client
   crash appears in the latest run. Manual closure was a normal disconnect.
8. The resource worker repeatedly reports `state=5 queued=0`. The travel gate
   alternates state 3 and 0 with an empty destination. This is not evidence of
   queued resource work.

### Character identity

1. Captured Tython fixtures use player node
   `0x4000010E218A839C`; the selected emulator character is
   `0x4000010E218A839B`.
2. `CapturedCharacterRemap` rewrites both packed and little-endian references
   across CRT, effect-event, and On Enter payloads.
3. Live logs show the periodic client invocation using selected character
   `0x4000010E218A839B`, so the selected identity exists in the relevant native
   path.
4. Offline remap tests pass and verify that captured references are replaced
   in the tested payloads.

### Replication fixtures and CRT3

1. CRT1 contains schema definitions including:
   - `chrIsMe` = `0x4000000365D249CB`
   - `chrCharacterPlayMode` = `0x400000077CDF593B`
   - `chrPlayerLoaded` = `0x4000000D5DF53477`
2. CRT2 contains the captured `chrPlayerCharacter` object and many associated
   objects. The selected player reference is remapped before transmission.
3. The stored CRT3 is not a verified full capture. Native-reader/dump analysis
   showed its 25-byte style-7 body ends during the third component of a
   three-component value. Changing only its outer sequence ID does not repair
   this truncated value.
4. The run ending at 16:42 on 2026-09-24 suppressed CRT3. The server logged:
   `AreaStartupBundle: suppressing known-incomplete CRT3`.
5. Even without CRT3, the client consumed through CRT17 and entered the same
   30-second loop. Therefore neither sending the known-bad CRT3 nor omitting it
   has solved world entry. CRT3 should remain suppressed in normal runs because
   its contents are still demonstrably incomplete.
6. A 19:55 controlled run used an isolated CRT1/CRT3 pair that appended three
   GOM-derived phase schemas and changed CRT3's structure reference to the
   proposed `phsPlayerPhaseData` structure. The client rejected CRT1 with
   `G::SerializationException("Unable to read field count")`; dump path:
   `Diagnostics/world-entry-20260924-195555-32536-first.dmp`. Later dump
   inspection proved the active schema reader was still bounded to the
   original 44,001 bytes: the generator appended 206 bytes but failed to
   update CRT1's little-endian length at offsets `0x04..0x07`. Thus this run
   rejected malformed framing, not the appended type records or CRT3's
   22-byte value interpretation. The generator now writes and validates the
   44,207-byte bound; its corrected isolated pair remains unverified live.

### Packet order and shapes

1. Comparison against untouched `swtoremu2` found that RPC
   `CF 65 F1 36 91 ...` had drifted later during the startup-bundle refactor.
   It has been restored immediately after CRT1 and the first `CF 75 ...` RPC.
2. The corrected order did not advance world entry, but it remains the captured
   historical order and is guarded by an offline assertion.
3. Fifty-four fixture wire round trips pass, including transport headers and
   raw-deflate preservation.
4. Character remapping tests pass.
5. Rendezvous and change-state packet-shape tests pass.

### The repeating operation

1. The repeating blob is exactly:
   `C7 71 C3 79 12 F2 40 F5 F5`.
2. It appears in the initial post-startup batch and then alone every 30 seconds.
3. The original C++ reference server consumes `CMsgF96DCDB0` without replying.
4. Echo, result, mirror, and acknowledgement experiments did not advance world
   entry. The trace launcher currently swallows these calls.
5. The operation is emitted synchronously from a runtime-generated script
   callback through generic client VM/event/RPC adapters.
6. The correlated 64-bit value `0xD000199A7D03034B` resolves to the
   `chrPlayerCharacter` class definition, not a Hero method.
7. Static disassembly shows RVA `0x001C173B` is the return point after a
   virtual GOM operation. It is not itself a named readiness routine.

### Script/archive and dump experiments

1. The matching April system-generated script archive is installed by the
   trace launcher. Its absence was tested and rejected as the direct blocker.
2. `guiGFxLoadingScreen` definition lookups did not become active during the
   repeated loop.
3. External full-memory dumps do not reliably contain the custom high-memory
   allocator regions holding the relevant live VM objects.
4. Thread-pausing and atomic-suspension dump experiments did not recover a
   usable field/value mapping.
5. Dump watcher startup and the temporary hook pause were removed from the
   normal launcher. `Diagnostics\Capture-ReadinessDump.ps1` remains only as a
   retired diagnostic artifact.
6. Aggressive memory walking on the generated-event path caused repeatable
   client crashes and must not be reintroduced.

## Latest run: exact interpretation

Latest live sources:

- `SharpServer\bin\Debug\NexusToR.log` (through 16:42:38)
- `nexusclient\nexusclient\nexus_hook.log` (through 16:42:37)
- `Diagnostics\startup-summary.log`

Timeline:

- 16:41:11–16:41:13: CRT1, CRT2, and CRT4–CRT17 sent; CRT3 suppressed.
- 16:41:14: client reported sync through CRT17.
- 16:41:14: rendezvous and `CharacterChangeState("AreaServer")` sent.
- 16:41:41: periodic `F5F540F2` operation, active VM depth 1.
- 16:42:11: same operation and same native path again.
- 16:42:38: user closed the client; normal disconnect.

Compared with the immediately preceding CRT3-enabled run, the selected
character, class key, native call stack, operation bytes, and 30-second period
are structurally unchanged. Pointer addresses naturally differ by process.

## Strong inferences (not proven facts)

1. The client is waiting on a gameplay/readiness condition rather than raw
   resource I/O. This is strongly supported by `queued=0`, successful CRT17
   sync, and the stable script-side poll, but the precise condition is unknown.
2. Missing or incorrect replicated player/phase state is the leading remaining
   area of investigation. Candidate fields include `chrPlayerLoaded`,
   `chrIsMe`, play mode, and phase ownership/active-phase fields. No trace has
   yet shown the runtime value of any of these fields.
3. A genuine compatible CRT3 or an equivalent phase update may be necessary.
   This is plausible because the stored CRT3 references phase data, but the
   enabled-versus-suppressed runs prove only that the current truncated fixture
   is neither sufficient nor required to consume later streams.
4. The periodic F5 operation is probably a status notification or poll symptom,
   not a request whose direct reply unlocks the world. The reference-server and
   reply experiments support this, but its exact script-level meaning remains
   unidentified.

## Unproven assumptions that must not be presented as facts

1. We do **not** know that `chrPlayerLoaded` is false or missing.
2. We do **not** know that `chrIsMe`, play mode, or phase state is the single
   blocking condition.
3. We do **not** have a schema-aware decode of the style-7 player payload.
4. We do **not** know the method name behind the runtime-generated callback.
5. `0xD000199A7D03034B` is **not** a method ID; it is a class record key.
6. RVA `0x001C173B` is **not** a proven readiness function.
7. The reachable `not_found` string is correlation only; it is not a proven
   return value for the readiness operation.
8. Successful CRT17 acknowledgement proves transport/consumption, not correct
   semantic application of every prior object update.
9. No guessed CRT3 tail, forced field value, or fabricated server RPC response
   has evidentiary support yet.

## Current intentional behavior and modifications

1. `SharpServer\NET\Packets\Server\AreaStartupBundle.cs`
   - restores the historical `CF 65 F1 36 ...` order;
   - applies selected-character remapping to captured payloads;
   - suppresses known-incomplete CRT3 by default;
   - permits CRT3 only when `SWTOR_ENABLE_UNVERIFIED_CRT3=1`;
   - sends On Enter through the remapping helper.
2. `SharpServer\NET\Packets\Server\CapturedCharacterRemap.cs` performs the
   fixture identity rewrite.
3. `Client\Hook\Src\ToR.cpp` contains read-only event, RPC, GOM lookup, and
   readiness correlation logging. It does not force readiness state.
4. `Run-SWTORClassic-Trace-Tython.cmd` rotates logs, installs the matching April
   script archive, uses swallowed RPC mode, and waits for client exit before
   collecting logs.
5. `Diagnostics\Test-WorldEntryOffline.ps1` checks startup order, the CRT3
   diagnostic guard, fixture consistency, remapping, wire round trips, and
   enter-signal shapes.

The worktree is substantially dirty and includes user/pre-existing changes,
generated binaries, logs, caches, and diagnostic artifacts. Do not reset,
clean, or broadly revert it. Inspect overlapping changes before editing.

## Validation at checkpoint

The x86 Debug server build succeeds with existing warnings and no errors.

`Diagnostics\Test-WorldEntryOffline.ps1` passes:

- captured startup prefix order;
- character-reference remapping;
- 54 fixture wire round trips;
- rendezvous/change-state shapes;
- CRT/phase structural checks;
- CRT3 opt-in guard.

These tests reject malformed framing and internal fixture inconsistencies; they
do not prove gameplay readiness or style-7 semantics.

## Recommended next investigation (offline first)

1. Build or recover a schema-aware decoder for style 7/8/9/10 using the April
   `client.gom` class hierarchy and field order. Start with the player object in
   CRT2 and the later updates referencing the remapped player.
2. Produce a table showing, for each relevant CRT:
   object ID, class ID, field name/ID, type, decoded value, and update order.
3. Specifically determine the transmitted values and later changes for:
   `chrPlayerLoaded`, `chrIsMe`, `chrCharacterPlayMode`, and the known phase
   fields.
4. Cross-check pre-existing implementations and comments before writing a new
   decoder:
   - `Server\Framework\Src\Network\Stream.cpp`
   - `Server\WorldServer\Src\Logic\Handlers\Character.cpp`
   - `Tools\tor_tools\Hero\Hero\DeserializeClass.cs`
   - `Tools\Hero\Hero\DeserializeClass.cs`
   - `Tools\tor_tools\GomLib`
   - `Diagnostics\WorldEntry-CRT3-Findings.md`
   - `Diagnostics\WorldEntry-Initial-Analysis-20260923.md`
5. If schema decoding cannot be completed, the next high-value evidence is a
   genuine April-compatible area-session capture. Do not invent the missing
   CRT3 bytes.
6. Request another client run only after a narrowly testable change or a new
   observer can distinguish two concrete hypotheses.

## Useful commands

Build:

```powershell
& 'C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe' `
  SharpServer\NexusToRServer.sln /t:Build /p:Configuration=Debug /p:Platform=x86 /m
```

Offline gate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Diagnostics\Test-WorldEntryOffline.ps1
```

Normal traced run, only when justified:

```text
Run-SWTORClassic-Trace-Tython.cmd
```

## Bottom line

The transport and startup pipeline now reach a stable, reproducible boundary:
the client accepts all remaining replication streams and final enter signals,
then a generated script callback repeats every 30 seconds. The blocker has not
been identified. Player/phase state is the best-supported next target, but it
remains a hypothesis until style-7 data or live field values are decoded.

## 17:41 live-snapshot addendum

Offline analysis of `Diagnostics/tython-live-20260924-1741-29260.dmp` now
resolves the April client's real descriptor/context/storage path rather than
treating descriptor words as direct object offsets.  At the Tython readiness
loop the verified state-0 runtime values are:

- `chrIsMe = true`;
- `chrCharacterPlayMode = 1`;
- `chrCharacterPhaseMode = 1`;
- `chrPlayerLoaded = false`.

The first three prove that client-side initialization supplies values omitted
or reset by the incoming CRT stream.  `chrPlayerLoaded=false` is the leading
specific blocker hypothesis, not yet proof of the entire gate.  The named
`phsPlayerPhaseData` fields are not in the player's 610-field value container;
the separate phase-data instance still must be located offline.  Details and
addresses are recorded in `WorldEntry-Style7-Decode-20260924.md`.  Do not
request another client run or change packet bytes until an offline trace of
the loaded setter/gate yields a specific testable intervention.

The exact script scan now supplies that testable need.  The only April script
containing the full `chrPlayerLoaded` ID is definition
`0xD000199A7D03034B`, which is also the definition logged during every repeated
readiness poll.  This proves shared script-module ownership, not yet a branch
dependency.  A future run is justified only with an external read/write data
breakpoint on the newly resolved live Boolean address so its actual consumer
or setter stack can be captured without changing the value or packet stream.

That data-breakpoint test is complete. The Boolean resolved false before
`CharacterChangeState` and remained false through eight initialization
accesses. A native hit was a generic Boolean copy read, and three later
periodic readiness callbacks did not access the field. This rejects
`chrPlayerLoaded` as the direct `0xF5F540F2` polling gate. Investigation should
now return to the callback's actual context/phase inputs rather than forcing
this Boolean or changing its replication bytes.

CRT3's phase-data owner node is `0x00000017BFADF6AC`. The normal trace suppresses
CRT3, and the newest full dump contains no occurrence of that node ID, although
the referenced active phase and replicated player both exist. Therefore no
live `phsPlayerPhaseData` instance or phase-field values exist in this run.
Moreover, CRT3 names compact structure 1 while this CRT1 defines structure 1
as one-field `utlTrainerList`, not the five-field phase class. The fixtures are
not a matching schema pair. Do not enable the saved CRT3 or assign its 22 bytes
to phase fields by appearance; the next required evidence is a matching
CRT1/CRT3 capture or a fully reconstructed compact phase schema.

An offline writer scaffold now provides a strict first acceptance test:
`Diagnostics/Build-Style7Schema.py` round-trips all 104 CRT1 compact structures
byte-for-byte (44,001 schema bytes) without writing fixtures. Its
`--manifest phsPlayerPhaseData` mode derives the five field/type chains from
the April `client.gom` and reports, rather than guesses, two unresolved nested
structure references: `phsActivePhaseInfo` and
`phsUniqueActivePhaseInfo`. Consequently it cannot yet encode CRT3. The next
step is to reconstruct and validate those embedded compact structures plus
value/state serialization against known-good data; only then should a new
phase transaction be considered.

The writer now also has a non-emitting `--propose-phase-schema` mode. It builds
dependency-first in memory as proposed structures 105 (`phsActivePhaseInfo`),
106 (`phsUniqueActivePhaseInfo`), and 107 (`phsPlayerPhaseData`), then proves
the 44,207-byte expanded schema round-trips internally. Corpus validation
reproduces 2,691/2,731 captured field type chains exactly; 22 definitions are
absent from the April GOM and the other 18 are solely ambiguous selection
between duplicate `dynVisual`/`dynVisualState` structures. These proposed
numbers are not wire facts, and the tool still emits neither values nor CRT
files. Next: validate map, embedded-class, and field-state value serialization
using existing known-good captured structures.

CRT3's 22 value bytes now have a residue-free schema-dependent interpretation:
`phsActivePhases` contains one type-1 entry whose inner map contains phase
`0xFF5F184AAA9ECE77` and an empty zero-field `phsActivePhaseInfo`; the following
value is `phsAuthorityID = 0x4000010E218A839C` (the replicated player). This
matches the numerically sorted reconstructed phase schema exactly. It is not
yet wire-authoritative because the available CRT1 still maps structure 1 to
`utlTrainerList`, and CRT3's final `00` field-state byte needs the matching
schema-aware decoder. No CRT bytes were modified or fabricated.

An isolated candidate pair now exists in
`Diagnostics/GeneratedPhaseCandidate`. Candidate CRT1 appends structures
105-107 while preserving all original structures and its entire transaction;
candidate CRT3 changes only offset `0x1E` from structure 1 to 107. Its existing
22 value bytes and `00` state byte are untouched. Production fixtures remain
unchanged. Do not run this pair yet: the specific remaining offline gate is to
prove that the original `00` state byte is valid for the reconstructed
five-field phase schema.

The April `phsPlayerPhaseDataClassMethods` script now proves why this matters:
`OnReplicationNodeCreate` assigns the replicated node directly to
`$PHASE.phsActivePhaseData`; no fallback object is created when CRT3 is absent.
The asset decoder also identifies phase type 1 as `phsTypeClass` and shows all
five phase fields share attribute bitset `0x0240`. An opt-in CRT override was
added to the trace launcher: only candidate CRT1/CRT3 are loaded from
`Diagnostics/GeneratedPhaseCandidate`, with every other fixture falling back
to the untouched AreaServer directory. Build and offline gates pass. A client
run is now justified specifically to distinguish successful phase-node
creation from rejection of the reconstructed schema/state stream.
## 2026-09-25 Safe Login lifecycle checkpoint

`_JPEXTRACT/effCOntainerComponentClassMethods.txt` confirms that removing an
effect from its container is what invokes client cleanup. CRT2 identifies
positive effect container `0x1AC6F6DC0E`, with Safe Login `/0/1` in slot 1 and
immobilizing Safe Login Immunity `/0/2` (`0x1AC6F6DC1C`) in slot 2. The next
test sends a schema-driven style-8 replacement of `conContents` retaining only
slot 1, followed by removal of `0x1AC6F6DC1C` in that same replication
transaction. The server builds successfully and the general offline
world-entry gate passes.
