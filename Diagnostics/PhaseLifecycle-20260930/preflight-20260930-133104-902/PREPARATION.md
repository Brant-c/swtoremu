# Phase lifecycle preparation — 2026-09-30

## Status

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

Run `Launch.ps1` first. Do not move toward the doorway unless the hook log
reports non-overlapping private-memory lifecycle method addresses and the
observer reports `READY`. If discovery remains pending/ambiguous, stop without
crossing. The exact interaction after `READY` is: enter the Masters' Retreat,
walk through the visible green doorway once, stop when blocked or after reaching
`gnarls_new`, do not use abilities, and leave the client open for preservation.

Only after that corrected CRT3-on result is preserved should
`Launch-Crt3Off.ps1` be used for experiment 07.
