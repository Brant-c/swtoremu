# Experiment2026-09-30-17

## Question
Does returning through the gateway restore phase UI after captured node recreation and link restoration?

## Existing evidence
MovementTether-20260930/AUDIT.md and tether-evidence.json; experiment15 real-player sweep clear/floor succeeds; operator gateway traversed then blocked beyond, inward passage did not restore phase membership.

## Single variable
SWTOR_PHASE_REENTRY=1 after anchor refresh verified. Each launcher changes only that behavior relative to the prior accepted runtime. Reentry run is deferred until anchor behavior verified.

## Exact input
Server SHA256 5277D1037C36EFD58D7E8E77855EEC8BB0601B21102FEF62105AE3CCDAABBC0B. Exact dirty source/runtime identity in RetreatReentry-20260930/identity.csv. Both VerifyOnly passed. Opcode0D446E80 S2C, area source65B3 and session destination. Style8 player structure26 with206 Vector3 or25 phase-info reference, complete54byte state mask. Anchor101byte and restore143byte packet fixtures for selected player839B/839C, handles8/19 under MovementTether-20260930/packet-*.bin. First run retains captured2.4 leash; refresh250ms. Restore single captured classPhaseInfo create before link; no room/awareness replay. Defaults off.

## Predictions
Positive: RetreatMembership exited then reentered logs, named client phase callback resolves old retreat instance and UI banner restores.
Negative: both operations delivered/accepted but membership/UI fail to restore.
Inconclusive: no opt-in log, wrong selected player, malformed packet, failed world load, missing client acceptance proof. Offline checks do not prove client behavior.

## Evidence to preserve
Server NexusToR.log, client nexus_hook.log and launcher console/errors; user observed traversal/UI. Keep small full logs or bounded tails and SHA manifest.

## Result
Behavior-verified. Operator entering-story UI restored and barrier remains gone. Four exits/four reentries recorded in preserved full small logs: RetreatReentry-20260930/prelaunch-20261001-002114-440/RESULTS.md. Client first reentry resolves retreat FF5F184AAA9ECE77.

## Conclusion
Captured phase-info recreation then selected-player link restoration works repeatedly. Exit timing needs alignment. Does not establish general trigger runtime, group/quest eligibility, exterior NPC replication, or conversations.
