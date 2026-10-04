# Experiment 2026-09-30-01 — Doorway CRT18 suppression control

## Question
With the bounded decoder fixed as baseline, does a doorway crossing with the
unverified CRT18 send suppressed apply phase-info destruction and change native
loading or exterior residency?

## Existing evidence
Captured: C5 registry row and Fixtures/Movement/C5-20260929.hex.
Hypothesis: generated CRT18 could be a native room stream. Inspection refutes
its provenance as a captured room stream, not every possible native lifecycle.
CRT.Has checks the configured override first; CRT.Get reads that same file.
Generate-PhaseInstanceDuplicate.py constructs a duplicate phase instance.
See ../DoorwayControl-20260930/README.md for exact lookup and hash evidence.

## Single variable
Remove the automatic CRT18 send after doorway phase-info destroy. The bounded
decoder is held fixed as baseline, not claimed as another independently tested
variable in this run. This record supersedes the still-unrun 2026-09-29-01 control
configuration. Do not compare against an old permissive-decoder live run and
attribute any difference solely to suppression. No new outbound packet.
Retry is unset (the existing disabled baseline), spawn remains captured, and
all original startup and ability switches remain unchanged. Do not use abilities.
A new hook, native watchpoint or other runtime change needs a separate record.

## Exact input
- Dirty identity, build logs and source snapshots: ../DoorwayControl-20260930/.
- Candidate build/NexusToRServer.exe SHA256:
  FF454DC4CCAE09980DF558FC214CA85188605B3CA9433655DEBC0D6F12926880.
- Debug/x86 .NET Framework 4.8. Installed executable untouched.
- Effective switches: planned-effective-switches.txt is a preview;
  effective-server-switches.txt is written only during actual launch.
- Pinned launcher/hook/fixtures/build inputs: identity.csv.
- Suppressed S2C 0x0D446E80 CRT18 candidate: 97 bytes, SHA256
  6752695E7BCCA4139D9488E56B35F95D4B37DC0750064B88166B52374CCB9A09.
  Exact bytes: crt18-preserved.hex (body only), retained original .18.acrt.
- Expected C2S movement: D5 6A 11 61 / component 0x65B30008 for handle 8;
  fixture C5-20260929.hex is historical, never injected.
- Existing destroy: S2C 80 6E 44 0D, dynamic area destination, stream 0x001B502E,
  removed node 0x1AC6F6DC1F. Preserve its actual AREA-PAYLOAD bytes in the run.

## Predictions
Positive: accepted C5 samples bracket X=-63, exactly one destroy is sent;
native receipt, relevant callback and node/phase-field changes independently
confirm application. Native loading/residency observations identify whether the
exterior becomes resident and traversable without a new packet.
Negative: independently confirmed crossing/application and unchanged native
state with a wall weakens the phase-removal-only hypothesis. It does not prove
which stream/notification is missing.
Inconclusive: unsupported movement without accepted crossing, another CRT18
emitter, abilities using the destroy stream, stale binary, absent client apply
proof, unknown native residency, unrelated startup failure or mixed sessions.

## Evidence to preserve
Before any launcher: use Preserve-Logs.ps1; timestamped folders + manifests
preserve latest/before-latest logs without overwriting them. The launcher repeats
this preflight, captures effective switches, and snapshots logs at client exit.
Keep the client alive after one crossing for after-crossing collection, native
observations and timestamped operator notes. Preserve raw server/hook/client
logs, nearby opcode bytes, movement CSV, native callbacks/fields, loading state,
room/collision evidence and any screenshot/video. See README for commands and
instrumentation gaps. Missing native observations must be marked unavailable.

## Result
PENDING — no client run or crossing occurred. Native game interaction is not
available in the enabled tools. Before/after isolated builds pass. Seven checks
pass before/after; WorldEntryOffline fails at the same pre-existing source guard
("Opt-in RequestWorldFadeIn gate observer is missing."); later assertions unrun.

## Conclusion
No behavior conclusion or confidence promotion. Registry updates the existing ClientReplicationTransaction row with the
generated-fixture warning; Captured applies only to the captured fixtures, and
CRT18 native room semantics remain Hypothesis. Automatic
unverified doorway emission removed; independent retry remains opt-in and off
for this control. Next single evidence-producing step: user performs one manual
crossing with Launch-Control.ps1, leaving the client alive for collection.

## Live update — 2026-09-30 00:07 Toronto
A live run has now occurred with the prepared build. User reports an invisible
wall beyond the green phase doorway. Accepted C5 samples bracket X=-63;
existing destroy plaintext and native replication route/apply return are saved.
CRT18 suppression is logged. Specific phase-info removal and native loading /
room-collision residency are not independently established. Outcome: observed
wall persistence; full lifecycle result inconclusive. No confidence promotion.
See [live results](../DoorwayControl-20260930/live-analysis/RESULTS.md), including
exact snapshot paths, movement.csv, destroy.hex, PacketWorkbench report,
effective switches and nearby opcode windows. Earlier PENDING text above is
preserved as pre-run history. No runtime change was made during collection.
