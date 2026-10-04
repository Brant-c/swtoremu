# Experiment 2026-09-30-11 — player phase-field exit

## Question
Does clearing player phsPhase in the existing doorway transaction invoke normal phase exit and allow movement into gnarls_new?

## Evidence and single variable
PlayerPhaseFieldLifecycle registry row: phsEntity.GetPhaseInfo reads phsPhase; its Replication_Update handler calls PHASE.OnPhasedInstanceUpdated when that field changes. Experiment10 delivered phase-info destroy and selected/activated exterior but wall persisted. Existing PhaseExit had no player phase-field update. Only change for this run: add field25=0 to the same doorway transaction, before the existing effect-container update and phase-info removal. Collision flags, hooks, C7 decoder, CRT3 and startup remain as experiment10. No collision disabling or invented room RPC.

## Exact input
Manual launcher: Run-SWTORClassic-PhaseFieldExit.cmd. Launch.ps1 pins identity.csv; VerifyOnly passed, no processes launched. SWTOR_PHASE_EXIT_CLEAR_FIELD=1; CRT3=0; phase lifecycle log-only=1; native room/trigger traces=1; phase retry disabled.
Debug x86 server SHA256: 4E91FC57AE069DDF4D0811A390C22EE5DA489FDA36503BB866732C17415DBAE8. Hook unchanged185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED.
AreaClientReplicationTransaction opcode0x0D446E80, source65B3/destination runtime area service8, stream0x001B502E. Actual plaintext clear-8.bin120bytes SHA256 BAB4C9D42DB5C37DAE738BAD10F6C0B5118C512297EFC9A063BCA338D37916FE. Exact hex, handle19 case and decode report in Diagnostics/PhaseFieldExit-20260930/packet-verification.json. Player0x4000010E218A839C style7 structure26 index25 phsPhase0x40000002641F28CC UInt64=0; all other214 fields absent. Existing benign update retained, removal0x1AC6F6DC1F unchanged.

## Predictions and validity
Positive: server EXPERIMENT phsPhase=None line, retained named destroy callback delivery, story-area state disappears and operator can walk through doorway and continue outside. Exterior selected/activation logs provide corroboration, not success by themselves.
If wall remains with phase UI cleared and correct transaction applied, field clear alone does not fix wall. If callback/field application unproven, do not infer absence of effect from server emission alone. No new observer required for this run; missing normal lifecycle confirmation remains an evidence limit. Invalid: wrong launcher/pins/environment, duplicate stream, decoding error, no crossing log, startup failure, abilities fired or repeated doorway attempts.

## Procedure and logs
Start fresh launcher manually, load Tython and stand still; tell agent loaded for bounded config/server log inspection. Then one doorway approach, stop at wall or outside, report banner/state and keep client open. Preserve small current server NexusToR.log and client nexus_hook.log before close. No full dumps or repeated observer trials. Preserve-CurrentLogs.ps1 bounds oversized prior logs to2000lines.

## Offline validation
Build Debugx86 pass (existing warnings). Baseline and post-change routing, blob framing, wire round-trip and workbench pass. WorldEntryOffline fails before and after with unchanged missing RequestWorldFadeIn observer. Test-PhaseFieldExit and Verify-PhaseField pass: exact default46byte packet hash preserved, dynamic routing8/19, captured schema type/field assertion, one supplied field, retained container/removal bytes, exact end consumption. Offline success does not prove native field application or wall fix.

## Result
Ready for manual run; no live result yet. Runtime remains opt-in. Source/server/registry before copies retained in PhaseFieldExit-20260930. Old experiment launchers deliberately retain old pins and reject new server.
# Experiment11 live result — 2026-09-30 20:54:50
Operator reports still blocked at wall after one doorway attempt. Banner disappearance not answered; do not infer it.
Server new phase-field experiment branch emitted at20:54:50, stream001B502E,120bytes, field25None before phase-info removal; crossing(-63.40 -> -62.97). No CRT18. See crossing-server.txt.
Client hook same20:54:50: inbound routed0D446E80 source65B3/destination8; CrtApplyHook count17 entry and applied return; named phsPhaseInfo.OnReplicationNodeDestroy entry/return with stream001B502E. Exterior room selection/activation return; five measured trigger collision masks remain clear. This proves transaction delivery/apply path and destroy callback, NOT individual player-field application or OnPhasedInstanceUpdated execution.
Outcome: playable objective not achieved; clearing field alongside destroy did not visibly remove wall. Normal lifecycle hypothesis remains inconclusive because its specific callback not observed; do not promote opt-in default or repeat same run.
New identity caveat in saved hook at20:55:19: ReadinessVmHook character4000010E218A839B, whereas fixture/schema-derived player update node is4000010E218A839C. The distinction may be placed/root vs replicated node; audit it against existing character/replication records before any claim wrong-node or changing ID. GetPlayerCharacterNode comparison in phsEntity handler is essential and unverified for our target.
Logs bounded: hook-tail2000lines/server-tail700lines captured while client alive; crossing-server from1800line bounded tail. No new hooks/runtime change. User may close once agent final confirms capture. Next offline verify runtime local-player vs replicated node identity and self-handler invocation; if valid, trace phase-info link/parent/callback dispatch. No repeat doorway or manualcollisiondisable.

Subsequent audit resolves the identity caveat: startup explicitly remaps captured
839C to selected839B, while this generated clear bypassed remapping. Experiment11
is therefore invalid as a negative test of selected-player phase exit. Source
correction and offline integration are recorded in PhaseTransitionAudit-20260930.
Also, the old observer labeled UpdateGateway was actually SendCurrentPhaseInfoToGUI;
no-nested-gateway inference from that observer is invalid. Experiment12 prepares
the corrected identity and verified bounded phase callback collection.
