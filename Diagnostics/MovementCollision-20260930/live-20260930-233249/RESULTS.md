# Experiment15 live snapshot results
Operator: still blocked; phase departure and new tutorial observed, same successful phase state as previous run.
Client pid2604; diagnostic prepared23:32:49; normal-player coverage23:36:36. Snapshot captured while processes were still running; files are immutable snapshots, not final shutdown logs.

## Observations
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
