# Experiment 2026-09-30-06 — named phase-info destroy lifecycle observer

## Question

When the existing 46-byte doorway destroy for node 0x1AC6F6DC1F is applied, does the April client run phsPhaseInfo.OnReplicationNodeDestroy, remove the child from the parent phsPhases state, and call PHASE.UpdateGatewayForInstance while the reconstructed phsPlayerPhaseData remains independently active?

## Existing evidence

Experiments 01 and 03 establish accepted bounded-C5 samples bracketing X=-63,
one exact 46-byte `0x0D446E80` removal transaction for node
`0x1AC6F6DC1F`, entry and return from the generic client CRT apply route, CRT18
suppression, stable selected-room pointers, and operator-observed wall
persistence. They do not establish removal of that specific node or invocation
of its named class callback.

The April `phsPhaseInfoClassMethods` client script says its destroy callback
resolves the parent, removes `Me` from `parent.phsPhases`, clears join
overrides, calls `$PHASE.UpdateGatewayForInstance`, and fires
`Replication_Destroy`. The April `phsPlayerPhaseDataClassMethods` script
separately assigns `$PHASE.phsActivePhaseData = Me` on create and does not clear
that global merely because a phase-info child is destroyed. These are
client-derived control-flow facts subject to decompiler limitations, not prior
live observations.

## Single variable

Current user-authorized scope: the next corrected CRT3-on run uses the
log-only profile in `../PhaseLifecycle-20260930/LOG-ONLY-PREPARATION.md`.
The full-memory observer and its READY requirement are omitted by explicit
user instruction. Named callback entry/return and nested gateway update remain
the deciding client evidence; server movement/send logs retain exact destroy
bytes. Parent lookup/global-state mutation and node-removal questions remain
unresolved by this narrower run. The previous live attempt at 14:21 installed
the repaired hooks but had CRT3 suppressed, so it is not the CRT3-on baseline.

Enable `SWTOR_TRACE_PHASE_LIFECYCLE=1`, a forwarding-only observer for four
byte-exact April script methods. It records named phase-info destroy entry and
return, gateway-update calls nested within that callback, and player-phase-data
create/destroy. A separate external process uses query/read access (`0x410`) to
snapshot the three HeroNodes and references before and after the callback. No
packet, field, return value, movement rule, trigger behavior, or startup CRT is
changed. CRT3 remains enabled as in the preceding controls.

## Exact input

- Dirty-file and binary identity: `../PhaseLifecycle-20260930/identity.csv`
  pins the inputs, including hook source/DLL, server/client, launchers, CRT1/CRT3,
  observer, PhaseExit, and the three native script resources.
- Environment: the established Tython trace launcher plus
  `SWTOR_TRACE_PHASE_LIFECYCLE=1`; `SWTOR_ENABLE_UNVERIFIED_CRT3=1`; no spawn
  override or phase-instance retry; CRT18 remains suppressed.
- Existing S2C input: opcode `0x0D446E80`, area component handles
  `0x65B3/0x0008`, stream `0x001B502E`, removal node `0x1AC6F6DC1F`, after an
  accepted C5 crossing. No input is added.
- Prior exact 46-byte plaintext SHA-256:
  `2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`;
  the live run must preserve its own bytes and hash.
- Pinned native script resources/method offsets: phase-info destroy
  `65A4399D0102A007.scpt` SHA-256 `76B92E...A60E` at decrypted `+0x0B78`;
  gateway update `C10C1F8290BE3551.scpt` SHA-256 `1DFA91...1F04` at
  `+0x32E3`; player-phase-data methods `9308DE76F6AAF774.scpt` SHA-256
  `E40D0E...3F1F` at `+0x00B1/+0x03A1`. Full hashes are in the identity file
  and checked by `Test-PhaseLifecycleSignatures.ps1`.

## Predictions

Positive observation:

- Generic CRT apply count 18 brackets a named
  `phsPhaseInfo.OnReplicationNodeDestroy` entry/return; a nested
  `phsOracle.UpdateGatewayForInstance` call is logged with destroy depth 1;
  the phase-info HeroNode or its references disappear after return; the parent
  and player-phase-data HeroNodes remain; no player-phase-data destroy runs.
  Loss of a child reference supports lookup removal but is not by itself a
  semantic identification of `parent.phsPhases`.

Negative observation:

- The generic apply returns without the named callback; the named callback runs
  but no nested gateway update occurs; or the phase-info HeroNode and all
  observed references remain unchanged after the callback. Any such result
  separates a concrete lifecycle failure from generic delivery.

Invalid/inconclusive conditions:

- Method discovery is absent or ambiguous; baseline cannot find all three
  HeroNodes; no accepted C5 crossing; exact removal serialization or generic
  apply proof is absent; the observer cannot read; another outbound experiment
  or phase retry runs; abilities are used; startup fails; or the client closes
  before post-callback snapshots.

## Evidence to preserve

- Server/launcher logs and exact crossing window, including accepted movement
  and effective switches.
- Full hook log plus the lifecycle/CRT window with timestamps.
- `../PhaseLifecycle-20260930/live-*/before-*` and `after-*` ID/object/pointer
  scans, summaries, ready metadata, and SHA-256 manifest.
- Exact removal bytes plus PacketWorkbench output.
- Operator observation of banner, loading, wall/collision, and continued
  movement, explicitly separate from lifecycle evidence.

## Result

### Valid corrected log-only baseline, 14:57:26 Toronto

CRT3 emission and its named create callback were independently recorded. The
corrected four-method discovery installed at 14:54:31. At 14:57:26 accepted C5
movement crossed `-64.87 -> -62.98`, one exact 46-byte destroy was sent, and
generic apply 18 bracketed named phase-info destroy entry/return. No nested
gateway update was recorded. CRT18 was suppressed; the operator remained
blocked. This answers the narrowed log-only question, not parent lookup/global
read-back or HeroNode-removal questions. Exact bytes, startup gates, timestamps
and interpretation are preserved in
`../PhaseLifecycle-20260930/live-20260930-145102-logonly/RESULTS.md`.
Registry: add only the narrow Behavior-verified callback-execution claim;
retain broader replication schema confidence. Earlier invalid attempts below
remain preserved and must not be merged with this result.

An attempted run occurred at 01:43–01:50 Toronto and is invalid for the stated
question. At 01:48:25 accepted C5 movement crossed `-64.87 -> -62.93`; the
server emitted the intended destroy on stream `0x001B502E`, and generic client
apply count 18 entered and returned. The operator reported the wall persisted.

Two preparation defects invalidate lifecycle interpretation:

1. The launcher used the stale `SharpServer/bin/Debug/NexusToRServer.exe`
   (SHA-256 `640AE44D...FA35`) rather than the current isolated build. It loaded
   the generated 97-byte `.18.acrt` (SHA-256 `6752695E...9A09`) and emitted it
   as a second transaction on stream `0x001B502F`; generic apply count 19 then
   returned. This violates the destroy-only condition.
2. The initial method scanner searched all executable memory and matched its
   own four signature constants inside `MemoryMan.dll`. The reported addresses
   `0x652B4B80..0x652B4C20` overlap and therefore cannot be the four full script
   bodies. No named callback line was recorded. Absence of a callback hit is
   not evidence because the detours targeted false addresses.

The combined multi-identity observer also failed validation and its empty
phase-object snapshots are excluded. A separate established scanner found the
known `gnarls_new` HeroNode in the same live process, but that does not rescue
the broken combined observer.

Evidence is preserved in
`../DoorwayControl-20260930/phase-lifecycle-invalid-crossing-20260930-015001-825/`.
The hook/source defect was corrected after shutdown by restricting discovery
to executable `MEM_PRIVATE` regions. The actual launch server was rebuilt from
current source; its metadata contains `CRT18 suppressed` and not
`emitted room-load stream`. No corrected live run has occurred.

## Conclusion

### Corrected preparation attempt, 13:52 Toronto

The operator loaded Tython and stayed still. No doorway attempt was requested.
Discovery remained zero and the observer timed out without READY. A read-only
scan found candidate code above 2 GB and ambiguous short player-phase-data
prefixes. Both discovery defects are now repaired and tested offline; the
fresh instrumented crossing is still pending. See
`../PhaseLifecycle-20260930/live-20260930-135250-576/RESULTS.md`. No named callback,
gateway-state change or lookup removal was established; registry unchanged.

- Outcome: inconclusive/invalid; no named lifecycle fact established
- Confidence change: none
- Registry rows updated: none
- Runtime code: forwarding hook remains opt-in; self-match fixed; server rebuilt
  into the actual launch path with current CRT18 suppression
- Next single question: in a corrected destroy-only run, does genuine
  private-memory method discovery succeed and does
  `phsPhaseInfo.OnReplicationNodeDestroy` execute for stream `0x001B502E`?

