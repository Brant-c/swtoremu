# Experiment2026-09-30-15 — bounded local-player collision and supporting-floor outcomes

## Question
After confirmed phase exit, does normal player movement encounter a known retreat trigger, another collider, or a supporting-floor rejection?

## Existing evidence
Experiment14 corrected style8 clears selected player's phsPhase: client oracle exit and UI departure observed, barrier remains. Evidence PhaseFormat-20260930/live-20260930-222139/RESULTS.md.
Room selection returns exteriorF4FD9000 after linked-room activation22:22:01 in supplied excerpt; full physics readiness unproved. Existing TriggerCollision result=0 snapshots are placeholders, not collision results.
Jedipedia April stand and behavior scripts cross-checked with pinned native paths in PlayerMovement-20260930/NATIVE-COLLISION-PATH.md.

## Single variable
Enable one passive movement collision diagnostic. Three ABI-verified query/context hooks measure existing engine calls without extra engine queries or writes. Phase-clear packet and earlier phase/room observers retain experiment14 settings.

## Exact input
- Dirty source/runtime inputs: MovementCollision-20260930/identity.csv; previous identity left intact.
- DLL SHA256: 1D9E7A3AFCA3BF8CCF8C270852AE91A2C1F577A4E2C3EDDE2C81FB19E5C12FB7
- Switches: SWTOR_TRACE_MOVEMENT_COLLISION=1, SWTOR_PHASE_EXIT_CLEAR_FIELD=1, SWTOR_TRACE_PHASE_UPDATE=1, SWTOR_TRACE_ROOM_SELECTION=1, SWTOR_TRACE_TRIGGER_COLLISION=1, SWTOR_ENABLE_UNVERIFIED_CRT3=0, SWTOR_PHASE_LIFECYCLE_LOG_ONLY=1; retry disabled. Generic launcher baseline unchanged. VerifyOnly passed.
- Local native sweep7B7450 cdecl6args filtered caller737737 and active player's behavior+F0; supporting queryCEF540 cdecl8args filtered callers7394E4/73966D under738F80 stdcall1arg same-player context.
- Network: no new opcode/body/order. Retain corrected120byte AreaClientReplicationTransaction phase clear documented experiment14; no CRT18/transfer guess.
- Exact prefixes/relocations: MovementCollisionPrefixes.h generated from pinned native PE SHA2562B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494.

## Predictions
Positive: prepared marker, coverage=local-player-normal-update, changing proposed position with collision hit and contact identity, correlated with user still blocked and phase exit. knownRetreatTrigger=1 directly connects a blocking contact to tracked trigger; another identity redirects investigation to that object and room. Support result0 near attempt can identify missing support, but alone cannot prove sole cause.
Negative: normal movement coverage with no collision contacts and successful supporting floor queries during barrier attempt weakens tracked-contact/floor hypotheses; inspect subsequent movement application and controller gates.
Inconclusive: unsupported/failed hook installation; absent normal update coverage; no doorway movement samples; invalid result range; exhausted cap before attempt; contact node not readable; different server/phase baseline. Do not interpret missing logs as successful movement.

## Evidence to preserve
Server NexusToR.log and client nexus_hook.log. New launcher preserves prior logs; input manifest and prior supplied room excerpt retained. Operator reports whether doorway traversed and story banner vanished. Review only decisive MovementCollisionHook, phase and room lines with timestamps; retain full small logs or bounded tails.

## Result
Pending manual run. ReleaseWin32 build and configuration checks passed. No client launched by agent.

## Conclusion
- Outcome: pending
- Confidence: Client-derived ABI and record layout; live contact outcome unverified.
- Registry: LocalPlayerCollisionDiagnosticABI.
- Runtime: passive opt-in only; no collision workaround.
- Next question: which physical result limits attempted doorway movement?

## Live result

- 48 sampled normal-player sweeps: all collision0, all result lists empty, query output equals proposed position in displayed records.
- 48 sampled same-player supporting-floor queries: all result1/outputValid1; normal predominantly0,1,0.
- Player EB89C000 room98 changes D2ADA500 toF4A69500 at sample12 (23:36:39). Registered F4A69500 name=gnarls_new23:36:15. Selected exterior returned23:36:40.
- Phase field matched and oracle resolves newInstanceNameID0; exit gateway/GUI branch completes23:36:40.
- Near stop23:36:41, start=-62.9180,-6.8988,-126.2895; proposed/output=-62.9151,-6.8988,-126.2866; collision0/hits0 and floor result1. Supporting queries later preserve that same position.
- Both48-sample budgets were eventually reached after the initial doorway attempt; initial stop was captured before exhaustion. No inspection failures found in snapshot. Room residency and supporting floor exist; full destination content readiness still not established.

## Interpretation and limits
No blocking contact identified by this sampled sweep. Positive-floor observations weaken missing-support hypothesis at measured positions. These results do not establish that all collisions are absent: 250ms sampling can miss brief contacts, and sweep can be bypassed when movement delta is effectively zero. The proposed positions are already tiny near the stopped location; physical rejection may precede this call, occur in an unsampled query, or happen later in movement processing.

## Next offline target
Trace where character current-position input is formed before737520/7B7450 and how it is applied afterward. In byte-verified722250, desired displacement uses behavior+DC times frame duration and heading+E0, then invokes character virtual slot+CC at7223A4 before controller737120. There is also manager723860 and later position application. Pinned PE CharacterNode primary table1151154 slotCC resolves006D5FB0. Audit that exact function and position application before any new observer. Do not disable collision, add transfer packets, or request another identical run.

## Outcome
Phase exit remains behavior-verified; sampled collision and floor outcomes observed. Actual wall mechanism unresolved. Preserve passive diagnostic opt-in; no runtime changes during this live run. See manifest.json, decisive-excerpts.txt and server-phase-excerpts.txt.

Evidence: MovementCollision-20260930/live-20260930-233249/RESULTS.md.
