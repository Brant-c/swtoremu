# Experiment 2026-09-30-10 — C7 movement decoder control

## Question
Does accepting native-proven C7 movement with correct end-position offsets change the retreat doorway wall outcome?

## Existing evidence
Client-derived AA6920 writer, pinned April PE with341 printed prefixes verified; Captured ten complete56-byte C7 packets. See ../MovementC7-20260930/FINDINGS.md and ../TriggerCollision-20260930/live-20260930-172807/RESULTS.md. Prior run switched exterior and destroyed phase-info via C5 while wall persisted; five known trigger flags clear. C7 rejection causing the wall remains a hypothesis.

## Single variable
Server accepts captured C7 mask in addition to C5 and decodes end position after its12-byte vector. Existing reply, phase-exit and client hook code unchanged. All experiment09 environment settings retained.

## Exact input
- Launch Run-SWTORClassic-MovementC7.cmd; identity and verified-config.txt in ../MovementC7-20260930/.
- Server SHA256:150A707AA20D324BEC1B19671BEE9B65CC1B3227BBB35A0654E179BBEF37C9CD.
- Hook SHA256:185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED.
- CRT3off, retry disabled, room/collision logs on, lifecycle log-only.
- C2S61116AD5 component65B30008; C7 body48/full56. Exact saved packet ../TriggerCollision-20260930/live-20260930-172807/movement-c7-first.bin.
- No new packet/reply requirement introduced.

## Predictions
Positive: complete C7 accepted in server AreaPoll logs, correct position reaches crossing detector once. If client continues outside, doorway progress is behavior-verified for this run.
Negative: accepted C7, completed crossing/destroy/room selection and wall persists falsifies C7 rejection alone as the wall cause.
Invalid: wrong hashes/config, incomplete movement/crossing evidence, hook failure or diagnostic caps before relevant events, unrelated actions.

## Evidence to preserve
Small current server/hook/launcher logs and hashes; C7 body and positions; room selection/collision snapshots; destroy/callback; visible wall/outside result. No process scans or dumps.

## Result
Pending one fresh run. Offline build/tests pass except pre-existing world-entry observer failure unchanged before/after. VerifyOnly passed; no processes launched.

## Conclusion
Pending. Load standing still; verify config; one crossing without abilities; stop wall/outside and keep client open for bounded log preservation.

Live result: nine C7 accepted, one crossing/destroy, exterior selection and callback complete; operator still stuck. C7 decoder acceptance/crossing Behavior-verified; C7 rejection alone wall hypothesis falsified. See ../MovementC7-20260930/live-20260930-180457/RESULTS.md. Decoder retained; no ack change.
