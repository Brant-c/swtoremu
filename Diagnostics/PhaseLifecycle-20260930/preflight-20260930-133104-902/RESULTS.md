# Offline preflight — 2026-09-30, Toronto

No client/server launch or doorway attempt occurred. Existing dirty changes and
the invalid-run evidence directory were preserved.

## Input verification

- All 16 original identity rows: size and SHA-256 pass (`identity-before-check.csv`).
- Actual launch server SHA-256: `AA5F12BE0000FB45264DB5414EFEC2856C7970ECAFD8E615343048C5B51C35B6`.
- Server metadata: `CRT18 suppressed` present; `emitted room-load stream` absent.
- Fresh-process check: zero matching client/server processes (`process-check.json`).
- All 10 artifacts in the original invalid-run manifest still match their
  preserved hashes (`invalid-evidence-check.csv`).
- Source review: lifecycle signature discovery excludes `MEM_IMAGE`; checks
  committed executable private allocations and rejects non-unique signatures.
  Full live method identity, body overlap and forwarding ABI are still unverified.
- Trace launcher enables CRT3 and phase lifecycle tracing; retry defaults to
  disabled and spawn override is cleared. Both launch wrappers reject inherited
  SWTOR environment switches. Effective live values still require log checks.

## Changes from the preserved input

- `Watch-PhaseLifecycle.ps1`: exactly one HeroNode for each required identity
  before readiness; explicit remaining live gates; sequential scan timestamps;
  partial evidence and manifest preserved on failure.
- `Launch.ps1`: READY alone does not instruct doorway movement.
- `Test-PhaseLifecycleReadiness.ps1`: isolated offline readiness regression.
- `PREPARATION.md` and `identity.csv`: current review and pinned diagnostic inputs.
- This preflight directory: original observer/launcher/preparation/identity,
  dirty status, input verification, process check, and exact test results.

No server, hook, fixture, packet or gameplay source/binary was changed. No rebuild
was performed. Protocol-Evidence.csv remains unchanged.

Before/after worktree listings also show unrelated assembly-reference cache
status changes under Launcher, PacketAnalyser and SCPTExtractor during this
review. Their origin was not established; those files were left untouched.

## Tests

Exact output and exit codes are in `test-results.json`. All tests used x86
Windows PowerShell; assembly tests used the actual launch binary.

| Check | Outcome |
| --- | --- |
| PhaseLifecycleReadiness | Exit 0; valid baseline accepted, 12 invalid cases rejected |
| PhaseLifecycleSignatures | Exit 0; all four resource hashes/offsets/patterns agree |
| AreaRouting | Exit 0; handles 8/19, intact payload, unattached rejection, 11 packet types |
| AreaBlobFraming | Exit 0; 38 bodies, 17 CRT/2 awareness fixtures preserved |
| AreaWireRoundTrip | Exit 0; 54 fixture packets, byte-exact raw-deflate round trips |
| PacketDecoder | Exit 0; C5 preservation, 44 truncations, wrong variants/opcode/trailing bytes, dispatcher rejection/no gameplay |
| CapturedCharacterRemap | Exit 0; CRT2 25, effect1 2, On Enter 3 references |
| AreaEnterSignals | Exit 0; 37-byte rendezvous, 13-byte state, routing/entry point |
| PacketWorkbench | Exit 0; hex, envelope, registry, packed bounds, comparison |
| WorldEntryOffline | Exit 1; `Opt-in RequestWorldFadeIn gate observer is missing.` Later assertions not reached |

## Facts and limits

April extracted client scripts describe conditional removal from the parent's
`phsPhases`, clearing join overrides, a conditional gateway update, and the
destroy event. Player-phase-data create assigns `phsActivePhaseData = Me`; the
separate destroy code resets the unique-active name ID. These script semantics
do not establish live assignment or lookup mutation.

The previous invalid run preserves accepted crossing at 01:48:25, intended
destroy/generic apply 18, extra stale-server CRT18/generic apply 19, and the
operator's wall report. Its self-matched hook addresses and failed observer
cannot establish callback absence. The evidence remains in
`../../DoorwayControl-20260930/phase-lifecycle-invalid-crossing-20260930-015001-825/`.

No new independent live fact was produced here. Named callback execution,
gateway nesting, phase-info removal, CRT3 active state and native exterior
residency remain unresolved. A forwarding callback return alone must not be
treated as a read-back of the active-phase global. Whole-memory pointer scans
are delayed, non-atomic observations; pointer disappearance alone does not
identify `phsPhases` semantically. Discovery after CRT application may miss an
earlier player-phase-data create, so missing startup hits remain inconclusive.

Next single evidence-producing step: explicitly authorize the corrected
CRT3-on `Launch.ps1` run, then verify genuine non-overlapping private method
addresses, observer READY, effective CRT3, launch binary hash, CRT18 suppression
and retry disabled before requesting one doorway crossing. Experiment 07
remains pending until that valid baseline is preserved.
