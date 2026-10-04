# Experiment 2026-09-30-03 — Read-only doorway room residency timeline

## Question

During one unchanged doorway crossing, do the April client area root or current-room pointers at area+0x2A0 and area+0x400 change identity or +0x8C/+0x90 lifecycle state?

## Existing evidence

Experiment 01 established one accepted C5 crossing, exact phase-info destroy
serialization, entry and return from the client's replication-apply route, CRT18
suppression, and operator-observed wall persistence. It did not establish that
the specific phase-info node was removed or that `gnarls_new` became resident.

Experiment 02 sampled the area root's `+0x8C` value as 3 after the crossing. It
did not identify a room object or observe a transition. Static April-client
disassembly now establishes writers and readers of object lifecycle field
`+0x8C`; the client loop compares objects selected at area offsets `+0x2A0` and
`+0x400`. The semantics of each pointer, room names, auxiliary state `+0x90`,
and the responsible wire lifecycle remain hypotheses. See
`../DoorwayControl-20260930/Native-Room-State-Analysis.md`.

## Single variable

Add one external read-only observer to the unchanged experiment-01 doorway
control. It samples the area root, the pointers at `area+0x2A0` and
`area+0x400`, and each object's `+0x8C/+0x90` values every 20 ms. It uses
`OpenProcess(0x410)` and `ReadProcessMemory` only. No server, client, hook,
packet, environment switch or outbound behavior changes. The generated CRT18
remains present as preserved evidence and suppressed by `PhaseExit`.

## Exact input

- Dirty build and source identity: experiment 01's
  `../DoorwayControl-20260930/identity.csv`; rerun-specific files are pinned in
  `../DoorwayControl-20260930/room-state-rerun/identity.csv`.
- Candidate `NexusToRServer.exe` SHA256:
  `FF454DC4CCAE09980DF558FC214CA85188605B3CA9433655DEBC0D6F12926880`.
- Environment switches: unchanged from experiment 01; actual launch values are
  written to `../DoorwayControl-20260930/effective-server-switches.txt` and
  preserved with the run logs. Phase retry and spawn override are absent. The
  existing baseline still has `SWTOR_ENABLE_UNVERIFIED_CRT3=1` and the three
  ability experiment switches enabled; the operator did not use abilities.
- Existing S2C phase-info destroy: opcode `0x0D446E80`, component handles
  `0x65B3/0x0008`, stream `0x001B502E`, node `0x1AC6F6DC1F`; actual bytes must
  be preserved again. No packet is added or injected.
- Expected C2S movement is the bounded C5 form of `0x61116AD5`; the captured
  historical fixture remains `Fixtures/Movement/C5-20260929.hex` and is never
  injected.

## Predictions

Positive observation:

- Accepted movement brackets the same doorway threshold, the destroy is sent
  exactly once and enters the client apply route, and the timeline records a
  contemporaneous pointer identity or lifecycle-state transition. A new stable
  selected object plus exterior rendering and traversable collision would
  support native destination-room residency.

Negative observation:

- With a valid crossing and client apply-route evidence, both selected pointers
  and their states remain stable while the invisible wall persists. This would
  establish that this control did not cause an observed selected-room lifecycle
  transition; it would not identify the missing packet.

Invalid/inconclusive conditions:

- Observer cannot attach or offsets are unreadable; no accepted C5 samples
  bracket the threshold; destroy delivery/apply-route evidence is absent;
  unsupported movement is acted on; CRT18 or another new outbound hypothesis is
  emitted; the pinned inputs differ; startup fails; or client interaction is not
  limited to one doorway approach without abilities.

## Evidence to preserve

- Server and launcher logs: a new timestamped `Preserve-Logs.ps1` snapshot,
  including nearby opcodes, accepted movement and effective switches.
- Hook/client log: matching timestamped hook log plus client `swtor.log` where
  available; independently distinguish generic replication apply from proof of
  this node's application.
- Native timeline: `../DoorwayControl-20260930/room-state-rerun/timeline.csv`,
  `watcher-console.log`, and `watcher-errors.log`.
- Packet report: export movement and the exact destroy plaintext after the run;
  run PacketWorkbench on preserved evidence where applicable.
- User-visible observation: loading screen, area banner/minimap text, exterior
  rendering, and whether collision permits continued walking. Preserve a
  screenshot while the client remains open if it adds information.

## Result

Live run occurred 2026-09-30. Launch requested at 00:20:11 Toronto. The external
observer attached to PID 45972 at 00:22:56 with module base `0x006E0000` and
global area-pointer address `0x01776E20`.

Accepted C5 movement was `(X,Y,Z)=(-64.8741,-6.906221,-127.671)` at 00:23:32,
then `(-62.95565,-6.898841,-126.2381)` at 00:23:54, which bracketed X=-63.
A third accepted C5 sample at 00:23:54 was `(-62.95174,-6.898841,-126.2342)`.
Intervening C7 variants were explicitly rejected before behavior.

At 00:23:54 the server serialized exactly one 46-byte phase-info destroy on
stream `0x001B502E` for node `0x1AC6F6DC1F` (SHA256
`2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`).
The hook independently recorded parsed opcode `0x0D446E80`, then
`CrtApplyHook: crt count=18` entry and `applied` return. This proves delivery
through the generic client apply route, not removal of this specific node.
CRT18 suppression was logged and no phase retry was emitted.

At 00:23:48, six seconds before the crossing, native state was:
area `0xF41439A0` state/aux `3/6`; primary `0xD2C14500` state/aux `3/6`;
secondary `0xD2C15500` state/aux `3/6`; tree begin `0xD2B64E70`.
The same identities and values were recorded every second through 00:25:47,
more than 113 seconds after the crossing. The 20 ms observer wrote a row on every
signature change; there was no change row in that interval. Its earlier change
rows describe initial client and area startup, demonstrating that the observer
could detect pointer and state transitions. When the client closed at 00:25:48,
it recorded the global area pointer becoming null and ended cleanly.

The startup `AreaAwarenessEntered` payload at 00:23:31 contains `gnarls_new` in
the dynPlaceable record for node `0x1AC6F6DC94`; its only fixture occurrence at
offset `0x51` lies inside that record. This establishes that the
existing startup awareness bytes name that object before the doorway attempt;
it does not establish selected-room or collision residency.

Operator observation: no change in behavior. No loading-state, location-text,
rendering or collision change was reported, and the character remained blocked.
Evidence and hashes are in
`../DoorwayControl-20260930/room-state-rerun/live-20260930-002429-594/`.

## Conclusion

- Outcome: the phase-destroy-only selected-room-transition hypothesis is
  falsified for the observed `+0x2A0/+0x400` identities and `+0x8C/+0x90`
  fields; broader native room semantics remain unresolved
- Confidence change: none; no wire-shape or lifecycle claim promoted
- Registry rows updated: none (no new protocol fact)
- Runtime code retained: experiment-01 CRT18 suppression; observer is external
  and read-only
- Next single question: which startup native objects correspond to
  `gnarls_new`, the selected pointers, and the doorway collision owner?

