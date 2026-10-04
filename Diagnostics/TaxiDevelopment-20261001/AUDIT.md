# Tython taxi development checkpoint

The user accepted Weller's cinematic/conversation and restored camera/input.
Quest progression and persistent storage remain pending. The next requested
milestone is a functional taxi route to enemies, followed by NPC/combat work.

## Implemented, awaiting client acceptance

Opt-in `SWTOR_TYTHON_TAXI=1` appends a fresh taxi NPC and four empty equipment /
effect containers after existing startup awareness. No existing NPC is replaced.
Shared runtime allocator gives every object a new identity. Creation uses the
captured AreaAwarenessEntered family, existing compact structure66, April taxi
prototype `npc.location.tython.taxi.jediretreat_pad1`, and terminal
`tax.tython.poi_jedi_retreat_pathone`. Membership/UI/Weller baseline is retained.

The NPC now stands at the authored anchor (-53.5,-7.7,-125.5), read from the
area instance row `spn.location.tython.taxi.taxi_poi01_jediretreat_pad1.spn_c`
= (-535,-1255,-77). That dump stores integers with X = col1/10, Z = col2/10,
Y = col3/10; the mapping is pinned by `med_poi01_masters_retreat.spn_c`
(-597,-1285,-69) -> (-59.7,-6.9,-128.5), which matches the captured exterior vendor
at (-59.787,-6.8998,-128.335) to 0.19. The pad mapnote is at (-53.6,-7.7,-125.9)
and the two authored air speeders at (-52.9,-7.7,-125.3) and (-53.9,-7.7,-125.1).

The earlier placement (-59.7872,-6.8998,-125.8348) was a vendor offset, not a taxi
anchor: it sat 6.3 units west in X and 0.8 units above the pad level, inside the
retreat NPC cluster. The minimap marker comes from the mapnote, not from this NPC,
so its being in view never placed the NPC there. Health/stat maps are still bounded
captured vendor defaults, not established taxi stats. Generated NPC targetability
Boolean state is provisional. Empty container records round-trip the captured
containers and omit the copied effect.

Appearance/identity fields are now carried. The first run rendered no droid
(tutorial and minimap marker only) even though the awareness was delivered and
the client kept polling. The framing was then verified byte-identical to the
captured record, so header/envelope/allocation were not at fault. The real
difference was field content: the captured rendering vendor 0x1AC68957EB presents
30 of 96 struct64 fields, while the synthesized taxi record presented 18 of 95
and omitted every appearance/identity field, keeping only spnSpawnedSpec. Per
Jedipedia, chrCharacter puts `_characterSpecification` on `visible_character`.

The record therefore now also carries the vendor's captured tail: its last 57
body bytes, in field order, occupying schema66 slots 62,63,66,68,69,76,77,79,85
(chrCreatureTypeList, cbtFaction, chrTemplateVisualIndex, cbtCreatureType,
brkResourceName, chrClass, _characterSpecification, ablContainer, chrLevel).
struct66 drops struct64 index 69 vndVendorIconOnExtraMaps, so indices >=70 shift
by one. The block is transplanted verbatim rather than re-derived, because the
local tail decoder cannot split it per field without guessing (0xC0-0xC7 are
valid signed packed tokens, and enum values >=0xC0 are legal raw bytes). Fixture
612 -> 669 bytes. Whether the client now renders a model is still a Hypothesis.

Player schema26 updates unlock the two terminal specs for the session (map field42).
Interaction fields51 and60 point at the taxi with `chrInteractionTypeTaxi=3`.
The service accepts the captured generic right-click SID99EB62D0 when its sole
typed ID is this session's taxi. It also recognizes the compiled logical
RequestUseTerminal SID574AFD80; its live wire attribution remains unverified.
Other bounded one-ID requests to the taxi are logged without gameplay response.
No unknown selector is used to trigger a map or travel.

## Jedipedia / April findings

Reader: https://swtor.jedipedia.net/reader; matching April systemgenerated archive.
Script IDs and useful methods:

- `14988178523977114911` taxTerminalComponentClassMethods: Replication_Create,
  UpdateTerminalIndicator, UseTerminal, ValidateTaxiInteractionProximity.
  UseTerminal rejects dead/in-combat/too-distant NPC/player and conversations;
  then calls `$CHARACTER.RequestUseTerminal(Me)`.
- `14988151862778083528` guiApiGfxTaxiClassMethods: showTaxiMap,
  generateTaxiNetwork, cmdTakeTaxiRoute. Only known terminal specs enter the
  route graph; mapnotes provide terminal metadata, localized names and positions.
  cmdTakeTaxiRoute calls RequestTakeTaxi(source terminal spec,destination spec,
  not launchedFromHydra), then sets waiting flag.
- `14988055391397265151` chrOracleClassMethods: RequestUseTerminal assembly
  offsets4850/4858 has RPCBegin(logical SID574AFD80, domain8E3C86ED), serializes
  NPC NodeRef ID and sends client-to-server. RequestTakeTaxi offsets4900/4908
  has logical SIDC7DBF85E, same domain, then ID, ID, Boolean serializers.
  Compiled logical domain differs from captured live untrusted domain1279C371;
  do not assume compiled selectors directly establish all live wire selectors.
- Extracted playercharacterclassmethods updateInteraction calls showTaxiMap
  when replicated interaction points to taxTerminalComponent and type is Taxi.
- April GOM chrInteractionType enum is None1, Conversation2, Taxi3, Vendor4.

`taxi-content.txt` preserves prototype/route data. Retreat terminal
E000DC42A2436F58 links to Gnarls E0009C95E5C2E162 with reversed path
`pth.location.tython.mob.taxi.poi_gnarls1_to_poi_retreat1` (E000436FBD8E6AA8)
and arrival path E000C51EAD34A3AE. Bucket path prototypes omit positions;
actual authored waypoints/arrival anchor still need extraction. No invented
arrival position or successful-travel response has been implemented.

## Verification and next run

Build, taxi packet checks/independent bounded decoding, Weller tests, routing,
all38 captured bodies, all54 transport fixtures and PacketWorkbench pass.
Test-WorldEntryOffline has the same pre-existing missing RequestWorldFadeIn
observer source check before and after this change; no hook change was made.

Launcher configuration verified without launching processes. After the fixture,
packet and source change the pinned manifest was intentionally regenerated with
`Update-Identity.ps1` (membership and order preserved, only Bytes/SHA256
recomputed; 8 of 91 inputs refreshed), and `Launch.ps1 -VerifyOnly` passes. No
client was launched by the agent.

Run Run-SWTORClassic-Taxi.cmd, leave retreat, and look for a new droid near the
exit where the marker is. This run's only change from the last is the appearance
field set, so the decision is narrow: if a droid appears, the field set is
behavior-verified and the next step is the use/route decoder; if still nothing,
stop synthesizing and clone the vendor's whole struct64 record instead. Right-click
once only if a droid is visible. If the map opens, select Gnarls once, report the
visible result, then close. Flight will not occur yet. Server logs already record
complete CMsgF96DCDB0 bodies; additional observer tooling is unnecessary here.

## Remaining work after acceptance

1. Verify NPC appearance/nameplate/targetability and travel map; attribute actual
   use/route selectors from this run, correcting only demonstrated differences.
2. Extract authored Retreat and Gnarls anchors/waypoints and audit native taxi
   lifecycle, controlled vehicle, movement/path replication and arrival cleanup.
3. Implement strict two-ID/Boolean route decoder, source/destination/proximity
   validation and session travel state, then one real route and return path.
4. Replicate destination's gameplay NPCs; visual scenery alone is not an NPC.
   Then pursue the requested basic combat milestone. Full persistence stays later.
