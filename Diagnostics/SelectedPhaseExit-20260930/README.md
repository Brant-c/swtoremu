# Selected-player phase exit, experiment12

Ready for a fresh manual run using `Run-SWTORClassic-SelectedPhaseExit.cmd`.
The agent has not launched the client or servers. Load Tython and stand still;
report loaded before approaching the doorway. First verify that the client hook
contains `PhaseUpdateHook: installed discovery=relative-gui-anchor-and-executing-call`.
An ERROR or missing installed marker means do not approach yet.

The only gameplay change from experiment11 is correcting the generated player
field update to use ActiveCharacter._id, matching startup replication. New
observers are passive and opt-in via SWTOR_TRACE_PHASE_UPDATE=1. They forward
existing calls and never change fields, collision, requests, or results.

## What this run can decide

Correlate server target ID and crossing timestamp with these client checkpoints:

- `phase-field-matched`: the script encountered the actual phsPhase changed ID.
- `local-player-comparison-passed`: this handler belongs to the local player.
- `PHASE.OnPhasedInstanceUpdated` entry and return.
- `new-instance-resolved` with newInstanceNameID=0, followed by instance-changed.
- `old-instance-exit-call-follows` and then old-instance-exit-branch-complete:
  together show the old instance's exit call returned. The latter by itself can
  occur when the old instance was invalid and its exit call was skipped.
- `exit-branch-new-instance-invalid` and exit-gateway-gui-branch-complete.
- `player-phase-info-invalid`: the player subsequently resolves no phase info.

Existing CRT apply, phase-info destruction, room selection/activation and trigger
collision observers remain available. Report whether the story-area banner
disappears and whether walking through the doorway succeeds. Stop at the wall
or outside and leave the client open for a bounded log capture. No repeated
attempts or abilities. Capture tails, not full logs or memory dumps.

If local phase exit completes but movement remains blocked, investigate physical
character-room/contact association next. If local-player/phase callback evidence
is missing, do not label the membership change a valid negative result.

## Observer verification and limits

The pinned April oracle has section0 base0xC83 in its decrypted payload.
Section1940/payload25C3 is OnPhasedInstanceUpdated; section2660/payload32E3 is
SendCurrentPhaseInfoToGUI. The old observer called the latter UpdateGateway;
that label and its one-argument ABI are corrected. The real UpdateGateway is
section32C0/payload3F43 and is not directly hooked here. Earlier "no nested
gateway" conclusions from the mislabeled observer are invalid.

The new oracle entry is resolved 0x720 bytes before the existing verified GUI
anchor; its prefix, epilogue and relocated TrackLine target must match. Native
HM.TrackLine at static005D20A0 is pinned by its exact entry bytes and two loaded
script relocations. phsEntity is identified only from an executing TrackLine call
with its verified prefix, phase-field comparison and epilogue. No additional
address-space discovery scan is performed. Checkpoint logging caps at128 events;
oracle entry/return logging caps at32 calls. Existing older discovery remains
unchanged. The phsEntity arguments are Me, 64-bit replication argument and list;
fixed generated ESP offsets60/64/68/6C are verified against its assembly.

No arbitrary NodeRef memory words are interpreted as character IDs. New instance
name ID is read from the verified oracle local slots78/7C after initialization;
branch markers establish validity checks. These are passive observations of the
existing path, not independently invoked engine functions.

Build and script/native-prefix verification pass. Selected-ID integration checks
startup CRT2/CRT4 and exit agree for actual and alternate IDs, both area handles,
only field25 supplied, zero target rejected and default destroy byte-identical.
Server routing/blob/wire/workbench checks passed after the identity fix; the
existing WorldEntryOffline missing RequestWorldFadeIn observer failure remains.
New native observers still require live installed/callback verification.

Launcher pins are in identity.csv. VerifyOnly passed with CLEAR_FIELD=1,
TRACE_PHASE_UPDATE=1, CRT3=0, lifecycle log-only=1, retry disabled and existing
room/trigger observers. Base verbose launcher is unchanged. Old launchers retain
old pins and reject the corrected binaries.


Experiment13 prepared: passive callback address corrected from GUI minus720 to minusD20, derived from pinned payload32E3/25C3. Address/relocation regression and Win32 build pass. Per-condition validation added; optional failure no longer suppresses old lifecycle observers. No packet change. Runtime pending. Use selected launcher, load and stand still to verify installed/startup callback coverage before doorway attempt. See experiment13 record.


2026-09-30 correction: native style7 class field states are ONE bit per field; style8 TWO bits. Previous shared two-bit decoder invalidates style7 field-selection reports. Explicit style support and main/dump callers corrected. Old phase-clear style7 mask selected51 chrCurrentInteraction, not25 phsPhase. Serializer now style8, one-byte change only, opt-in. Experiment14 prepared; native regression and relevant packet tests pass, existing fade-in observer offline failure remains. Live outcome pending. See Diagnostics/PhaseFormat-20260930/FINDING.md.


Experiment14 result:22:21:51 corrected phase field recognized for local player; PHASE resolves no current instance, executes exit and gateway/UI branches, returns. Operator UI confirms leaving phase; invisible barrier persists. Phase-state portion behavior-verified, traversal failed. Evidence PhaseFormat-20260930/live-20260930-222139/RESULTS.md. Client closed. Next collision/contact/controller/room boundary evidence, not another phase-clear/observer repeat. Retain opt-in.
