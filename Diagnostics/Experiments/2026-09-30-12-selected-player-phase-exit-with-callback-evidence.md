# Experiment 2026-09-30-12 — selected player phase exit with callback evidence

## Question

Does clearing the selected player phase link execute the normal local phase exit and allow exterior movement?

## Prepared run specification

The broad audit found experiment11 targeted captured player839C while startup
remapped to selected839B. Thus11 is inconclusive for the selected-player phase
lifecycle. This run corrects that one gameplay variable: exit field record nodeID
comes from ActiveCharacter._id. All other packet records/order and collision
behavior remain as11. Passive bounded callback instrumentation accompanies the
correction; it does not mutate gameplay.

Manual launcher: `Run-SWTORClassic-SelectedPhaseExit.cmd`. Full source/binary/input
SHA256 pins and effective configuration are in
`Diagnostics/SelectedPhaseExit-20260930/identity.csv` and `verify-config.log`.
Server SHA25649B019822627080EF9132E85E34B8E95E0D93E261678FE1384D1806915BECA4A.
S2C CRT opcode0D446E80 source65B3/runtime area destination8; stream1B502E at the
temporary doorway crossing. For selected839B/handle8 the complete120-byte packet
is `Diagnostics/PhaseTransitionAudit-20260930/clear-4000010E218A839B-8.bin`,
SHA2563A85682CF66160953CBEE04DEC2A232E69E11B58204C0010AA083A10AD3D79DF.
Only structure26/field25 phsPhase is supplied with UInt64zero before retained
container update and phase-info1AC6F6DC1F removal. Runtime IDs/handles may differ;
log and correlate the selectedID rather than assuming the fixture identity.

Settings: PHASE_EXIT_CLEAR_FIELD=1; TRACE_PHASE_UPDATE=1; CRT3=0;
PHASE_LIFECYCLE_LOG_ONLY=1; phase retry disabled; existing room/trigger traces.
Base launcher unchanged. Build, pinned native/script entry checks and selected
identity/packet integration pass; VerifyOnly launches no processes. Existing
WorldEntryOffline missing RequestWorldFadeIn observer failure is unchanged.

Procedure and deciding checkpoints: see SelectedPhaseExit-20260930/README.md.
Load/stand still and confirm PhaseUpdateHook installed marker before approach.
Then one doorway approach, stop at wall/outside, report banner and movement,
keep alive for bounded server/hook tail capture.

Positive lifecycle proof requires phase-field-matched, local-player-comparison-
passed, PHASE.OnPhasedInstanceUpdated entry/return, resolved new nameIDzero,
instance-change/exit branch evidence and player-phase-info-invalid. Gameplay
success additionally requires visible exterior movement. Successful callbacks
with wall persistence reject phase-link clearing as a sufficient physical fix.
Missing callbacks, installation ERROR, changed pins/config, wrong identity,
decode failure, or missing transaction delivery make the relevant inference
inconclusive. No broad memory scan/dump, guessed transfer or collision disabling.

Current result: READY, live result pending; client/server not launched by agent.
Both correction and new observers remain opt-in. Older11 launcher pins remain
stale intentionally. Save bounded live evidence under SelectedPhaseExit-20260930.
Live result: see Diagnostics/SelectedPhaseExit-20260930/live-20260930-213358/RESULTS.md. Corrected selected839B packet emitted/delivered/generic applied; operator still blocked. New observer preparation ERROR means named field/callback evidence absent; lifecycle inference inconclusive. Client closed; no observer-only rerun requested.
