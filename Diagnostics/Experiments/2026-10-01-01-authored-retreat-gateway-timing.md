# Experiment2026-10-01-01 — Authored retreat gateway timing

## Question
Does symmetric crossing at authored gateway X remove delayed exit UI while preserving repeated entry/exit?

## Existing evidence
Run17 four exits/four returns; operator story UI restored and barrier gone, exit slightly late. Authored gateway centerX=-63.6167984009. Jedipedia phsPhasedInstanceClassMethods14988075381240041184 reviewed: UI methods display entering-story banner and clear GUI on exit; no client body proves exact production server exit volume.

## Single variable
SWTOR_RETREAT_GATEWAY_TIMING=1; anchor refresh/reentry remain enabled. Per-character reset also prevents stale selection history; this run uses same selected character.

## Exact input
Runtime/source hashes in RetreatGateway-20261001/identity.csv. Existing101byte anchor,143byte membership recreation,120byte clear/removal serializer unchanged. Timing uses authored center with +/-0.05 emulator-policy hysteresis and existing corridor, evaluating segment intersection. No claim of native rotated volume implementation.

## Predictions
Positive: exit clears UI near gateway, return restores entering-story banner, repeated cycles remain stable and exterior movement free. Negative: UI still late or toggles while stationary, return fails.

## Evidence to preserve
Small full client/server logs, manifest, RetreatMembership timestamp and position, user observation.

## Result
Behavior-verified local timing improvement. Operator reports seemed better. Server exit00:35:14, entry00:35:19, exit00:35:23; matching client callbacks resolve None/retreat/None and return normally. Full small logs: RetreatGateway-20261001/prelaunch-20261001-003805-442/RESULTS.md. This run has one complete return cycle, prior run17 four.

## Conclusion
Local Tython retreat behavior accepted as working baseline. Production rotated trigger semantics/general phase eligibility remain outside this compatibility detector. NPC interaction and exterior replication proceed separately.
