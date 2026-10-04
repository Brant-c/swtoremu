# Experiment 2026-09-29-01 — Doorway control after bounded movement decode

## Question
With unchanged outgoing packets, does the doorway crossing correlate with a client
opcode or native loading-state change?

## Existing evidence
Captured: registry CMsg61116AD5 row; preserved C5 bytes in
../Fixtures/Movement/C5-20260929.hex. Offline decoder acceptance and rejection are
recorded in ../DecoderBaseline-20260930/after-Test-PacketDecoder.log.
Hypothesis: native room/world-content residency is still the blocking condition.
CRT18, AssetCreated, InstanceCreated and SendToArea are not established solutions.

## Single variable
The bounded inbound decoder and failed-Read execution gate are the only new runtime
changes from this development session. No outgoing serializers or startup ordering
were edited. Do not add an outgoing experimental packet to this run.

## Exact input and preflight
- Dirty-file identity: ../DecoderBaseline-20260930/dirty-before.txt,
  tracked-before.patch and session README/RESULTS.md.
- Candidate assembly: ../DecoderBaseline-20260930/after-build/NexusToRServer.exe.
  It has NOT been deployed over the installed server.
- Environment: ../DecoderBaseline-20260930/launcher-switches.txt. Record the actual
  inherited environment at launch, especially SWTOR_PHASE_INSTANCE_RETRY.
- Expected observed C2S opcode: 0x61116AD5, component 0x65B30008, doorway movement.
- Exact reference bytes: ../Fixtures/Movement/C5-20260929.hex; text-file SHA256
  75DABCBD92AFE83052F78F94AF788216973ED5A000A9C7B6F6E7231404E80B80.
- Reference is one historical packet, not a proposed packet to inject.

Preflight issue: existing PhaseExit.OnMove invokes SendRoomStream after destroy;
SendRoomStream may emit CRT18 when CRT.Has succeeds. The configured override
folder already contains a generated .18.acrt. This session did not introduce,
modify, validate or enable that path. Do not mistake its comment for proof of a
native room stream. Resolve this pre-existing confound explicitly before a live
control; do not delete or overwrite the candidate. Any isolation change must be
recorded as the sole additional experimental variable in a separate run record.
The baseline world-entry source guard also fails before and after this session.

## Predictions
Positive: timestamped C5 XYZ crosses X=-63; phase-info destroy delivery and native
application are independently confirmed; an inbound opcode or native loading-state
write consistently aligns with the crossing. Capture resident-room/collision status.
Negative: a confirmed crossing and applied destroy has no correlated opcode/state
change while the wall persists. This weakens the crossing-message hypothesis only.
Inconclusive: no decoded crossing, unsupported variants only, missing handler
execution/delivery proof, CRT18 or other experimental packet emission, mixed logs,
unverified loaded binary, or unrelated startup failure.

## Evidence to preserve
Create a new run-specific directory before using launchers that rotate logs. Preserve
server, hook, native client logs and prior latest/before-latest files without replacing
them. Save packet hex and PacketWorkbench reports for a narrow crossing window,
decoded XYZ with server timestamps, destroy handler evidence, loading-state writes,
resident-room/collision observations, and the exact effective switches/build hashes.

## Result
PENDING — no client/server process was active during inspection. Native game control
is not available through the enabled UI tools in this session. No live run was started
and no live acceptance, loading-state or exterior-residency conclusion was drawn.

## Conclusion
Confidence unchanged. Next evidence: one isolated doorway control timeline, after
resolving the pre-existing CRT18 confound, without adding a room-notification guess.

## 2026-09-30 follow-up
Still no run. The CRT18 confound is isolated in the separate experiment
[2026-09-30-01](./2026-09-30-01-doorway-crt18-suppression-control.md).
Use that prepared control and its build/environment identity for the next run;
do not launch this older candidate or combine results across configurations.
