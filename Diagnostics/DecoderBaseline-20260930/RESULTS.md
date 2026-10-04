# Bounded decoder session results — 2026-09-30 UTC

## Implementation
- SharpServer/NET/TORGamePacketHandler.cs: shared Read-success gate before Run.
- SharpServer/NET/TORGameClientPacket.cs: rejected-decode log records opcode,
  component (or unavailable for a short header), total length, offset and reason.
- SharpServer/NET/Protocol/PacketCursor.cs: bounded non-throwing reads for LE u32,
  floats, opaque byte blocks, Hero v5 unsigned/signed tokens and explicit end check.
  First failure is sticky. The packet adapter throws only at the existing Read boundary.
- SharpServer/NET/Packets/Client/CMsg61116AD5.cs: decode only full u32 C5 variant,
  four floats and 16 opaque bytes, exactly 44 total bytes, before any gameplay.
- SharpServer/NexusToRServer.csproj: include cursor. Prior dirty additions preserved.
- Diagnostics/Test-PacketDecoder.ps1 and PacketDecoderRegression.cs: x86 harness,
  real-dispatch rejection tests, successful/failed execution contract probe and cursor tests.
- Diagnostics/Fixtures/Movement/{C5-20260929.hex,README.md}: captured regression input.
- Diagnostics/Protocol-Evidence.csv: C5 row now records observed length/opaque tail,
  provenance and conservative acceptance limits; confidence remains Captured.
- Diagnostics/Experiments/INDEX.md and new 2026-09-29-01 run record: pending control.
- This baseline directory: source snapshots, initial dirty status/diff, switches,
  workbench report, build and test logs, isolated build/intermediate outputs and notes.

Only this list was edited/created in the session. Existing diagnostic files, installed
server binaries, hook, startup serializers, RPC parser and PhaseExit were preserved.
No shared RPC envelope or unrelated packet migration was introduced.

## Exact validation outcomes
Build before and after: exit 0, Debug/x86 .NET Framework 4.8, existing warnings.
Tests run in C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe with
-NoProfile -ExecutionPolicy Bypass -File Diagnostics/Test-NAME.ps1
-AssemblyPath <baseline build or after-build>/NexusToRServer.exe.
PacketWorkbench has no AssemblyPath argument.

| Test | Before | After |
| --- | --- | --- |
| AreaRouting | PASS exit 0 | PASS exit 0: 11 routed classes; handles 8/19 |
| AreaBlobFraming | PASS exit 0 | PASS exit 0: 38 byte-exact bodies |
| AreaWireRoundTrip | PASS exit 0 | PASS exit 0: 54 raw-deflate fixture packets |
| WorldEntryOffline | FAIL exit 1 | Same FAIL exit 1: Opt-in RequestWorldFadeIn gate observer is missing. |
| PacketWorkbench | PASS exit 0 | PASS exit 0 |
| PacketDecoder | new test | PASS exit 0 |
| CapturedCharacterRemap | not run separately | PASS exit 0: references CRT2=25, effect1=2, On Enter=3 |
| AreaEnterSignals | not run separately | PASS exit 0: 37-byte rendezvous and 13-byte state bodies |

WorldEntryOffline stops at its source guard. Its later assertions were not reached;
character-remap and enter-signal child tests were run independently on the new build.
No claim that the complete world-entry suite passed. Exact stdout/stderr in Test-*.log
and after-Test-*.log. Initial harness setup failed using Add-Type with an executable
reference; the checked-in harness uses CodeDom and the final run passes.

PacketDecoder covers captured heading/XYZ/body preservation, all 44 shorter prefixes,
C7 and altered high variant byte, wrong opcode, appended byte, actual dispatcher
rejection metadata/no gameplay entry, failed/successful/reused Read/Run contract,
all 256 singleton Hero tokens in both signed/unsigned modes, 1..8-byte magnitudes,
truncated magnitudes, byte order, UInt64 maximum, signed overflow and sticky failure.
Hero support is v5 only. D0 follows PackedStream.Write(long.MinValue) and the existing
Workbench behavior; the local PackedStream signed reader appears to fall through
and overwrite this special value. No claim of native wire verification is made.

Repository-wide git diff --check reports pre-existing whitespace in GeneratedPhaseCandidate
README and earlier server logs. Those files were not rewritten to silence it.

## Established versus unresolved
Established offline: a false Read result cannot reach Run through the handler; observed
C5 bytes decode identically; malformed/unsupported C5 inputs cannot trigger movement,
retry, echo, ack or enter signals through the dispatcher. Existing serializer checks pass.
Strict length/variant rejection is an intentional safety policy, not a claim that all
native movement uses this shape. C7 is known to occur and is now rejected before all
behavior; it previously bypassed OnMove but could reach replies/retry logic.

Unresolved: meanings of the 16-byte tail, unconverted variants, live-client effects of
strict acceptance, native loading-state handler, gnarls_new residency and collision.
No new lifecycle evidence or confidence promotion. Source comments claiming CRT18
is native room streaming remain non-authoritative; see the pending experiment preflight.

## Next single evidence-producing step
Obtain one isolated doorway-control trace with the bounded decoder, no new outbound
message, and independently observed destroy application/loading-state/room residency.
Resolve the existing CRT18 emission confound before calling it a control. The experiment
record is prepared; no live run was performed because native game-control APIs are
unavailable here. The installed server has deliberately not been replaced by this build.
