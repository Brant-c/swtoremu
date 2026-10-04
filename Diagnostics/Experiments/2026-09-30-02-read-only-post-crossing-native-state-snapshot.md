# Experiment 2026-09-30-02 — Read-only post-crossing native state snapshot

## Question
What does the existing external Read-WorldTravelState observer read from the
still-open client after the blocked doorway control, without hooks or writes?

## Existing evidence
Experiment 2026-09-30-01 records accepted C5 crossing, destroy serialization,
native replication apply return and operator-reported wall persistence.
The screenshot supplied afterwards shows rendered world, green doorway,
Master's Retreat minimap text, and no loading overlay. Historical chat text
"Entering Story Area [Owner: Taci]" is not proof of current phase membership.

## Single variable
One external read-only sample using unchanged Diagnostics/Read-WorldTravelState.ps1.
OpenProcess requests 0x410 (query/read); the script uses ReadProcessMemory and
CloseHandle, no writes, suspension, hooks, packet injection or native calls.
This is a post-control observation, not a second doorway crossing or a controlled
before/after native-state comparison. It does not alter gameplay configuration.

## Exact input
Script SHA256 A81B90FD5D907015C74668CE15003704F1BBD0DB2B608BA30B8D805BBB5269C4.
Source preserved as ../DoorwayControl-20260930/live-analysis/Read-WorldTravelState.source.ps1.
Invoked with System32 Windows PowerShell -NoProfile -ExecutionPolicy Bypass -File.
Process/build identity is in experiment 01 and live-analysis/processes.json.
Read interval: 2026-09-30T00:09:49.4853656-04:00 through 00:09:50.0008588-04:00.

## Predictions and procedural limitation
A non-null area pointer plus a readable +0x8C field gives a numeric state sample.
A null pointer or failed read gives no state conclusion. A snapshot cannot prove
which handler wrote a value or whether it changed at the crossing.
The allocator initially failed formatting the second daily numeric ID. The shell
continued and the observer ran before this record could be allocated. This record
is retrospective, not a claim of successful pre-registration. The allocator was
fixed by casting its measured next ID to int; a subsequent invocation successfully
allocated 2026-09-30-02. No runtime code changed. Do not treat this as a newly
controlled lifecycle experiment.

## Evidence to preserve
../DoorwayControl-20260930/live-analysis/native-world-travel-state.log
native-state-start.txt / native-state-end.txt / native-state-disassembly.txt
user-client-open.png (SHA256 298DB0E8A6BF677D9E1FDE99BAA9376794B9524577C655EEDBB061AB3A52A778)
../DoorwayControl-20260930/client-open-20260930-000924-891/manifest.csv

## Result
Observer exit 0. PID 28416: travel manager 0x01776DF8, area pointer 0xF43739A0,
area+0x8C = 3. Resource worker state 5, queued=0, pending resource reads=0,
active reads=0/50, resource bytes=0. Another enumerated process has a null area
pointer; its script block has no PID label, so do not assign it solely by order.

Static disassembly at VA 0x0074F2E0 loads [ebx+0x28], then 0x0074F2E7 compares
[pointer+0x8C] to 3. Nearby code references several loading-stage strings and
calls different functions for them. This supports that the field is examined by
loading-related code; it does NOT by itself map 3 to "waiting for server to
notify area of new player". No native write was observed and no complete state
machine was recovered. Resource queue idleness does not prove all required
assets or collision were requested or resident.

## Conclusion
New evidence: a numeric native-state snapshot while the user is blocked.
No proof of specific phase-info removal, gnarls_new residency, collision readiness
or a missing notification's identity. No protocol confidence promotion.
Next single step: trace writers of this specific area object's +0x8C state and
recover their call paths, before naming or sending a candidate transition packet.
