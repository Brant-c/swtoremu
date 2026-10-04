# Live control — provisional result, 2026-09-30 00:07 Toronto

The user launched the prepared control at 00:03:02.952 -04:00 and reported
"entering tython now", then: "I am blocked by an invisible wall beyond the green
door indicating a phase". This is an operator-reported wall observation, not an
independent native residency measurement. No report of banner disappearance or
loading-screen change was supplied.

## Identity and preservation
Server PID 32304 is running the prepared isolated executable, SHA256
FF454DC4CCAE09980DF558FC214CA85188605B3CA9433655DEBC0D6F12926880.
The launch-time effective switch file is preserved here. It matches the planned
switches; retry interval and spawn override are absent. No runtime code or
configuration was changed during the run. No new outbound hypothesis was sent.
Both swtor-emu PIDs 28416 and 33844 were observed; process metadata is preserved,
but their individual roles were not independently established. Do not infer two
player sessions from process count alone.

The authoritative snapshot paths are in sources.txt. Use the runtime server and
hook files listed there, NOT last-server-full.log / last-nexus-hook.log, which
still contained the prior run at snapshot time. Original logs and latest / before-
latest copies were preserved in entering-tython-* and after-crossing-* directories
with SHA256 manifests. NexusToR.server.out is empty; no native Documents/SWTOR*
client log was found by the preservation helper.

## Timeline
- Server 00:06:20: area startup emitted for tython_blockout/4611686019869492753/1.
- Server 00:06:21: accepted C5 X=-64.8741 Y=-6.906221 Z=-127.671.
- Intervening C7 movement frames are explicitly rejected; no C7 semantics inferred.
- Server 00:06:30: accepted C5 X=-62.95798 Y=-6.898841 Z=-126.2313.
  These accepted samples bracket the temporary X=-63 detector plane. This is
  not proof of a continuous trajectory or arrival in a loaded exterior room.
- Server 00:06:30–31: existing destroy serialized, stream 0x001B502E, removed node
  0x1AC6F6DC1F. Exact 46-byte plaintext in destroy.hex; PacketWorkbench report
  retained. PhaseExit logs exactly one crossing and CRT18 suppression.
- Hook 00:06:30: parsed opcode 0x0D446E80 with handles 65B3/0008;
  CrtApplyHook count=18 enter and applied return are logged. This is the
  eighteenth observed replication callback, NOT evidence that fixture CRT18
  was emitted. No CRT18 override emission or phase retry is logged in snapshot.
- Later accepted C5 positions in the snapshot remain near X=-62.95; do not
  infer wall collision from those positions alone. The user reports the wall.

Server times are asynchronous log-writer times, not receipt times; the apparent
one-second hook/server ordering difference is not a transport chronology proof.
Raw packet bytes and nearby opcodes remain in server-crossing-window.log and
hook-crossing-window.log. Movement was exported by the existing bounded decoder
without Run. No parser, hook, packet serializer or server setting was changed.

## Established versus unresolved
Established: prepared build running, accepted C5 samples bracket the detector,
existing destroy serialized, corresponding native replication route/apply
callback observed by time/order, automatic CRT18 suppressed, user still blocked.
The hook does not log stream/node in the apply callback; exact transaction
association is a time/order inference. Specific phase-info child removal is NOT
independently confirmed for this run. No phase-field readback, mapped node-destroy
callback or banner-change observation proves that application here.

Native loading-state writes and room/collision residency were not observed.
No conclusion that the client stayed in a particular native loading state, nor
that missing residency is proven. No opcode's lifecycle meaning is promoted.
A lack of new phase-gateway RPC in this one window would not establish absence
of such an RPC in general. The unresolved C7 interval further limits timing.

Outcome: wall persistence observed; full native lifecycle control is inconclusive.
Next single evidence-producing step: derive a safe read-only observer for the
specific phase-info removal/native loading or room-residency state, record its
instrumentation as a separate experiment, then repeat only that observation
change. Do not choose a new outbound packet from this result.

## Additional alive-client observation — 00:09:49–50
The user's screenshot is preserved as user-client-open.png; the world and green
phase doorway render, Master's Retreat is displayed on the minimap, and no loading
screen is visible. Chat's Entering Story Area text is historical, not phase readback.
A separate external read-only observation found area pointer 0xF43739A0 and
+0x8C state 3 in PID 28416, with resource queues idle. This is not a state-write
trace and does not establish exterior residency or the meaning of state 3.
See experiment 2026-09-30-02 for full provenance and the record-allocation failure;
no hook, packet, configuration or native memory was modified for this observation.
