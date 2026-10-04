# Phase lifecycle preparation — 2026-09-30

## Status

Current instructions: use `LOG-ONLY-PREPARATION.md`. The user explicitly replaced
the external full-memory observer with server/client named-hook logs. The
desktop launcher now forces CRT3=1 and was checked with `-VerifyOnly` before
launch. No external READY is required for this narrower callback question.

Latest preparation (14:19 Toronto): the corrected attempt loaded Tython but
made no doorway attempt because discovery failed. Its evidence and the wider
read-only discovery are in `live-20260930-135250-576/RESULTS.md`. The full-32-bit
relocated-prefix hook is now built and tested; observer bounds are corrected.
The client and servers have exited. Use `Run-SWTORClassic-PhaseLifecycle.cmd`
from the desktop for the next CRT3-on baseline; it invokes Launch.ps1. Do not
use the CRT3-off launcher. The updated identity manifest pins the repaired
inputs and new diagnostics. No new live callback result exists yet.

No further client launch occurred after the user asked to stop before launching.
The next CRT3-on run is prepared but unexecuted. Experiment 07 is a separately
prepared CRT3-off ablation and must not be combined with the baseline run.

## Corrections after the invalid attempt

- Rebuilt current `PhaseExit.cs` into the actual launch binary
  `SharpServer/bin/Debug/NexusToRServer.exe`. The compiled metadata contains
  `CRT18 suppressed` and does not contain `emitted room-load stream`.
- Restricted lifecycle signature discovery to executable `MEM_PRIVATE`
  allocations. This excludes the hook DLL's own signature constants, which
  caused the invalid attempt's overlapping false addresses.
- Corrected the observer's shared log access and byte-array scan carry length.
- Pinned source, binaries, client, scripts, fixtures, observer, tests, and both
  launch paths in `identity.csv`.

## Validation

- Release x86 hook build: pass.
- Debug x86 server build into the actual launch path: pass, warnings only.
- `Test-PhaseLifecycleSignatures.ps1`: pass for all four pinned methods and
  decrypted offsets.
- `Test-AreaRouting.ps1`: pass.
- `Test-AreaBlobFraming.ps1`: pass.
- `Test-AreaWireRoundTrip.ps1`: pass.
- `Test-PacketDecoder.ps1`: pass against the rebuilt server.
- `Test-CapturedCharacterRemap.ps1`: pass.
- `Test-AreaEnterSignals.ps1`: pass.
- `Test-PacketWorkbench.ps1`: pass.
- `Test-WorldEntryOffline.ps1`: retains the established failure at its first
  assertion: `Opt-in RequestWorldFadeIn gate observer is missing.` Later
  assertions were not reached.

## Next run gate

### Offline readiness review at 13:31 Toronto

All 16 original pinned inputs passed both size and SHA-256 verification. No
`swtor`, `swtor-emu`, `NexusToRServer`, `ShardListServer`, or `nexusclient`
process was found. The launch server still contains `CRT18 suppressed` and
does not contain `emitted room-load stream`. Hook discovery remains restricted
to committed executable `MEM_PRIVATE` regions; unique short signatures do not
by themselves prove complete method-body identity or non-overlap in a live run.

Review found that the external observer could report `READY` despite missing
phase HeroNodes. It now requires exactly one HeroNode for the gnarls control,
phase-info child, parent instance, and player-phase-data identity. Missing,
duplicate, and non-HeroNode matches abort without readiness. `ready.json`
includes those counts. Readiness text and the launcher's final instructions
now retain the independent method-address and server/switch gates before
movement. Failures preserve partial hook evidence and a manifest; summaries
record scan start/end times and explicitly describe sequential scanning.

`Test-PhaseLifecycleReadiness.ps1` passed a valid baseline and all 12 rejected
baseline cases. Signatures, AreaRouting, AreaBlobFraming, AreaWireRoundTrip,
PacketDecoder, CapturedCharacterRemap, AreaEnterSignals, and PacketWorkbench
passed against the unchanged launch binary. WorldEntryOffline still exits 1
at `Opt-in RequestWorldFadeIn gate observer is missing.` Later assertions were
not reached. No rebuild was needed because only observer/launcher diagnostics
changed. No protocol registry change or new live fact was established.

Original inputs and worktree status, hash checks, process check, and exact test
output are preserved in `preflight-20260930-133104-902/`. `identity.csv` is
repinned for the observer/launcher changes and now also pins the readiness test;
the original manifest is preserved in that preflight directory. No client or
server launch occurred. The next evidence-producing step remains the corrected
CRT3-on experiment 06, only after explicit user authorization to launch.

Run `Launch.ps1` first. Do not move toward the doorway unless the hook log
reports non-overlapping private-memory lifecycle method addresses and the
observer reports `READY`. If discovery remains pending/ambiguous, stop without
crossing. The exact interaction after `READY` is: enter the Masters' Retreat,
walk through the visible green doorway once, stop when blocked or after reaching
`gnarls_new`, do not use abilities, and leave the client open for preservation.

Only after that corrected CRT3-on result is preserved should
`Launch-Crt3Off.ps1` be used for experiment 07.
