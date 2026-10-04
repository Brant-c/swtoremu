# Next-session handoff: taxi NPC still unrendered pending one client run

## Status

Run 1 result (unchanged): the Taxis tutorial appeared for the first time and a
minimap marker was visible, but the taxi NPC was not. Do not interpret the
tutorial/minimap as proof of NPC rendering, successful interaction, map opening,
or travel. No successful taxi click is reported. Screenshot:
`taxi-tooltip-no-npc.png`. Run 1 logs: `prelaunch-20261001-130957-581/`.

This session analysed run 1 and changed the NPC record. The awareness *was*
delivered (NexusToR.log 13:06:56, taxi NPC=0x0000001AC7000001) and the client kept
polling afterwards, so delivery is not the fault. Record framing was verified
byte-identical to the captured rendering record, so header/envelope/allocation are
not the fault either. The fault is field content: the captured vendor presents 30
of 96 struct64 fields, the synthesized taxi record presented 18 of 95 and carried
only spnSpawnedSpec, omitting every appearance/identity field.

Run 2 result: still no droid (operator also reported slight added lag, unconfirmed and
plausibly unrelated). Run 3 changes placement only, to the authored taxi pad anchor
(-53.5,-7.7,-125.5) read from the area instance row
`spn.location.tython.taxi.taxi_poi01_jediretreat_pad1.spn_c` = (-535,-1255,-77).
The previous position was a vendor offset 6.3 units west in X and 0.8 units above
the pad level. The instance columns are X=col1/10, Z=col2/10, Y=col3/10, pinned by
med_poi01_masters_retreat matching the captured vendor to 0.19. The minimap marker
comes from the mapnote, so it never implied the NPC was on the pad.

The Jedipedia node extraction in _JPEXTRACT/NPC independently confirmed the two
constants we were already using are correct: `taxTerminalSpec` on
`npc.location.tython.taxi.jediretreat_pad1` is 0xE000DC42A2436F58 and the node's
own id is 0xE0008B8CC0FAEA1D, both already in the generator. It also shows the
authored npcFaction -878620586690540766, which matches the value decoded from the
captured vendor tail.

The taxi objects travel in their own packet, after the captured startup objects.

A delivery-mechanism change was tried and REVERTED: merging the five taxi records
into awareness set 1 - the shared stream carrying the captured vendor and the
authored speeders - broke previously working content, because a rejected appended
object list costs the client the whole set-1 object set, not just the taxi. The
merge bytes were provably well-formed offline, which is exactly the trap: a
well-formed stream is not an accepted one. AreaAwarenessEntered, AreaStartupBundle,
PhaseExit and TythonTaxi are back to committed behavior, and the merge script was
removed with the approach rather than left implying it was still live.

The separate packet is the correct shape for this experiment precisely because it
is additive: worst case is no droid, never a broken world. Do not retry delivery
changes without an isolated test that leaves the shared payload untouched.

The hardcoded position in the caller log is gone: AreaTaxiAwareness now logs its
own fixture SHA256, byte count, placement and all five node IDs, so a run log
always states which fixture it sent.

Run 6 is a spawn-link probe. spnSpawnedComponentClassMethods resolves the chain
GetSpawner() -> spnParentAnchorId -> $SPAWNER.GetSpawnerSpecForNode, and
spnSpawnerSpec is script-side only, so the anchor is the only replicated handle
into it. All four readable set-1 rendering NPCs carry a distinct anchor; ours
carried none, and neither did tmrContainer. Both are now borrowed verbatim from
the vendor (values the client already accepts), so the run tests whether the
spawn link matters rather than inventing a value. Fixture 684 bytes.

Note the correction: struct 62's index 27 is effContainerOther, not the anchor, so
Weller is not evidence about anchors. Also established but NOT the fix:
spnSpawnedEntryAppearance drives apply_appearance inside a Replication_Create,
yet no captured rendering NPC carries it, so creatures don't model through that
path.

If it still shows nothing, the spawn chain is ruled out and the answer is
wholesale cloning of a captured rendering record (struct42, the minimal proven
shape), retargeting only node and position.

## Objective and accepted baseline

Workspace D:\SWTORClassic\swtoremu; Windows, x86 .NET server, April2012 client.
Read AGENTS.md and preserve the dirty workspace. swtoremu2 is read-only reference.
No resets, broad observer work, or automatic client launch. User prefers
Jedipedia script/GOM evidence and existing server/client logs.

User accepts retreat exit/reentry, barrier removal, improved gateway timing,
and Weller cinematic/conversation with normal ending restored. Quest progression
and database persistence remain pending by agreement. Exterior visual models
are not necessarily server-replicated gameplay NPCs. Weller inside the phase
renders correctly with a nameplate; do not confuse him with exterior NPC issues.

Requested next milestone: taxi NPC -> native travel map -> one Retreat/Gnarls
route -> destination enemy NPCs -> basic combat. Flight is not implemented yet.

## Current taxi implementation

Launcher: `Run-SWTORClassic-Taxi.cmd` invokes this directory's `Launch.ps1`.
Single opt-in feature flag `SWTOR_TYTHON_TAXI=1`; working phase/tether/Weller
baseline is retained. New awareness is appended after captured startup objects.
No NPC replacement or new hook was introduced.

- `SharpServer/AreaServer/TythonTaxi.cs`: per-client/selected-player state,
  shared allocator for five nodes; startup awareness then known-terminal update.
  Handles owned taxi target only, area component and complete typed-ID bounds.
  Accepts captured generic NPC right-click SID99EB62D0 or compiled logical
  RequestUseTerminal SID574AFD80. Unknown bounded one-ID selectors are logged
  without response. Clear interaction then open interaction are separate packets.
- `SharpServer/NET/Packets/Server/AreaTaxiAwareness.cs`: embedded669-byte fixture,
  fourteen guarded six-byte identity patches; rejects duplicate/invalid-width
  identities. Existing AreaAwarenessEntered opcodeA1D9E226 and dynamic routing.
- `SharpServer/AreaServer/TaxiNpc.bin`: generated NPC schema66 plus four empty
  linked equipment/effect containers, captured schema13/14 framing. Logical
  resource name `taxi.awareness` embedded by NexusToRServer.csproj.
- `SharpServer/NET/Packets/Server/AreaTaxiInteraction.cs`: schema26 player fields
  42 taxKnownTerminals,51 chrCurrentInteraction,60 chrCurrentInteractionType.
  Player schema has215 fields; flat two-bit state bytes54, style8/version5.
  Known-terminal map count4 means2 entries with merge flag0; ID+Boolean entries.
  Taxi enum3; None enum1. Updates use existing CRT family0D446E80/shared stream.
- `AreaStartupBundle.cs` calls Initialize at startup end. `CMsgF96DCDB0.cs`
  calls taxi Handle before Weller Handle so taxi right-click is not rejected by
  Weller's owner guard. All behavior is excluded when the taxi flag is off.

## Highest-value next checks

Analyze saved logs first: identify TythonTaxi startup marker, actual fresh NPC
ID, creation/replication/appearance failures and tutorial timing. Compare the
spawned compatibility position to where the user stood; do not assume the
minimap's authored taxi icon points at this newly placed runtime NPC.

The fixture deliberately uses a COMPATIBILITY placement
(-59.787200927734375,-6.899799823760986,-125.8347930908203), 2.5Z from captured
vendor(-59.7872,-6.8998,-128.3348). It is NOT the taxi platform's recovered
authored position. Establish position/ground elevation before blaming appearance.

If placement is correct, compare missing taxi appearance/replication fields with
a captured visible NPC and the April taxi prototype. NPC template is
E0008B8CC0FAEA1D (`npc.location.tython.taxi.jediretreat_pad1`). Gloms from
captured schema66 are aiCharacterAgentOverrideComponent, spnSpawnedComponent,
brkOwnerComponent, taxTerminalComponent. Fixture's flags7A specify template,
captured parent1AC688BE1E, metadata and create values. No explicit base class
is sent (same shape as donor vendor). Prototype/glom application is a hypothesis.

Fixture only sends reliable common fields: position/rotation, scale/melee,
weapon state, phsPhase1 copied from captured exterior donor, equipment/effect
refs, taxi terminal spec, captured stat maps/health defaults, toughness/snare,
spnSpawnedSpec, and provisional targetable Boolean state. It OMITs runtime
appearance fields, spnParentAnchorId, timer/ability refs, NPC level and later
fields because old decoder did not fully round-trip the donor. This omission is
a candidate rendering cause, not established. Health460/stat maps are donor
compatibility defaults, not actual taxi stats. Inherited taxi prototype visual
fields have not been verified in the native client.

Do NOT blindly copy vendor appearance: it would create the wrong model. Use
April NPC prototype's actual protocol-droid appearance data and client scripts.
The Inspect-Awareness diagnostic still shows incomplete donor decoding; enum
values must be packed (e.g232/233), signed values use signed packed tokens,
and top-level Boolean states have special handling. Generic Generate-CrtValues
has known limitations; do not treat a partial read as a correct whole NPC decode.

After NPC can render/click, attribute actual live use/route selectors from logs
and check map acceptance. No confirmed route request yet. Avoid travel success
replies or invented destination coordinates until path/vehicle lifecycle is known.

## Jedipedia and content evidence already gathered

Read `AUDIT.md`, `taxi-content.txt`, `fixture.json`, `Generate-Taxi.py` first.
Existing user's reader remains at https://swtor.jedipedia.net/reader with April
archives loaded; do NOT reload and lose them. Use cua_repl, restore documentation
after compaction and rebind existing browser2/tab1 if needed. Native app controls
are disabled. File tree is canvas; decimal script ID search produces an async
filtered row that can be clicked after fresh screenshot. Read rendered main text.

Scripts:
-14988178523977114911 taxTerminalComponentClassMethods: replication registration,
  UpdateTerminalIndicator, UseTerminal eligibility/proximity, taxi use call.
-14988151862778083528 guiApiGfxTaxiClassMethods: map/known destinations/graph;
  cmdTakeTaxiRoute passes source spec,destination spec,not launchedFromHydra.
-14988055391397265151 chrOracleClassMethods: native RequestUseTerminal
  offsets4850/4858 RPCBegin(SID574AFD80,domain8E3C86ED), NPC-ID serializer;
  RequestTakeTaxi offsets4900/4908 SIDC7DBF85E/domain8E3C86ED thenID,ID,Boolean.
  These are logical compiled IDs. Live captured domain is1279C371; selector
  translation can differ. Do not claim all compiled IDs are live wire IDs.
- `_JPEXTRACT/playercharacterclassmethods.txt` updateInteraction opens taxi GUI
  from fields51/60 when target has taxTerminalComponent.

Terminal Retreat E000DC42A2436F58, Gnarls E0009C95E5C2E162. Route reversed
pth.location.tython.mob.taxi.poi_gnarls1_to_poi_retreat1 E000436FBD8E6AA8;
arrival pth.location.tython.mob.taxi.arrival_taxi_poi_gnarls1_from_poi_retreat1
E000C51EAD34A3AE. Bucket path prototypes lack coordinates; authored paths and
actual spawn anchors must be extracted elsewhere. LegacyHero prototype glom IDs
printed by Inspect-TaxiContent are unreliable; captured compact-schema IDs are
the metadata reference. Variable field IDs/values and terminal route links read.

## Tests/configuration/evidence

Before run: server build, Test-Taxi.ps1 and independent Verify-Taxi.py pass for
areas8/19. Existing routing,38 captured bodies,54 transport fixtures, Weller
and PacketWorkbench checks pass. Test-WorldEntryOffline has the same preexisting
missing RequestWorldFadeIn observer source check before/after; no hooks changed.
Offline tests do not establish taxi rendering/map behavior.

Taxi and Weller VerifyOnly both passed with nonempty pinned identity manifests.
Earlier Weller identity.csv had been empty; it was populated this turn. Current
manifests pin server/hook/archive/fixtures/source/launcher/AUDIT/experiment.
After a source/build or pinned-document change, intentionally regenerate the
manifest and VerifyOnly before telling user to run; do not bypass hash failures.
RetreatGateway historical launcher retains old hashes; use current Taxi/Weller.

Experiment `Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md`:
operator result now tutorial appeared but NPC invisible; rendering acceptance
failed, map/travel untested. This latest handoff records the result without
changing pinned experiment/AUDIT files or repinning the existing launcher.
Registry rows taxi awareness/map remain Hypothesis. Weller teardown promoted
Behavior-verified, evidence `WellerStory-20261001/RESULTS-END.md` and saved run
prelaunch-20261001-122710-944 (start12:12:22/end12:13:58 SID70C14D2A). Cancellation
and reopening not separately operator-confirmed; no quest state committed.

## Tool paths / practical pitfalls

Python C:\Users\brant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
MSBuild C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe
Build project SharpServer\NexusToRServer.csproj /p:Configuration=Debug /p:Platform=x86.
Tests loading server need C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
-NoProfile -ExecutionPolicy Bypass. Existing general tests accept -AssemblyPath.
New-ProtocolExperiment.ps1 runs under current PowerShell7; WinPS5.1 misreads its
UTF8-noBOM punctuation. Preserve logs before launches. No extra observers needed
to capture CMsgF96DCDB0; existing server poll log writes complete bodies.
Git ownership: use command-scoped -c safe.directory=D:/SWTORClassic/swtoremu;
do not change global Git config. Dirty preexisting work is extensive.

Keep progress updates short and explain concrete findings. User explicitly asked
to stop investigation now for usage conservation; resume only in next session.
