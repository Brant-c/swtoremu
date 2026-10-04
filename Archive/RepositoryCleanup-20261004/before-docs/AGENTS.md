# SWTORClassic development instructions

## Active objective and reading order

Start with `Diagnostics/CURRENT-PICKUP.md`, then
`Diagnostics/Foundation-Audit-20261004.md` and
`Diagnostics/Protocol-Evidence-Registry.md`.

The active goal is to resolve character-load and phasing foundations before
extending taxi behavior. First audit the player-update encoding. Preserve the
accepted local entry/movement/retreat exit-and-reentry baseline while identifying
and replacing unsupported compatibility workarounds. Do not resume superseded
invisible-wall or taxi-travel plans by default.

CURRENT-PICKUP is the single active checkpoint; update it in place. Dated
handoffs/plans/audits/results supply evidence only, not current instructions.
See `Diagnostics/Documentation-Status.md` for corrections and archive locations.

## Established findings

- World entry renders and the character can move using compatibility settings.
- Snapshot replay, forced mobility/loaded state, a client loading-confirmation
  patch, moving tether anchor, and captured phase identities remain workarounds.
- Local retreat exit/reentry and improved gateway timing were accepted later
  than the September wall experiments. General phase/area lifecycle is unresolved.
- Weller rendering/nameplate/quest indicator predate conversation work.
- Exterior models, including the medcenter, do not establish targetability/use.
- Taxi remains absent; tutorial/minimap do not establish creation or interaction.
- Phase membership is created early enough for the story-area UI and ownership.
- `CMsg61116AD5` carries an observed movement variant used by the temporary
  doorway-crossing detector.
- Destroy-only phase-info removal did not remove the wall in earlier runs;
  later tether-refresh and membership work established local traversal/reentry.
- Awareness and CRT fixtures are creation/replication data, not proven native
  room streams. Re-sending them can create duplicates.
- `_Room_Activate` is server-only and is not a client RPC.
- Experiment08 selected `gnarls_new` and ran activation while its wall persisted.
  This is historical evidence, not the current objective. Missing streaming was
  never established as the cause; consult its dated results only when relevant.

## Claims that are not established

- `AssetCreated` or `InstanceCreated` is the missing "notify area" message.
- `SMSG_SEND_TO_AREA` is the missing phase-exit message.
- CRT18 is a captured or valid native room stream.
- A known opcode implies that its body shape or lifecycle role is known.

Do not make these default runtime behavior without new evidence.

## Evidence policy

Label protocol claims with exactly one primary confidence level:

- `Captured`: byte shape observed in a known capture.
- `Client-derived`: read/write order recovered from the April native client.
- `Behavior-verified`: produced the predicted result in the April client.
- `Hypothesis`: plausible but not established.

Record every protocol claim in `Diagnostics/Protocol-Evidence.csv`. Do not use
source comments or chronological handoffs as the only registry.

Evidence priority:

1. Production capture with known behavior.
2. April native client send/receive-handler disassembly.
3. `Server/Framework/Src/Network/Packet.h`, preferably confirmed against the
   client dispatcher.
4. Extracted scripts, GOM data, and area assets for semantics.
5. Hypothesis.

## Experiment policy

Use `Diagnostics/New-ProtocolExperiment.ps1` to create a run record from
`Diagnostics/Experiments/TEMPLATE.md`. Change one protocol variable per client
run. Record the exact bytes, expected positive and negative observations, and
deciding logs before the run. Preserve results in
`Diagnostics/Experiments/INDEX.md`.

A lack of response is evidence only when delivery and relevant handler
execution were independently confirmed.

Experimental behavior must be opt-in, visibly logged, and excluded from the
default startup path until behavior-verified.

## Packet work rules

- Use `Diagnostics/PacketWorkbench.ps1` for plaintext packets and binary
  fixtures before writing a one-off decoder.
- Use `Tools/PacketAnalyser` for its existing capture/decryption workflow. It is
  a legacy GUI and is not the protocol schema source.
- Use `Tools/Hero/Hero/PackedStream.cs` as the local reference for Hero packed
  value tokens and transport-version behavior.
- Use `Tools/SCPTExtractor` and `_JPEXTRACT` for script semantics.
- Use `Tools/tor_tools` or `D:\SWTORClassic\extracTOR` for archive/content work.
- `D:\SWTORClassic\assettest\resources` is extracted content, not a native
  network-client decompilation.
- `D:\SWTORClassic\swtoremu2\Tools` is a comparison/reference tree. Do not edit
  it unless the task explicitly targets that tree.

For inbound decoders, validate bounds and the end of the expected message.
Never execute gameplay behavior after a failed decode. Keep raw framing,
message decoding, and gameplay behavior separate.

## Baseline verification

Before and after protocol changes, run the applicable existing checks:

- `Diagnostics/Test-AreaRouting.ps1`
- `Diagnostics/Test-AreaBlobFraming.ps1`
- `Diagnostics/Test-AreaWireRoundTrip.ps1`
- `Diagnostics/Test-WorldEntryOffline.ps1`
- `Diagnostics/Test-PacketWorkbench.ps1`

Some server tests require 32-bit PowerShell and a prepared assembly path; read
their parameters before running them. Offline success does not prove native
client acceptance.

## Scope discipline

- Preserve the dirty worktree and existing diagnostic evidence.
- Do not reset or delete prior-agent files to make the tree clean.
- Do not migrate unrelated login, repository, character, or mail packets while
  working on phase exit.
- Keep `PhaseExit` as a temporary crossing detector. New room lifecycle and
  stream ordering belong in a separate room-transition service once proven.

