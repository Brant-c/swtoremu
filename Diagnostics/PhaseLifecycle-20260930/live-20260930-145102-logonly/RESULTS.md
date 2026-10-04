# Corrected CRT3-on doorway result — 2026-09-30 Toronto

The operator crossed once and reported `stopped, stuck on wall`. This is a valid
baseline for the user-authorized log-only callback question. No full-memory
observer was used; lookup mutation, global read-back and native room residency
were intentionally outside this run's scope.

## Independent live facts

- Fresh desktop launch at 14:51:02, server PID 25608 and hooked client PID 45688.
  Pinned server SHA-256: `1931A175025884E2E790363F7EEACEA096FAB3B8C9D41E3C273F426DE706A356`;
  installed hook: `258C834F1A524F039CF96D74EBDED5650A9AA3FE1166759C808CE961AE1A3D36`.
- At 14:54:31, discovery installed unique private-memory method prefixes at
  phase-info destroy `0xEC9FD6B0`, gateway update `0xEC7E2670`, player-phase-data
  create `0xEC64C810`, destroy `0xEC64CB00`. These prefix windows do not overlap.
- CRT3 emitted at 14:54:31: 55-byte matched override, SHA-256
  `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`.
  `phsPlayerPhaseData.OnReplicationNodeCreate` entered and returned with argument
  `0x001B5014` at that time. This proves callback execution, not a read-back of
  `$PHASE.phsActivePhaseData`.
- Startup bundle completed at 14:54:33. The first accepted C5 position was
  `(-64.874,-6.906,-127.671)`.
- At 14:57:26, accepted C5 movement crossed `-64.87 -> -62.98`. The server
  emitted one exact 46-byte destroy for phase-info node `0x1AC6F6DC1F` on stream
  `0x001B502E`. Exact plaintext SHA-256:
  `2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`.
  `doorway-destroy.bin`, `.hex` and `-workbench.txt` preserve it.
- Generic CRT apply count 18 brackets named
  `phsPhaseInfo.OnReplicationNodeDestroy` entry and return, with argument
  `0x001B502E` and destroy depth 1. Generic apply then returned. No count-19
  doorway transaction was present in the captured crossing window.
- No `phsOracle.UpdateGatewayForInstance` call was recorded within that destroy
  callback. The observer logs this method only while destroy depth is positive;
  unrelated gateway calls are not covered by this absence statement.
- No player-phase-data destroy entry was recorded through the saved window.
  This does not prove its global remains active or that every node still exists.
- CRT18 suppression was explicitly logged at 14:57:26. Retry was disabled in
  the new launch's effective switches. No abilities were requested or reported.

## Script facts and interpretation

The April phase-info script conditionally updates the gateway only if a parent
is resolved, its `phsPhases` lookup contains the child, and the local player
character resolves. It removes the lookup entry and clears overrides inside
those branches, then fires the destroy event. The live logs prove the named
callback executes; they do not identify which branch was taken or prove lookup
removal. No nested gateway call was observed despite the wall persisting.

Possible explanations include an unresolved parent, missing parent lookup
membership, missing player resolution, or another lifecycle/room/trigger issue.
No one explanation is established. This result does not justify guessed
CRT18, room, trigger, awareness or notification packets.

## Preservation and registry

Full small text logs and hashes were preserved at
`../../DoorwayControl-20260930/phase-lifecycle-logonly-blocked-20260930-145754-227/`.
This directory holds startup gates, exact inputs, effective switches, narrow
crossing windows, event counts and the exact destroy packet. The operator's
pasted server excerpt matches the same 14:57:26 window.

Protocol-Evidence.csv receives a separate narrow Behavior-verified row for
this destroy transaction's named callback execution; the general replication
schema row remains Captured. Gateway-update absence and unresolved field/node
state are recorded as limits, not promoted into proven wire semantics.
No runtime/launcher changes were made while observing this crossing, and no
additional offline tests were needed after the previously verified build.

Next single controlled question: does disabling CRT3 change callback/gateway
behavior or the wall, using the same log-only inputs and all other settings?
Experiment 07 must be aligned to this exact log-only baseline before that run;
its older launch wrapper must not silently restore verbose tracing. Preserve
this CRT3-on result first and do not rerun or launch the ablation automatically.
