# CRT3-on preparation result — no doorway attempt

The desktop-access launch began at 13:52:50 Toronto. The operator loaded Tython
and stated they had not moved. Startup CRTs 1–17 entered/returned through the
generic apply hook at 13:56:21; the area startup bundle completed at 13:56:23.
CRT3 was enabled. The server executable remained the corrected pinned build.
This was not a valid lifecycle baseline: all four named discovery counts were
zero and the observer timed out without READY. No named callback absence claim
is supported, and no doorway destroy was requested as part of this experiment.

A read-only full-32-bit private/executable scan at 13:58:24 found 11 short-prefix
candidates in PID 40024, all above 2 GB. PID 37844 had none. The hook and external
observer had wrongly bounded their searches to below 0x7FFF0000. The short
player-phase-data signatures were also ambiguous (five create, four destroy).
Exact address/type/protection evidence and 512-byte candidate reads are in
`full-address-discovery-code/`. The first scan's summary Address field was
incorrect because PowerShell resolved the array's Address method; the per-hit
CSV was valid and the second scan corrected that summary.

Longer pinned prefixes (54 bytes for phase-info destroy/gateway update, 56 bytes
for player-phase-data create/destroy) distinguish the intended candidates while
ignoring only canonical external CALL rel32 operands. The actual C++ matcher
was tested against all 11 saved code samples: four intended prefixes accepted,
seven unrelated prefixes rejected. All 220 fixed/relocation-byte mutations
passed. This is discovery evidence, not named callback or state-mutation proof.

The hook now scans the full 32-bit address range with wide address arithmetic,
retains executable MEM_PRIVATE filtering and uniqueness checks, and rejects
overlapping prefix windows. The external observer uses the same full range and
requires x64 PowerShell. The player-phase-data return label no longer claims
the active global was read back. Release x86 hook build passed; signature/resource
checks and the 12-invalid-baseline readiness regression passed. The initial
sandboxed build failed in MSBuild FileTracker with E_ACCESSDENIED; the normal-access
build passed. No server packet, fixture or gameplay behavior was changed.

The operator closed the client after asking to stop repeated restarts. No new
restart occurred until they asked when to run again. Logs were preserved in
`../../DoorwayControl-20260930/phase-lifecycle-no-crossing-final-20260930-141141-514/`
and `../../DoorwayControl-20260930/phase-lifecycle-closed-before-restart-*`.
Original hook/source and the run identity are preserved here. Protocol registry
unchanged. The next evidence-producing step is a fresh corrected CRT3-on launch
using `Run-SWTORClassic-PhaseLifecycle.cmd`, then readiness verification before
requesting one doorway crossing. CRT3-off remains deferred.
