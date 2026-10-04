# Experiment 2026-09-30-08 — Native physical room selection log

## Question
Does the April client select gnarls_new and take its immediate activation branch during one retreat doorway crossing?

## Existing evidence
Completed CRT3-on/off runs applied identical46-byte phase destroy and named
callback, wall persists. Experiment07 and PhaseInfoDestroyNamedCallback registry
row are the comparator. Authored retreat portals target gnarls_new in Tython.
B91AE0 updates area+298, calls B7C390; latter uses already-active +8C==3 or
immediate +90==6 branch, otherwise defers. Client-derived paths, no live proof.
Exact ABI/byte gates/limits: ../RoomSelection-20260930/README.md.

## Single variable
One opt-in native diagnostic logging room registration/selection/activation.
No server/protocol change. All28 priorCRT3-off settings match, only additional
SWTOR_TRACE_ROOM_SELECTION=1.

## Exact input
Dirty input hashes: ../RoomSelection-20260930/identity.csv; before inputs backed up.
CRT3=0, log-only=1, retry disabled. Config output/comparison saved alongside.
Existing S2C 0D446E80, component65B3/0008 stream001B502E; unchanged46-byte
phase-info destroy SHA256:
2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF.
New hook SHA256:
1B30BFD4DE2C822C83E36B23EF7C62624F7CBDA0589D1A130BD1AD154511E0DD.

## Predictions
Positive: samePID/area register maps gnarls_new to R. Crossing select requests
and stores R, activation logs +90==6 and +8C!=3 before, +8C==3 after. Supports
selection/immediate activation, not complete collision readiness. Already-active
+8C==3 is a distinct branch and must be reported separately.
Negative: valid crossing leaves selection in retreat, or selects exterior but
shows deferred activation. Distinguish selection failure from activation branch.
Invalid: missing INSTALLED/name mapping; wrongPID/area; unreadable fields;
cap reached; stale logs; changed packets/settings; no accepted crossing.
Absence constrains logged paths only, not all possible native content handling.

## Evidence to preserve
Fresh server/hook logs, launch timestamp/logs, inputidentity, exactdestroybytes
and workbenchcomparison. Operator standingstill, one crossing, wall/outside;
no abilities. Preserve before restart.

## Result
Completed live run16:34:05. At16:39:58 native selection changed retreat_d to
gnarls_new, activation entered/returned in already-active3/6 state. Startup
had already activated exterior2/6->3/6. Same46-byte destroy, named callback
entered/returned, no nestedgateway recorded. User remained atwall.
See [preserved result](../RoomSelection-20260930/live-20260930-163405/RESULTS.md).

## Conclusion
Selection and activation calls Behavior-verified. Failure of these calls is
falsified for this run; collision readiness and blocking collider remain
unresolved. Diagnostic retained opt-in; no fix or new packet. Nextoffline
target is gateway/trigger collision path after successful room selection.
