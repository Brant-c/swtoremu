# Experiment2026-09-30-16

## Question
Does updating the captured tether anchor permit movement beyond the2.4-unit spawn radius?

## Existing evidence
MovementTether-20260930/AUDIT.md and tether-evidence.json; experiment15 real-player sweep clear/floor succeeds; operator gateway traversed then blocked beyond, inward passage did not restore phase membership.

## Single variable
SWTOR_MOVEMENT_TETHER_REFRESH=1; reentry0. Each launcher changes only that behavior relative to the prior accepted runtime. Reentry run is deferred until anchor behavior verified.

## Exact input
Server SHA256 5277D1037C36EFD58D7E8E77855EEC8BB0601B21102FEF62105AE3CCDAABBC0B. Exact dirty source/runtime identity in MovementTether-20260930/identity.csv. Both VerifyOnly passed. Opcode0D446E80 S2C, area source65B3 and session destination. Style8 player structure26 with206 Vector3 or25 phase-info reference, complete54byte state mask. Anchor101byte and restore143byte packet fixtures for selected player839B/839C, handles8/19 under MovementTether-20260930/packet-*.bin. First run retains captured2.4 leash; refresh250ms. Restore single captured classPhaseInfo create before link; no room/awareness replay. Defaults off.

## Predictions
Positive: MovementTether startup log plus free movement beyond old radius and phase exit remains functional.
Negative: delivered anchor update and confirmed changed anchor still leave same barrier.
Inconclusive: no opt-in log, wrong selected player, malformed packet, failed world load, missing client acceptance proof. Offline checks do not prove client behavior.

## Evidence to preserve
Server NexusToR.log, client nexus_hook.log and launcher console/errors; user observed traversal/UI. Keep small full logs or bounded tails and SHA manifest.

## Result
Behavior-verified. Operator reports movement beyond barrier; preserved live client/server logs at MovementTether-20260930/prelaunch-20261001-001118-779/RESULTS.md. Server anchor refresh enabled00:02:12 and exit00:02:19. Decoded positions exceed old2.4-unit radius.

## Conclusion
The anchor refresh removed the previously observed movement restriction while retaining the captured leash and collision. Reentry remains a separate pending run17. No claim of complete exterior gameplay or authoritative movement simulation.
