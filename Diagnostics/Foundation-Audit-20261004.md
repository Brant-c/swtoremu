# Character entry and phasing foundation audit — 2026-10-04

Read-only runtime review. No server, launcher, fixture, or client behavior changed.
Scope: selected-character loading, active Tython startup, movement tether,
retreat membership, and their shared state. This is a source/configuration audit,
not a new native-client acceptance run. Protocol conclusions below summarize
existing evidence; new causal concerns are explicitly hypotheses.

## Conclusion

The playable baseline is a capture-replay compatibility implementation, not a
complete character/area lifecycle. Taxi feature development should yield to a
bounded foundation audit and correction. Preserve the accepted baseline as a
control; do not remove all workarounds at once or restart disproven room-stream
experiments. Current evidence does not prove that phasing causes the NPC faults.

## Actual entry path

1. CompatibilityLauncher waits for data/scripts/spec initialization and rewrites
   a module-report send into CharacterListRequest through client execution-context
   edits (CompatibilityLauncher.cpp around lines 1630–1680).
2. SelectCharacterRequest constructs Character(ID), whose constructor loads no
   persisted character data. WorldSendToArea always names Tython instance 1.
3. ModulesList sends a fixed world startup; AreaModulesList echoes its report and
   sends the fixed area bundle once. Its sent flag is set before completion.
4. AreaStartupBundle sends SetCharacter early, schema/hack-pack data, raw RPCs,
   captured CRTs, a fixed spawn teleport after CRT2, awareness, and effects.
5. CRT payloads are modified for player identity, phase-child ordering, Safe
   Login suppression, mobility, and player-loaded state. Loading completion also
   relies on a client branch patch. Thus rendering is not proof of an intact
   original entry handshake.

## Active workarounds and limitations

| Mechanism | Active implementation | Limitation |
|---|---|---|
| Captured world state | .acrt/.aaw/effect fixtures and opaque startup RPCs | Snapshot replay substitutes for generating state from the selected character and current area |
| Player identity substitution | CapturedCharacterRemap scans packed and little-endian byte patterns | Not field-aware; other captured object identities remain fixed |
| Fixed destination/spawn | WorldSendToArea and AreaStartupBundle | Every selected character enters the captured Tython start; no saved location/lifecycle selection |
| Phase child moved earlier | GeneratedPhaseCandidate CRT1/CRT4 overrides | Captured phase-info node moved before player creation; fixed owner/instance identities with selected-player remap |
| Login protection omitted | CRT2 node/container removal and effect-event suppression | Protection expiration/removal lifecycle is bypassed |
| Free mobility forced | Rewritten CRT16 field 9 | Successful separate-field delivery does not settle why combined encoding fails |
| Loaded flag forced | Rewritten CRT17 fields 100/129 | Final captured transaction sets readiness rather than deriving it from a complete server lifecycle |
| Loading confirmation bypass | CompatibilityLauncher CheckContinue branch patch | Takes local PhaseNeedsContinue(false) path instead of normal server confirmation; asset waits retained by patch design |
| Moving tether anchor | PlayerMovementState, field 206 every >=250 ms | Trusts finite client coordinates; no authoritative simulation or area ownership validation beyond current guards |
| Retreat membership detector | RetreatGatewayState plane/corridor/hysteresis | Local axis-aligned approximation; initial membership assumed inside; no quest/group/rotated trigger evaluation |
| Phase restoration | AreaPlayerMovementUpdate captured phase-info create | Reuses fixed captured child/parent and restores player field 25; not a general phase allocator |
| Phase exit effect update | AreaReplicationDestroy | Also replaces positive effect-container contents with captured slot 1, unrelated to phasing |
| Unhandled requests | Generic RPC swallow and area poll modes | Only selected feature handlers are implemented; an unanswered request cannot establish that initialization completed normally |

Active settings are inherited through Taxi Launch.ps1 into Trace-Tython.cmd;
the latter adds mobility/load/login/CRT-override/loading-fallback behavior.
Today’s server log confirms CRT1 and CRT4 overrides, login omission, CRT16/17
rewrites, movement tether refresh, and retreat exit. CRT3 is suppressed. The
compatibility log confirms the CheckContinue patch was installed.

## Concrete couplings / defects to prioritize

1. **Phase exit overwrites an unrelated effect container.** The serializer emits
   a replace-map containing only captured slot 1. Ability replication uses that
   same positive container for additional effects. Hypothesis: exiting after
   applying buffs can remove their client container references while server
   effect bookkeeping still retains them. No such live failure was tested here.
   Since phase clear already supplies an object update, investigate whether the
   extra container write is necessary before designing a controlled removal.
2. **Startup completion is not transactional.** AreaModulesList sets the sent
   flag before Send finishes. The merged-awareness construction failure branch
   sends original awareness then returns before OnEnter and remaining CRTs.
   This branch is inactive in today's separate-taxi mode, but can mark partial
   initialization complete. Other exceptions have the same flag problem.
3. **Area lifecycle state is connection-scoped.** Startup flags initialize in
   TORGameClient's constructor. The reviewed area attach and character setter
   do not reset them; movement state resets only on character-ID change, not
   area attachment. A second area/session entry is not represented cleanly.
4. **Movement routing is not checked at the gameplay boundary.** CMsg61116AD5
   decodes the component but PlayerMovementState receives only client/position.
   Its guards check the stored active area/service, not that this report belongs
   to that service. Finite bounds are useful, but do not establish routing or
   authority. No wrong-component run was performed.
5. **Entry signaling is internally inconsistent.** AreaEnterSignals.Fire is
   called only for movement Echo mode; the active launcher uses Swallow. Its
   configurable AreaServer state/rendezvous path is therefore not executed by
   that call in today's mode. Setting the environment variable does not prove
   the corresponding packet was sent.

## What is and is not established

Behavior-verified: accepted local free movement, retreat exit/reentry, and named
phase callbacks (Protocol-Evidence.csv; RetreatGateway and RetreatReentry run
results). These remain valuable controls. They do not establish general area
transition, authoritative movement, dynamic awareness, or phase eligibility.

Today's taxi node errors precede the logged retreat exit. This contradicts a
claim that that later crossing caused those earlier errors, but does not rule
out a common startup/schema problem. Medcenter targetability remains unresolved.
No claim that every visible exterior model is a fully initialized gameplay NPC.

Legacy PhaseExit's one-shot static detector is bypassed when PHASE_REENTRY=1.
Its room-activation/awareness helper methods have no calls in the reviewed path.
CRT18/instance retry are disabled in the active launcher. These stale code paths
are documentation hazards, not evidence of active room streaming.

## Bounded next work before taxi travel

1. Preserve a no-new-feature control with the accepted entry/movement settings;
   record exact active switches and sent payload transformations.
2. Audit schema26 field encoding, especially mobility enum versus Boolean loaded
   state, using matching native readers/local packed-token reference. Establish
   whether record splitting masks a serialization defect; do not assume it does.
3. Remove unrelated phase-exit effect-container mutation only after a byte-level
   review and opt-in controlled buff/exit/reentry run.
4. Recover original loading phase-confirmation request/response from extracted
   script and native handler evidence. Replace the client fallback only when the
   normal contract is known; keep the current working control available.
5. Make character/area entry completion and reset boundaries explicit, with
   fixture replay retained initially. Do not rewrite unrelated login/repository.
6. Determine whether the captured medcenter exists as a targetable gameplay
   object before/after crossing; trace its phase/interaction initialization.
   This is a better general-NPC control than synthesizing a taxi immediately.

No new client launch or protocol change was performed. Offline tests were not
rerun because this review changed documentation only.
