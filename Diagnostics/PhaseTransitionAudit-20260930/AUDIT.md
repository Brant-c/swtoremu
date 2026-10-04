# Seamless retreat exit audit — September 30, 2026

The most recent experiment targeted the captured character rather than the
selected character. This is an implementation error, not evidence that clearing
the normal player phase link fails. The correction is implemented and verified
offline. No new run is authorized by this document.

## Identity and replication

`CapturedCharacterRemap.CapturedCharacterID` is `0x4000010E218A839C`.
`AreaStartupBundle` obtains `client.ActiveCharacter._id`, uses it in
`AreaSetCharacter` and teleport, and passes it to every startup CRT constructor.
`AreaClientReplicationTransaction` remaps fixture references to that selected ID.
The completed run's server placed-ID and client ReadinessVmHook agree on
`0x4000010E218A839B`. These are not established separate root/component identities:
the source explicitly translates the captured identity into the selected one.

Experiment11's generated field record bypassed that translation and supplied
`839C`. Its received/applied CRT and destroy callbacks therefore cannot establish
an update of the selected player's field. The `phsEntity` handler additionally
requires `Me == GetPlayerCharacterNode()` before invoking the local phase lifecycle.
Do not label experiment11 a valid negative test of that lifecycle.

Correction: `PhaseExit` passes `ActiveCharacter._id` into the generated packet;
the packet requires a nonzero ID when field clearing is enabled, serializes that
ID directly, and logs it. The destroy-only control remains byte-identical.
`Test-SelectedPhase.ps1` and `Verify-SelectedPhase.py` verify that startup CRT2
creation, CRT4 phase link and exit update all address the same selected character,
for the actual B identity and an alternate character, with destination handles
8 and19. CRT4 links that player to phase-info `0x1AC6F6DC1F`; only field25 is
supplied by the generated exit update, with packed UInt64 zero. All other fields
are absent; removal and full packet end are validated. Reports and raw packets
are local to this directory. Original experiment source/binary and live evidence
are preserved separately.

## End-to-end paths and remaining gaps

| Stage | Existing behavior and evidence | Gap or implication |
|---|---|---|
| Character placement | ActiveCharacter ID drives SetCharacter, teleport, startup remapping; saved live log agrees | New field update previously violated this identity; corrected offline |
| Story membership | CRT4 structure26/index25 `phsPhase` references phase-info node; phase-info parent is retreat instance | Node destroy alone is a distinct input from changing the player's reference |
| Normal local phase change | Reader `phsEntityClassMethods`14988219368268985980: Replication_Update checks field40000002641F28CC and local-player equality, calls PHASE.OnPhasedInstanceUpdated | Specific handler execution and field application were not observed in experiment11 |
| Phase callbacks | phsOracle170 onward resolves old/current instances, calls OnInstanceChanged and old.OnPlayerExitedInstance, updates current name ID, then entry/exit UI/gateway branches | Runtime old/new nodes and branch execution still need confirmation |
| Gateway | phsGateway.TriggerEnter resolves instance; phsOracle UpdateGateway evaluates eligibility; SetGatewayState updates FX and cached type3 triggers' Collidable property | Not a proven native room stream or area-transfer request; TriggerLeave unknown output is not proof of no behavior |
| Doorway detection in emulator | Active PhaseExit watches C5/C7 movement and sends one destroy transaction; optional field clear now uses selected ID | Crossing threshold is temporary; production trigger/server exit sequence is uncaptured |
| Room selection | Live native register maps F4F29500=gnarls_new, D30FA280=gnarls_retreat_int_c, D30FA500=gnarls_retreat_int_d; room selection and activation return observed | Area selection/activation does not prove character physics attachment or collision/content readiness |
| Physical movement | Five measured story trigger collision bits were clear; offline authored shell tests did not intersect approach; ray query code has shape-specific filtering | Other blockers, capsule/sweep and active character collision association remain unresolved |
| Planet-instance switch | trvTravelComponent.RequestInstanceTransfer chooses numbered available planet copy, prompts, calls GSSOnRequestInstanceTransfer; rejects story membership | Different path; no evidence that ordinary doorway requires this RPC |

This map distinguishes logical story membership, area room selection and physical
movement. Clearing membership is a supported script input; neither the correction
nor a returned activation routine proves the complete seamless transition.

## Legacy implementation comparison

Active swtoremu: SharpServer AreaStartupBundle replays/remaps startup fixtures,
uses dynamic area routing and has the temporary PhaseExit movement detector.
Packets/MessageHeaders/base_gom_update.h describes update/removal framing; it
does not prescribe phase-exit semantics. Generated updates need the same identity
contract as fixture updates. Symbol adjacency in compiled scripts likewise does
not prescribe lifecycle call order.

swtoremu2, inspected read-only: SelectCharacterRequest emits WorldSendToArea
during initial selection; ObjectReply replays CRT1..17 and sends AreaSetCharacter
twice. AreaModulesList.RunImplementation is empty. TORGamePacketHandler's IN_GAME
branch handles close/tracking/ping and explicitly says TODO implement game packets.
Bounded named searches found no completed phase-exit or join-phase handler in
that tree. This supports an unfinished game lifecycle in the inspected source;
it does not establish that every unnamed opcode or asset has been decoded.

## Evidence required before another run

Do not repeat an isolated destroy, CRT3, gateway-collision or guessed travel test.
A useful next run should correlate, on the SAME selected identity:

1. Startup ID, pre-exit phsPhase reference and target ID of the generated update.
2. phsEntity Replication_Update entry/return, changed-field ID and local-player
   comparison; PHASE.OnPhasedInstanceUpdated entry/return and old/new phase state.
3. Phase-info destruction and native selected room/activation, using existing
   bounded observers, plus the operator's banner and outside movement result.

Only instrument named verified script entries/events and already known objects;
no broad memory scans, full dumps, manual collision removal or native calls with
unverified ABI. Current hook observes destroy and room paths but does not provide
items1/2. A corrected-ID rerun alone would still leave a callback ambiguity, so
no launcher has been repinned or new client run requested yet. If phase callbacks
complete and the wall remains, the next branch is physical character-room/contact
association, not another membership guess.

## Validation

Debug x86 build succeeds with existing warnings. Selected-ID integration and
default packet hash controls pass. Post-change area routing, blob framing,
wire round-trip and packet workbench pass. WorldEntryOffline has the same missing
RequestWorldFadeIn observer failure as before. Offline checks prove serialization
and source integration, not native callback execution or a playable exit.

The old experiment launcher retains its previous binary pin and will reject
this corrected build. The client should stay closed until the combined evidence
collection is ready.

## Subsequent preparation completed

The combined collection is now ready as experiment12; see
`Diagnostics/SelectedPhaseExit-20260930/README.md`. This supersedes the earlier
keep-closed preparation status. The client/server remain unlaunched by the agent;
the new manual launcher is Run-SWTORClassic-SelectedPhaseExit.cmd. Live hook
installation must be checked while standing still before approaching.

Further symbol verification found the historical oracle "UpdateGateway" hook
was SendCurrentPhaseInfoToGUI, section2660/payload32E3. Its label and one-Me
argument ABI are corrected. Previous absence of that observer cannot establish
absence of gateway refresh. The new actual OnPhasedInstanceUpdated callback at
section1940 is verified from this same module; passive TrackLine checkpoints
observe the phsEntity field/local-player gates and the oracle exit branches.
No new address-space scan or engine invocation. New bounds128 checkpoints/
32callback calls, exact prefixes and native helper verification are documented
in callback-prefixes.json and Prepare-CallbackPrefixes.py.
