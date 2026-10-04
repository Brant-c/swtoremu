# Experiment 2026-09-30-07 — CRT3-off phase bootstrap ablation

## Question

With the corrected destroy-only baseline and no other runtime change, can the client enter Tython and walk when reconstructed CRT3 is disabled, and does doorway phase behavior differ?

## Existing evidence

The valid corrected log-only CRT3-on comparator is now preserved at
`../PhaseLifecycle-20260930/live-20260930-145102-logonly/RESULTS.md`.
At 14:57:26 accepted C5 triggered the exact destroy; named phase-info destroy
entered/returned, no nested gateway update was recorded, and the wall persisted.
CRT3 emission and its named create callback were independently observed earlier.
The old invalid runs below are not the comparator.

Earlier live controls entered a rendered, movable Tython with the matched CRT1
override, mobility/player-loaded patches, safe-login removal/suppression, and
reconstructed CRT3 enabled. CRT3 uses a known incompatible compact schema and
is not authoritative. The April client scripts say
`phsPlayerPhaseData.OnReplicationNodeCreate` assigns
`$PHASE.phsActivePhaseData = Me`, independently of the phase-info child. It is
therefore a material phase-bootstrap confound. The completed ablation below
shows that usable startup under these settings does not require it.

Experiment 06's first attempt is invalid and must not be used as the CRT3-on
comparison: its stale server emitted CRT18 and its hook self-matched. This
ablation runs only after a corrected destroy-only CRT3-on baseline is complete.

## Single variable

Change only `SWTOR_ENABLE_UNVERIFIED_CRT3` from `1` to `0`. Retain the same
current server/hook binaries, matched CRT1 override, movement/player-loaded and
safe-login startup changes, trace switches, destroy-only PhaseExit behavior,
packet policies, character, route, and operator actions as the corrected
experiment-06 baseline. Do not add a packet, trigger, retry, awareness resend,
or ability action.

## Exact input

- Identity: use `../PhaseLifecycle-20260930/identity.csv` after it passes
  launch-time verification; preserve a run-specific copy and effective switches.
- Launcher: `Run-SWTORClassic-PhaseLifecycle-Crt3Off.cmd`, which sets CRT3 to
  `0` through Launch-Crt3Off.ps1 and the shared Launch.ps1. Both use the same
  log-only trace configuration, with no full-memory observer. Configuration-only
  comparison passed: all 28 SWTOR settings match except CRT3=1 versus 0.
  See `../PhaseLifecycle-20260930/crt3-off-preparation-20260930-150532-698/`.
- Expected difference: no startup S2C CRT3 fixture
  `tython_blockout-4611686019869492753-1.3.acrt` (55 bytes, SHA-256
  `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`).
- Existing doorway input, if startup remains usable: S2C `0x0D446E80`, handles
  `0x65B3/0x0008`, stream `0x001B502E`, node `0x1AC6F6DC1F`, with no CRT18.

## Predictions

Positive observation:

- CRT3 is explicitly skipped, no player-phase-data create callback occurs, yet
  Tython renders and the character walks. Compare phase banner/state and the
  same one-time doorway destroy/callback/wall result with the corrected CRT3-on
  baseline. A changed phase outcome supports CRT3 as an active confound.

Negative observation:

- Disabling CRT3 prevents usable world entry or movement, or produces no
  observable phase-lifecycle difference from the corrected CRT3-on baseline.
  The latter weakens—but does not prove absence of—CRT3's phase-state effect.

Invalid/inconclusive conditions:

- No valid corrected CRT3-on comparator; any other switch/binary/fixture
  differs; CRT18 or another outbound experiment is emitted; unsupported C7 is
  acted upon; no explicit CRT3 skip proof; startup fails for an unrelated
  reason; abilities are used; or logs are not preserved.

## Evidence to preserve

- Server log with effective switches, startup CRT list, accepted C5 movement,
  destroy/suppression lines, and exact packet bytes.
- Hook log showing method-discovery validity, generic applies, named callbacks,
  and absence of player-phase-data create/destroy hits where applicable.
- PacketWorkbench report for the exact destroy and a CRT emission inventory
  proving CRT3 absence.
- Operator observation of world entry, movement, banner, loading, collision,
  and wall; screenshot only if it adds independent evidence.

## Result

Valid desktop run launched 15:11:20 Toronto. CRT3 explicitly suppressed at
15:14:36, all four hooks installed, startup completed 15:14:37, and the operator
loaded and walked. No named player-phase-data create/destroy callback recorded.

At 15:19:43 accepted movement crossed `-64.87 -> -62.94`. The server emitted
the identical 46-byte destroy (PacketWorkbench comparison: zero differences)
and suppressed CRT18. Generic apply 17 brackets named phase-info destroy entry
and return. No nested gateway update was recorded. Operator reported still
stuck at the wall after walking into it for a second.

See [preserved result](../PhaseLifecycle-20260930/live-20260930-151120-crt3off-logonly/RESULTS.md)
for hashes, exact bytes, counts, full-log snapshot and observation limits.

## Conclusion

- Outcome: usable startup without CRT3 confirmed under these settings; a wall
  fix or changed observed destroy/gateway behavior from disabling CRT3 falsified.
- Confidence change: CRT3 is less supported as the cause of the wall. No claim
  of equivalent global phase state or identified conditional branch.
- Registry rows updated: PhaseInfoDestroyNamedCallback gains this corroborating
  run; general replication schema remains Captured.
- Runtime code retained, reverted, or still opt-in: no runtime edits during this
  run; CRT3 remains opt-in. No default configuration change made.
- Next single question: use static April client/script/asset evidence to identify
  the gateway/room-content path; no further client run until a concrete target.

