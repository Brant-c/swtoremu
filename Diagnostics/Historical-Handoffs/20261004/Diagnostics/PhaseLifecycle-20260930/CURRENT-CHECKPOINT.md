# Current checkpoint — 2026-09-30 Toronto

Read this first after compaction. Project: `D:\SWTORClassic\swtoremu`.
Goal: leave the Masters' Retreat through its visible green exit, enter
`gnarls_new`, and continue moving. The wall is still present. Preserve the dirty
worktree and all prior evidence; do not clean/reset or add guessed packets.

## User constraints

- Keep responses brief and make progress concrete. The user was frustrated by
  repeated preparation launches and lengthy observer tooling.
- Use server and named client-hook logs for this comparison. No external
  full-memory scans, dumps or additional observer process. Do not make broad
  lookup/global-state/node-removal claims from these logs.
- The user asked about launcher verbosity out of curiosity and asked not to
  refactor it. Only the necessary CRT3-off comparison wrapper/configuration was
  aligned; do not do unrelated cleanup.
- The user launches the game on the desktop; advise exactly which file and
  wait for loading feedback. Sandbox launches created invisible isolated
  windows earlier. Do not auto-launch another copy or repeatedly restart.
- No abilities during runs; one doorway crossing per run, then stop. Preserve
  the logs before requesting another experiment.

## Preserved valid CRT3-on baseline

`live-20260930-145102-logonly/RESULTS.md` is authoritative for the completed
log-only baseline. Fresh launch 14:51:02; CRT3 emitted at 14:54:31 and named
player-phase-data create callback entered/returned. All four native method
hooks installed at 14:54:31. Accepted C5 crossed `-64.87 -> -62.98` at 14:57:26.
The exact 46-byte destroy, stream `0x001B502E`, node `0x1AC6F6DC1F`, has SHA-256
`2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`.
Generic apply 18 brackets named phase-info destroy entry and return. No nested
gateway update was recorded. CRT18 suppressed. Operator: `stopped, stuck on wall`.
No player-phase-data destroy entry recorded; no global read-back performed.
Server logs alone cannot prove client callback execution. Both decisive logs
are preserved, with binary/hash evidence and narrow crossing extracts.

Full saved text logs:
`../DoorwayControl-20260930/phase-lifecycle-logonly-blocked-20260930-145754-227/`.
Protocol-Evidence.csv now has a separate narrow Behavior-verified
`PhaseInfoDestroyNamedCallback` row. The general replication row remains
Captured. Experiment 06 and its index reflect this valid result and preserve
the earlier invalid attempts separately.

## Established instrumentation repairs

- The old hook self-matched its DLL constants. It now scans executable
  MEM_PRIVATE only, over the entire 32-bit range (actual script code is above
  2 GB), with 54/56-byte pinned prefixes masking only external CALL operands.
- Native matcher tests: 220 byte mutations, four intended captured candidates
  accepted, seven unrelated short-prefix candidates rejected. Resource/prefix
  checks and the 12-invalid-baseline readiness regression passed. Release x86
  hook build passed. Do not rework this while the valid hooks already work.
- Log-only launch disables full CRT hex, RPC/loading/player-field tracing.
  Event-dispatch tracing remains on because current hook CRT discovery depends
  on that gate. Do not turn it off without a reason.
- Server logs only the exact small destroy packet under log-only mode; packet
  bodies/order unchanged. Debug x86 launch-path server build and AreaRouting,
  AreaBlobFraming (38 bodies), AreaWireRoundTrip (54 packets) passed.
- WorldEntryOffline's existing first failure remains `Opt-in RequestWorldFadeIn
  gate observer is missing.` Later assertions were not reached; do not present
  a full world-entry test pass.
- Earlier 14:21 attempt had CRT3 suppressed and is not the CRT3-on baseline.
  Its named hooks installed but no player-phase-data HeroNode was found. Do
  not merge it with the valid 14:51 baseline.

## Current verified CRT3-off preparation

The next single variable is CRT3=0. The user requested notice when ready and
this checkpoint before compaction. No new live ablation has been launched by
the assistant. The desktop entry point is:
`D:\SWTORClassic\swtoremu\Run-SWTORClassic-PhaseLifecycle-Crt3Off.cmd`.
It invokes Launch-Crt3Off.ps1, which delegates to the same Launch.ps1 as baseline
with `-Crt3Off`. Log-only profile, packet policies, fixtures and binaries are
shared. No external observer is started.

Both launch paths passed `-VerifyOnly` without starting anything. The actual
batch environment was compared: all 28 SWTOR settings match except
`SWTOR_ENABLE_UNVERIFIED_CRT3=1` versus `0`. Exact outputs and source/manifest
backups are in `crt3-off-preparation-20260930-150532-698/`.
`identity.csv` pins current inputs; only comparison launch files changed.

Pinned runtime hashes:
- Server: `1931A175025884E2E790363F7EEACEA096FAB3B8C9D41E3C273F426DE706A356`.
- Hook: `258C834F1A524F039CF96D74EBDED5650A9AA3FE1166759C808CE961AE1A3D36`.
- CRT3 fixture (to be omitted):
  `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`.
CRT18 remains suppressed and retry disabled. Baseline launcher remains CRT3-on.

## On the next user loading message

1. Read fresh timestamps/logs, not stale watcher or launcher files. Main paths:
   `SharpServer/bin/Debug/NexusToR.log`,
   `nexusclient/nexusclient/nexus_hook.log`,
   `Diagnostics/PhaseLifecycle-20260930/launcher-console.log`, and
   `crt3-off-launch-requested.txt`.
2. Confirm current launch explicitly suppresses CRT3, fixture .3 is not emitted,
   named hooks install, current runtime hashes match, retry disabled and CRT18
   suppressed. No observer READY is required in this user-authorized scope.
3. Confirm usable world entry with the operator. Ask for one walk through the
   visible exit doorway, stop at wall or outside, no abilities, client open.
4. Preserve accepted C5 crossing, exact destroy bytes/hash, generic apply,
   named destroy entry/return, nested gateway log (or absence within callback),
   player-phase-data events and operator outcome. Generic CRT counts can shift
   by one with CRT3 omitted: correlate timestamp/stream, do not demand count 18.
5. Preserve result and update experiment 07/index/registry only for the claim
   actually supported. No guessed AssetCreated, InstanceCreated, SendToArea,
   CRT18, awareness resends, fabricated triggers or _Room_Activate packets.

The script describes gateway update conditional on parent resolution, lookup
membership and local-player resolution. The live baseline doesn't establish
which branch failed. CRT3-off comparison is next; do not claim the wall cause
is solved or that room streaming was established.

## Live CRT3-off run 15:11:20
Operator loaded and standing still. Startup completed 15:14:37; CRT3 suppression confirmed; four hooks installed 15:14:36. Startup gates/settings/identity saved in live-20260930-151120-crt3off-logonly. User authorized to cross once next; outcome pending. No external observer. Preserve logs before restart.

## Completed CRT3-off comparison — authoritative latest result

Read live-20260930-151120-crt3off-logonly/RESULTS.md. At 15:19:43 accepted
movement crossed -64.87 to -62.94. Identical 46-byte destroy and SHA as CRT3-on;
PacketWorkbench zero differences. Generic CRT apply 17 brackets named
phase-info destroy entry/return. No nested gateway call or player-phase-data
create/destroy recorded. CRT18 suppressed. Operator walked into wall for a
second and remains stuck. Startup without CRT3 was rendered and movable.
Full preserved logs: DoorwayControl-20260930/phase-lifecycle-crt3off-blocked-20260930-152018-571.
Experiment 07 and registry callback row updated. This comparison is complete.
No global-state/lookup/trigger/room-residency equivalence claims. No default
runtime/config changes. Do not repeat CRT3 runs; next work should statically
trace April gateway/room-content evidence and define a concrete target before
requesting a new client launch. No external memory observer. Client can close
now that logs are preserved; do not auto-restart.

Next offline target is detailed in NEXT-STATIC-TARGET.md: trace native area collection/selection loop VA 0x0071C610, selected-object pointer writers +0x2A0/+0x400 and activation/collision callees. Extracted gateway-state body updates FX/cached-trigger collision; it does not establish a room-load packet. Older definitive wall/trigger claims remain hypotheses. Client stays closed until a concrete new target is ready.

Offline trace now saved in native-room-offline/FINDINGS.md. CSV script index reviewed; both BaseClient scripts already extracted, no specific JP export needed yet. Native change routine B91AE0 uses area+298, stores global14927B0, dirtyflag12E393F, calls B8F5E0 to resolve related/fallback and store+400, then B7C390 activation or deferredflags if+90!=6. +2A0 registration matches _everywhere_; prior pointer timeline doesn't settle +298 input. Next trace entity room association+98 setters and B7A040 resolution/readiness. Executable hash unchanged; printed byte-prefix verification passes. No runtime or wire behavior changed. No new client request yet.

User requested both-tree existing handling review. See repository-comparison/FINDINGS.md and two comparison CSVs. All48legacyserveropcode keys retain identical symbolic names in current; reference61116AD5/F96DCDB0/7CB9A193 also unknownencodednames. Ref7CB9 andAreaModules handlers empty; no61116handler. Reviewed reference areaattach is fixture replay1..17, no proven dynamicdoorway handler. 19/20CRT/awareness/hackfixtures identical; CRT3differs (live uses override/off, not diskbase). Reference read-only. Does not prove olddev never solved it elsewhere. Prioritize auditing adapted startupdata/order versus nativeclient selection before newpacket work.

User highlighted Packets/MessageHeaders. Follow-up saved repository-comparison/MESSAGE-HEADERS-REVIEW.md. Important naming correction: C++Framework Packet.h maps61116AD5=CMSG_CHARACTER_SYNC; currentrawCMsg loglabel is a presentationgap. Earlier claim48retainednames only covers C#legacyenum, not allC++names. Headers already used byStyle7decoder/startupanalysis; many opaqueunknownfields and versionconstraints (HackPack54fixed vsTython35). Review movementmaskwidth againstApril before changingdecoder. No wire/runtimechange this turn.

Startup order/destination audit saved startup-order-audit/FINDINGS.md. Original/currentwriteorder compared to preservedoffrun; earlySetCharacter alreadytestedfailed (don'trepeat), teleportafterCRT2 intentional, bulkCRT/awarenessorder retained. Authoredretreat c/d portals explicitlytargetgnarls_new, but live+298/player+98selection unproved. Major correction: room+1BC is EnviroScheme, proved parserB7D53B string115A950+setterB79F70; B7A040/B8D0F0 fallbackArea and+400path is environment-related, NOT destinationproof. Updated nativeFINDINGS. No runtime/configchange, no clientlaunch. Nextoffline trace playerroomassociation setter/collisionportalpath to+298; onlynew bounded eventlog couldsettlelive selection/readiness. Userdoesn'twantbroadobserverloops.

## Prepared experiment 08 — native room event log, awaiting operator run

Read Diagnostics/RoomSelection-20260930/README.md and experiment08. Three
hooks B90CF0 (register/name/returned room), B91AE0 (area+298 changes), B7C390
(activation numeric+8C/+90/arguments). Opt-in ROOM_SELECTION=1, no scans/dumps,
extra game calls, writes or newpackets. Caps512/256/256,127char names, PIDtagged,
readfailureFFFFFFFF. Same-room selections don't consume logbudget.
Originalcalls forwarded once including aftercaps. Don't equate EnviroScheme
with physicaldestination or numericstate with collisionreadiness.

Release Win32DLL SHA256:
1B30BFD4DE2C822C83E36B23EF7C62624F7CBDA0589D1A130BD1AD154511E0DD.
Server unchanged1931A175...356. Prefixcheck144PEbytes passes. Localx86ABI test
1542calls/LastError/faultreads/relocation/144mutations passes; live installation
stillunverified. DedicatedVerifyOnly passesall28CRT3-off settingssameexcept
newlogflag. No client/server auto-started. Basecmd/ref unchanged.

Launch D:\SWTORClassic\swtoremu\Run-SWTORClassic-RoomSelection.cmd, loadTython
standstill noabilities. Confirm freshlaunch timestamp, installedDLLhash,
CRT3suppressed, NativeRoomHook INSTALLED for mainclientPID, samearea name maps
for gnarls_new/retreat and initialselection before onecrossing. If names/prefix
fail don'trepeat observerloops; preservefailure and diagnose concreteproblem.
Then onecrossing, stopwall/outside clientopen, correlate acceptedC5/destroy
with select/activate, preservefreshlogs withPreserve-Logs beforeclose.
Logs newRoomSelectiondir launcher-console/errors/launch-requested; server
SharpServer/bin/Debug/NexusToR.log; hooknexusclient/nexusclient/nexus_hook.log.
Oldsource/DLL/identity backedup; oldLifecycleidentityunchanged intentionally,
oldlaunchersrejectnewhash. Use newidentity/newlauncher. Registrynotpromoted.
Doorwaystillunfixed; runpending. No external observerREADY requirement.

Experiment08 live pre-crossing verified, launch16:34:05, mainclient13756,
server27744. See RoomSelection-20260930/live-20260930-163405/PRE-CROSSING.md.
Installed/pinnedDLL agrees, CRT3suppressed, room/lifecyclehooksinstalled.
Roomnamesmapped: retreat_d D2C19000, gnarls_new F4C38000, area F40E39A0.
Startup16:37:21 selectsretreat_d; BOTH retreat_d and gnarls_new activation
logs reach8C3/906 BEFORE any operator movement. This weakens a blanket
claim exteriorneveractivates, but doesnotprove collision/fullcontentreadiness.
No limits/mismatch. Userstoodstill. Authorizingonecrossingnext; preservefresh
nativechangesanddestroy, userstopwall/outside/clientopen/noabilities.

## Completed live room-selection run — authoritative result

Experiment08 results saved RoomSelection-20260930/live-20260930-163405/RESULTS.md.
16:39:58 client13756 selected gnarls_new F4C38000 from retreat_d D2C19000,
area F40E39A0. Exterior activation already happened atstartup16:37:21 (2/6->3/6),
atdoorway already-active branch3/6 entered/returned. selectreturn before destroy
parse/apply in SAMEhooklog; no blanket cross-thread/clockorderingclaim.
AcceptedservercrossingX -64.87->-62.93, exactsame46-byte destroy/hash0differences;
CRT17bracketsnamedphaseInfoDestroyentry/return, no nestedgatewayrecorded.
Operatorstoppedwallstillstuck. No caps/readfailures/prefixmismatch.
Snapshot only smallcurrentserver/hook/launcherlogs, not oldlogs/fullmemory.
User can closeclient; no newrunrequest yet. Roomselection/activationfailure
falsified forrun; fullcollision/contentreadiness/player+98/triggeridentityunknown.
Nextofflinework: _SetGatewayState cachedtriggerCollidable and nativephysical
collider association, identify actualwallsource before newtest. Don'tguesspacket.
Updatebest-blocker hypothesis awayfrom exteriorneverselected/activated. Hook
staysopt-in; no runtimefix. Oldlaunchersstillrejectnewhashbydesign.

## Offline collision path after experiment08

Client closed per operator. No newruntime/config change. Read
RoomSelection-20260930/collision-offline/FINDINGS.md. Verified357listingprefixes
against pinnedPE plus RTTI: TriggerNode vtable116116C,+B4=7FDE70, type
.?AVTriggerNode@@. Collidable name1147BAC dispatch7FD9FB->keyB4963DC1->B4.
Setter7FDE70 standardthiscall(key,bool) ALreturn/ret8 updates+E0 bit1000,
changedtrue->6D4FB0 customEAXobject->D1E7B0 physics association;
changedfalse->6D4F60->D13480 removal path; samebit no association call.
Gettersreadsamebit. Entity+98room,+F0collider,room+120area,+4B0manager prerequisites.
Important:6D4FB0customEAX ABI, don'tguessthiscall.

Scriptcollisiontargets cachedtype3 INSTANCE_REGION, notgatewayeffectclone.
DerivedphsClassPhasedInstance state table disproves old claim onlyCanExit
leavescollisionfalse: CanJoin/CanOwn alsofalse, HasPhaseLock/CanOwnOrJoin
greenBUTtrue. Green/banner doesn'tprove liveCanExit. Cachedsamevalue means
noCollidablewrite, notproof nativebitclear. No nestedUpdateGateway3runs but
onlynested logging; othercallerupdatesunmeasured. Liveblockingcolliderunknown.
Next: statically deriveboundedTriggerNodeidentity/name/TriggerParam/position
reads, thenoneprecisesetterlogifneeded; don'trepeatroom/CRT3 experiments.
No clientrunneededuntilconcretetargetvalidated. Registrylocalcollisionrow
Client-derived only, no opcode claim/promotion.

## Prepared experiment09 — targeted collision log, no live run yet

Read Diagnostics/TriggerCollision-20260930/README.md. New launcher
D:\SWTORClassic\swtoremu\Run-SWTORClassic-TriggerCollision.cmd, userlaunch only.
CRT3off, roomlogretained, all29oldsettingssame, onlyTRIGGER_COLLISION=1.
NewDLL185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED.
Newhooks TriggerNode string7FE1F0(keyD84FB395 TriggerParam,wchar*,AL/ret8)
andBoolean7FDE70(CollidableB4963DC1,byte,AL/ret8), both exact48byte gates.
Identitypointer object+138:firstDWORDhashsourceproven7FE27F, hash148/14C;
Name110:firstpointer. Localcachetransform24/position2C30/34 loggedRAW; bit2
cachevalidity, NOTunqualifiedworldposition. 600verifiedlistingprefixes+RTTI.
AuthoredCSV3regions/1gateway, ExistsOnServer/Collidablefalse notliveproof.

Targetonlyknightretreat;256identity/256collisionevents,8otheridentitycontrols.
Fixed64event-derived pointers, atomicpublish; snapshotsbefore/afterexisting
roomselect max32, revalidatetype/param, notprocessscan/polling. Snapshotcatches
unchangedflagswhennoCollidablecall. +E0bit1000,+F0collider/+2Cbit40; snapshots
result0placeholder, readfailFFFFFFFF. Eachoriginalonce, AL/LastErrorpreserved.
Test519calls/filter/caps/snapshotrevalidation/faults/96mutationspassed.
Win32build and5PEprefixes pass, dedicatedVerifyOnlypinned/noautostart passes.

NewlaunchpreservesONLYcurrentserver/hook/ownlaunchlogs, full<=8MBeach else
marked2000linetail. Testedcurrentlogbackup. No staleoldlogs/memorydumpscopy.
BeforeToR/DLL/RoomSelectionTraceheader+baselineidentity backedup (headerbyte
hashverified). Oldroom/lifecyclelaunchpins unchangedrejectnewDLL. Basecmd/ref
unchanged. No runtimefix/protocolpromotion. Furtherlivegate needs mainPID
INSTALLED bothhooks, exactDLLhash, CRT3off, roomnames ANDtargetidentity/valid
snapshots beforeonecrossing. Userloadstandstill/noabilities first. Ifnone
preservecontrolsandfailure; noobserverloops/repetitivedoorattempts.
Afteronecrossingstopwall/outsideclientopen, savesmallcurrentlogs/destroy.

Experiment09 freshstartupverified17:28:07, main10580/server8188. Allpins/DLL
match, hooksinstalled, CRT3off, no cap/fault. SeeTriggerCollision-20260930/
live-20260930-172807/PRE-CROSSING.md andlocal-coordinate-map.json.
5nativeTargets:3authoredregions/originalgateway/clone, exactknightTriggerParam
+coordinatesmatch, validcachebit2. RegionsCollidable1then0at17:33:08 with
physicsmembership40setthenclear. Atretreatselectreturn17:33:09 all5bitsclear.
OldclaimsstaticengineTriggersabsentarecontradicted forTHISrun; don'toverclaim
alltriggerpresence or fullcollisioncontact. Crosspending userstoodstill.
Authorizeonecrossingnext, stopwall/outsideclientopen; correlateknownsnapshot
andanycollisionchanges withsame46bytedestroy. Noextraobserver/scansrequired.

## Completed experiment09, wallpersists; C7 rejection noted

Read TriggerCollision-20260930/live-20260930-172807/RESULTS.md. 17:34:46 room
switchretreat_d->gnarls_new; all5identifiednativeknighttriggers revalidated
before/return, collision1000ANDphysics40clear. 3exactauthoredregions+original
sourcegateway+namedclonepresent. No cap/fault/re-enable. Thereforemeasured
persistentregioncollisionhypothesisfalsified; notproofeverycolliderclear.
17:34:47 C5cross -64.87->-62.92, identical46bytedestroy/0diff/namedcallback
enteredreturned, no nestedgateway. Userstoppedwallstillstuck. Snapshotcurrent
smalllogs saved. Usercancloseclient, no restart needed.
UserhighlightedRejectedC7 opcode61116AD5 component65B30008 length56 offset8.
RawcompleteC7samples+firstbinarysaved. CurrentdecoderC5only; C7 extra12bytes
fitscandidateMoveVecflag2 fromlegacyPlayerMoveState BEFORE EndPosition, but
u16mask+endpaddingvsu32current requiresAprilnativeproof. Don'treadC7 XYZ at
C5offsetsorpretendmissingackproven. C5stillaccepted/crossingactioncompleted.
Nextoffline targetC7nativewrite/readfieldorder andwidths, existingheadercompare;
no repeatregion/room/Crt3runs. Othercolliders/playerroomassociationunresolved.

## C7 decoder fixed offline; experiment10 ready, no auto-launch
User closed client. No game/server processes observed. April send A80080 -> AA6920 verified against pinned PE;341 printed prefixes. Mask is u32 (legacy u16/headerpadding differs); C7 adds12-byte vector before end position. Decoder supports captured C5/C7 only, preserves raw body and uses correct C7 position offsets28/32/36. No guessed ack or room packet. Before source/server/tests/registry preserved in MovementC7-20260930.
Debugx86 server SHA150A707AA20D324BEC1B19671BEE9B65CC1B3227BBB35A0654E179BBEF37C9CD. Hook unchanged185B86... All environment settings compared equal to experiment09; new identity/VerifyOnly pass, older pins unchanged intentionally fail new server. Run-SWTORClassic-MovementC7.cmd is next manual launcher. No processes launched by agent.
Build/decoder100truncations+dispatcher/no-gameplay/area routing/blob framing/wire roundtrip/workbench pass. WorldEntryOffline existing missing RequestWorldFadeIn observer failure unchanged. Workbench old uniqueness check failed before change due multiple claims per opcode and UNKNOWNlocalrows; now checks opcode/direction/name without removing opcode/name lookup checks.
Read MovementC7-20260930/FINDINGS.md and Experiments/2026-09-30-10-c7-movement-decoder-control.md. C7 rejection alone not proven wallcause; preceding09 acceptedC5 still crossed/destroyed and room switched. Next one fresh run tests C7 accepted -> crossing and visible wall/outside result, with unchanged hooks. User loads/stands still, inspect new DLL/server/config then authorize one crossing; stop wall/outside/clientopen, preserve only small currentlogs. If wallpersists do not repeat observer/CRT3/region trials; unresolved other collider/contact/playerroomassociation. No runtime fix claim yet.

Experiment10 completed: live-20260930-180457/RESULTS.md. Nine C7 accepted18:10:19-23, C7 triggers crossing(-63.37->-62.94)/same46byte destroy. Hook exterior selection/activation3/6/namedcallback complete; five knowntriggercollisionbitsclear. Operator stillstuck. C7 liveacceptance Behavior-verified, rejectionalonewallcause falsified. Small logs saved18:10:40 beforeclose; user told canclose, no more doorwayattempts. Keepdecoderfix. Nextoffline inspect other collider/contact and characterroomassociation, no guessedpacket/ack or repeatedroom/CRT3/region controls.

Jedipedia position search completed: see MovementC7-20260930/jedipedia-comparison/FINDINGS.md. Reader [1.2.0] room portals reciprocal and match local assets/native selected room. Nearby concrete barricade0200 origin0.830 engine units (~8.30m), embedded collision188 triangles bounds3.99x2.00x1.51m; scaled radius cannot reach stop, weak candidate. Beware reader position table x10/XZY versus authored XYZ; do not call0.83 metres. Next inspect retreat shell geometry/native transform unit agreement and player association. No config changes, no launch; client stays closed.

Retreat shell offline comparison saved in jedipedia-comparison/FINDINGS.md and shell-model-bounds.json. Exterior embedded9212triangles includes hidden440; model bounds encompass stop bothYrotation signs. Local BWAG header validates reader x10 metre conversion. Interior_d model AABB overlap dependsYrotation convention; cpointoutsideboth (notcapsuleproof). Exact blockingtriangle/contact uncomputed. Reader OBJ export failed to provide download; interior UI stalled; stop UI retries. No runtime change/run prepared. Next native transform sign and validated collisionmesh/contact, client stays closed.

Generated collision meshes parsed offline with validation/positive controls; see Inspect-CollisionPath.py/collision-path.json. Actual recorded approach +/-0.3engineunits at5heights, bothYsigns, zero shell triangle intersections; nearest steep shellface >=4.57m. Weakens authoredshellwall only; native matrices/capsule/convex/activecontact unresolved. User highlightedciCollideInfoDebugger: reader client79Bstub allsections empty, no executable methods. sysBaseClientClassMethods1220 calls CollideRaySegment with hitvector/hitnode outputs; stronger nextlead. PinnedPE completeASCII/UTF16 querynames absent (Locate-CollisionQueries.py). Need metadata/nativebinding or existing debugcommand, not guessedhook. No runtime changes/newrun. Keepclientclosed.

Native collision query binding recovered: see jedipedia-comparison/FINDINGS.md section Native ray query. Local414namehash dictionary270EA7C38E8 agreesreaderCollideRaySegment; pinnedPEregistrationC191BD->C15380->CollisionScene root14928F0+858 vtable10D98F4/+14D1F6D0.545printedprefixesverified, RTTIexactbwaCollisionScene. Wrapper has hitvector/NodeRef output, managedresultctorD023F0/dtorB5A5A0, queryfilter2, aligned16bytevectors. Not yet callable diagnostic: verifyresult/filter/game-thread/activecontext; RaySegmentIsObstructed not provencalledduringmovement. No observerhook/runtimechange/run. RegistryNativeCollisionRayQueryBinding added; beforeCSVsaved. Userkeepclientclosed.

Ray lifetime/filterfollowup completed: see FINDINGS.md Result lifetime. ReaderFunction167 exactVector3/Vector3/refVector3/refNodeRef ->Boolean Symbol311 confirmed. D023F0 constructor/B5A5A0refcountcleanup, lazyresultstates; constructordoesnotinitallfields. D02750contextfilter2+4, otherglobalearlyoutbitseparate. D134B0->D20020 numericalcollider2Cfilters02/04/08/10/20; D1EF60 shape+1C/vtable1C getsfilter2 unchanged. Nextshape-specific filtermeaning/exactABI/game-threadsite needed. No passivehook assumedcalledonmovement; no runtimechange/clientrun. Usercommenthaveyouseentable answeredyes metadata used. Contextsaved.

## Transition symbol order checked against compiled bodies
Jedipedia reader Assembly view, sysBaseClientClassMethods script14988129110554817399:
- Dictionary172=7F34CD54 _NotifyPlayerCanTravel; body section0+7A40 is C3 RET.
- Dictionary173=43A3B07F _NotifyChangeAreaRequest; body section0+7A90 is C3 RET.
- Dictionary174=BF20A815 _Room_Transition; body7AC0..7AF4 calls only !HM.TrackLine and !HM.GetStringLength, then returns. No call to either notification.
- Relocations1421 at7A83,1422 at7AAB,1425 at7B7F are calls from each corresponding !sep argument adapter to its own body. They do not chain the three methods. Adjacent symbol entries describe compiled layout, not required execution order.
Inspect-TransitionBodies.py validates the exact Room_Transition body against local decrypted payload (unique match establishes section base5231), both RET bytes at expected offsets, and all three name hashes. Output transition-bodies.json. Local script archive SHA22BA4144FC2A63C3048231E8698DA413F23E72346936A35BC8FB274934216E1D.
Bounded text search across _JPEXTRACT, SharpServer, swtoremu2/Server finds only the three definitions in _JPEXTRACT/sysBaseClientClassMethods.txt. This does not establish absence of native or other compiled callers. Empty compiled script bodies do not establish that the overall engine events have no effect.
Confidence: Client-derived. No inferred packet schema or lifecycle order, no runtime change, no new client run. Next inspect native event dispatch/player collision context; do not add guessed notification ordering based on symbol adjacency.

## Shape-specific native ray filtering recovered
Offline pinned April PE RTTI inspection identifies bwa::CollisionTree vtable10D9A14, CollisionCharacter10DA0AC, CollisionHeightField10DA114, CollisionBox10DA23C. See Inspect-CollisionShapeRtti.py and collision-shape-rtti.json. Recorded entries stop at first non-code-range pointer; this is a bounded prefix, not proof of complete table length. RTTI descriptor/COL references and function pointers are read from the pinned PE.
Shape slot+1C for tree D20690 forwards to its own slot+4C D20960. Character D27D80 similarly forwards to D27F80. Tree D20960 transforms the segment using supplied transform, passes filter unchanged from EBX+14 to mesh-data D244B0.
D244B0: mesh-data flagbyte+18 must have bit01 and must not have bit02 (D244E7..D244F1). Candidate data +40 must have first word3 (D24599). Filter integer compared with2 at D245A2: equal jumps to D245CF, bypassing the category check. Other values require non-null category/material entry and its vtable+0 return equal to filter at D245B6..D245C9. Thus filter2 bypasses this mesh category discriminator; it does NOT bypass earlier collider flags, mesh enabled checks or geometry intersection. Numerical interpretation Client-derived; do not invent category names.
Heightfield D4DAC0 and box D516D0 use their own ray intersection paths; their inspected bodies do not load the passed filter slot EBX+14. Character D27F80 passes it to child geometry vtable+0C. Query equivalence to player movement remains unproved; do not treat a negative ray as a capsule sweep clearance result.
Trace-CollisionQuery.py verifies printed disassembly byte prefixes against pinned PE for all recorded ranges, including new shape/mesh slices. Some slices include adjacent functions; only named entry/path is interpreted. No hook/server/config change, no client launch or run requested.
Next: find the actual player movement collision/sweep caller or character room association and compare its collider/filter path. Broad passive CollideRaySegment hook is still inappropriate because this script helper is not proven called by walking. These recovered ray entries can support a targeted diagnostic only once game-thread context, safe result lifetime and actual movement relationship are established.

## RequestInstanceTransfer lead reviewed
Jedipedia reader trvTravelComponentClassMethods14988169905887148546 Code view: RequestInstanceTransfer(Integer) checks CanAreaInstanceTransfer, selects numbered entry from Travel.GetAvailableInstanceList and asks user to shuttle to another planet instance. RPCAcceptInstanceTransfer calls server grpGroupManagerClassMethods:GetGroupGSSID() untrustedMethods:GSSOnRequestInstanceTransfer(pending instance). CanAreaInstanceTransfer returns InStoryArea when Me.GetPhaseInfo()!=None. Local guiApiClassMethods153..162 invokes this from requestInstanceTransfer UI; gldOracleClassMethods2120..2135 offers it when guildmate currentAreaID matches but area instance differs. This supports numbered planet-copy switching, not automatic walking through local room portal. Does not disprove a separate story-phase server transfer requirement. No RequestInstanceTransfer implementation found in bounded SharpServer/Packets/swtoremu2 Server text search. Reader decompilation semantics only, no proven wire shape or native acceptance. Next distinguish room/phase transition from numbered planet instance transfer; no runtime change/client launch.

## Normal character phase-change path: new concrete missing update
Reader phsEntityClassMethods script14988219368268985980 (2.34KB): GetPhase returns Me.phsPhase; GetPhaseInfo converts the same ID to NodeRef; GetPhasedInstance resolves that node then its parent. Replication_Update!selfhandler checks changed-field ID0x40000002641F28CC (phsPhase), verifies local player, and calls $PHASE.OnPhasedInstanceUpdated, then adjusts companion/targets/group UI. This script was missing from local _JPEXTRACT text inventory; reader now supplies its body.
OnPhasedInstanceUpdated local phsOracle lines170 onward compares old phsCurrentInstanceNameID with current GetPhaseInfo().GetPhasedInstance().GetInstanceNameID() (or0), calls pc.OnInstanceChanged(old,new), old.OnPlayerExitedInstance(), updates current instance ID, then entry or exit GUI/gateway callbacks. No server transfer RPC in this observed update path.
Gateway TriggerEnter calls UpdateGatewayForInstance and OnPlayerEnteredGateway. TriggerLeave extracted unknown is not proof of no behavior. Type3 instance triggers get TriggerInstance class glommed; type4 gateway triggers get phase FX. Native TriggerInstance handling remains unresolved.
Active PhaseExit.OnMove sends only AreaReplicationDestroy, no player phsPhase update. Destroy callback removes node from instance phsPhases lookup and clears join overrides, not the above phsEntity Replication_Update path. Consequently source comment claiming exit is exactly destroy is not established and is contradicted as a complete description by this separate phase-field lifecycle.
CRT4 schema mapping in WorldEntry-Style7-Decode-20260924.md1009/1050 identifies player structure26 field25 phsPhase and packed valueCC1AC6F6DC1F. Older Phase-Mechanics note phsPhase=1 comes from different startup/create state; do not confuse it with final CRT4 link.
Next concrete implementation preparation: validate local schema/field25 type, build a single-field player phsPhase=None update using existing style7 writer/state conventions, round-trip offline and verify native callback delivery contract. Test opt-in phase-field clearing at crossing against current destroy-only baseline, with controlled transaction stream and explicit ordering; do not guess packet body, duplicate nodes or require live run until prepared. A field update is supported lifecycle input, NOT proof of wall fix or complete server instance transfer.
Bounded searches in SharpServer, swtoremu2/Server and MessageHeaders found no named phase exit/OnRequestJoinPhase/GetPhaseInfo handler. swtoremu2 has replay CRT/awareness/effects and named Area/World messages; absence of these names is not proof no unnamed handling. Locate-PhaseBindings.py uses actual reader dictionary hashes (earlier unverified computed hashes replaced), pinned PE has no occurrences; methods are compiled script definitions, not registered native external queries. No runtime changes/client launch. User goal remains normal seamless phase transition, no manual collision removal.

## Experiment11 ready: normal player phase link clear
User authorized implementation. Read Experiments/2026-09-30-11-player-phase-field-exit.md. PhaseExit opt-in SWTOR_PHASE_EXIT_CLEAR_FIELD=1 adds player structure26 field25 phsPhase UInt64=None before unchanged benign container/removal in same stream1B502E. Default destroy46byte hash unchanged. Candidate120byte hashBAB4C9...; decoder verifies captured215-field schema, ID40000002641F28CC, onlyfield25 supplied, allothersabsent, complete120byteconsumption. No manualcollisiondisable, no extra room RPC/stream. Source/binary/registry before copiesPhaseFieldExit-20260930.
New Debugx86server4E91FC57AE069DDF4D0811A390C22EE5DA489FDA36503BB866732C17415DBAE8; hook unchanged185B86...; new launcher Run-SWTORClassic-PhaseFieldExit.cmd -> Diagnostics/PhaseFieldExit-20260930/Launch.ps1. identity.csv and VerifyOnly passed; effective env includesCLEAR_FIELD1 andsame10baseline CRT3off/logonly/roomtriggertrace/retrydisabled. No process launched, client remains closed. Old launchers retain oldpins and reject newserver.
Baseline/postrouting/blob/wire/workbench pass; WorldEntryOffline same missing RequestWorldFadeIn observer fail. Packet test/Verify-PhaseField pass. Agent final authorizes user manual newlauncher, loadTythonstandstillreportloaded; then inspect smallserverlog/config and authorize one approach, stopwall/outside, keepalivecaptureboundedlogs. Record phasebanner disappearance as supportfornormalphasechange; serveremissionalone not fieldapplicationproof. No newobserver rebuildneeded. Live outcome pending. If wall stillpersists no claimlifecyclecompletewithoutphasefield/callbackproof.
Loaded-in pre-crossing check: area startup20:53:20, initial movement20:53:21 at(-64.874,-6.906,-127.671), no crossing/clear logged in last1200lines. Manual phase-field launcher launch-request20:39:46, current server executable matches4E91FC57... and installed MemoryMan185B86... unchanged. Launcher captured log-only phase trace / CRT3off configuration. Processpaths active NexusToRServer and two swtor-emu processes matchworkspace. CIM detail read denied; no retries/memory scans. Phase clear flag is set by pinned new Launch.ps1; actual branch execution will be confirmed by EXPERIMENT marker at crossing, do not claim marker already observed. Repository misses speedtree_collision.mat and /.tex present at startup, not newly assigned wallcause. User reports loaded standingstill. Authorize one doorwayapproach, stopwall/outside andkeepopen for bounded log capture. Outcome pending.
# Experiment11 live result — 2026-09-30 20:54:50
Operator reports still blocked at wall after one doorway attempt. Banner disappearance not answered; do not infer it.
Server new phase-field experiment branch emitted at20:54:50, stream001B502E,120bytes, field25None before phase-info removal; crossing(-63.40 -> -62.97). No CRT18. See crossing-server.txt.
Client hook same20:54:50: inbound routed0D446E80 source65B3/destination8; CrtApplyHook count17 entry and applied return; named phsPhaseInfo.OnReplicationNodeDestroy entry/return with stream001B502E. Exterior room selection/activation return; five measured trigger collision masks remain clear. This proves transaction delivery/apply path and destroy callback, NOT individual player-field application or OnPhasedInstanceUpdated execution.
Outcome: playable objective not achieved; clearing field alongside destroy did not visibly remove wall. Normal lifecycle hypothesis remains inconclusive because its specific callback not observed; do not promote opt-in default or repeat same run.
New identity caveat in saved hook at20:55:19: ReadinessVmHook character4000010E218A839B, whereas fixture/schema-derived player update node is4000010E218A839C. The distinction may be placed/root vs replicated node; audit it against existing character/replication records before any claim wrong-node or changing ID. GetPlayerCharacterNode comparison in phsEntity handler is essential and unverified for our target.
Logs bounded: hook-tail2000lines/server-tail700lines captured while client alive; crossing-server from1800line bounded tail. No new hooks/runtime change. User may close once agent final confirms capture. Next offline verify runtime local-player vs replicated node identity and self-handler invocation; if valid, trace phase-info link/parent/callback dispatch. No repeat doorway or manualcollisiondisable.

Post-close tail preserved after user clarified extended wall running: server-after-close-tail.txt(2000lines211151bytes), hook-after-close-tail.txt(2000lines193080bytes), in PhaseFieldExit-20260930/live-20260930-205320. Last C5movement20:56:58/59 and20:57:04 carries identical end-position bytes09D47BC24EC3DCC04374FCC2 while headings change, consistent with continuing input while positionblocked. Additional native room selections20:56:30/33/39 alternate selected pointers then returnF4F29500; exactotherroomnamesnotresolved, do not infer server phase transfers. Lastnamed phaseinfo destroy/apply remains20:54:50; no laterfieldcallbackproof. Disconnect20:57:10. Extra movement means run exceeded planned singleattempt; initial20:54:50 crossing evidence retained separately. Clientclosed peruser. No rerun needed; next offline audit player/rootnodeidentity and phase-field callback targeting. Userbannerstateunanswered.

Broad phase-transition audit complete for available offline evidence: read Diagnostics/PhaseTransitionAudit-20260930/AUDIT.md. Definite experiment11 implementation error: startup remaps captured839C to selected839B, generated exit field update bypassed remap. Therefore11 NOT negative evidence for clearing selected player phase or normal callback. Fixed PhaseExit -> AreaReplicationDestroy 4arg passes ActiveCharacter._id, rejects zero for clear, logs/serializes selectedID directly. Default2arg destroy46byte hash unchanged. Source/binary11 snapshots preservedauditfolder. Test-SelectedPhase/Verify-SelectedPhase integration verifies CRT2create/CRT4link/exit sameID for actualB and alternateID, bothhandles, field25only, exactend/removal. Build+postrouting/blob/wire/workbench pass; WorldEntryOffline same missing RequestWorldFadeIn observer. Registry11notes corrected/newSelectedPlayerPhaseExitIdentity row.
Savedpostcloseregister names resolve F4F29500gnarls_new,D30FA280gnarls_retreat_int_c,D30FA500gnarls_retreat_int_d. Laterroomselects are interior/exterior changes, not provenserverphase transfers. swtoremu2 inspectedread-only: ObjectReply startup replay, AreaModulesListempty, IN_GAME close/tracking/ping/TODOgamepackets, no completednamedphaseexit found. Phasefield -> localplayercomparison -> PHASE.OnPhasedInstanceUpdated -> old/newinstanceexit/entry -> GUI/gateway map recovered. Native characterphysicalroom/sweepcontact stillunknown, roomselect/activation notfullreadinessproof.
User requested broader audit and no repeatedisolatedtest. No newlauncher/repin/run requested; existing11launcher intentionally failsnewserverpin. Nextprepare combined bounded evidence selectedID+fieldref, phsEntity update changedIDs/localcomparison, PHASEold/newcallback plus existingdestroy/roomlogs. NeedexactscriptentryABI beforehooks; no broadscans/dumps/manualcollisiondisable. Userclientclosed; noautolaunch. No wallfixclaimed.

## Experiment12 prepared after broad audit; fresh manual launch ready

User authorized preparation. New launcher Run-SWTORClassic-SelectedPhaseExit.cmd,
Diagnostics/SelectedPhaseExit-20260930/Launch.ps1; identity.csv/VerifyOnly pass.
Server49B019822627080EF9132E85E34B8E95E0D93E261678FE1384D1806915BECA4A uses
ActiveCharacter ID for clear. New hookB9A7432B9A8F3708DC498E7138641323CF4882B48726C210B77E5517FC95290A.
TRACE_PHASE_UPDATE=1, CLEAR_FIELD=1, CRT3off/log-only1/retrydisabled, existing
room/trigger traces. No client or server launched; base verbose launcher unchanged.

Second definite audit correction: old oracle observer payload32E3/section2660
is SendCurrentPhaseInfoToGUI, NOT UpdateGatewayForInstance (actualsection32C0/
payload3F43). GUI hook label and one-Me-argument signature fixed. Registry notes
corrected; previous no-nested-gateway conclusions from this observer invalid.
Named phase-info destroy observations remain independent.

Prepare-CallbackPrefixes.py verifies exact April resources, entity payload14F,
oracle sectionbaseC83, callback section1940/payload25C3; resolves callback GUI
anchor minus720. Both loaded TrackLine relocs must match pinned native5D20A0
entry. Saved capture image slide derived from CurrentInterface absolute operand,
not assumed400000. Entity scriptasset SHA053D8D59... equals cachedDE84C79A54362211.
New PhaseUpdateTrace.h uses no new scan: entity identified from executing
TrackLine call only, prefix/fieldIDcomparison/epilogue checked. Logs capped128
checkpoints/32oraclecalls; native functions forwarded unchanged. Entity entry,
fieldmatched/localplayerpass, oracleenter/return/newInstanceNameID/exitbranch,
and player-phase-info-invalid can correlate with old room/destroy logs.
Read README for limits: old-instance-exit-branch-complete alone does not prove
old valid/called; need preceding call-follows. Exact old nameID not read; new
nameID slots78/7C initialized and verified. No NodeRef words interpreted as IDs.

Build passed (sandbox FileTracker denied; reviewed local build escalation passed).
Selected integration rerun/decoder, script/nativeprefix checkpoints, existing
lifecycle signatures, registry/workbench pass. Routing/blob/wire already passed
after server identity correction; WorldEntryOffline old missingfadeobserverfail.
OriginalDLL/source preserved PhaseTransitionAudit-20260930 before-callback files.
Experiment12 record created via New-ProtocolExperiment; gameplayonlyvariable
corrected selectedID, extra observers passive. Old launchpins stale deliberately.

Next user manually launches newSelectedPhaseExit, loadsTythonstands still/reports
loaded. Inspect boundedhooktail for PhaseUpdateHook installed marker and noERROR,
serverselectedID/startup/no prematurecrossing before authorizingoneapproach.
Do not claim installed before live marker. Then stopwall/outside, askbanner and
movement, leavealivecaptureboundedtails. If phase callback completes/newnameID0
andstillwall, investigate physical characterroom/contact next, no membership
guess/repeated observer trials. Live result pending; no wallfix claimed.
Experiment12 completed21:35:48; see SelectedPhaseExit-20260930/live-20260930-213358/RESULTS.md. Correctedselected839B120bytepacketmatchesofflinehash3A85682C...; clientgenericCRT17applyreturns; exteriorselected21:35:47; operatorstillwall/answeredno combinedbannerquestion.
NewobserverERROR21:33:58; noinstalledmarker; preparationalsoabortsexistingnamedlifecyclehooks. Thusnoactualfield/namedcallbackproof in12. Clientexitcode0/disconnect21:36:04; boundedhook/server/launcherfinaltails preserved. Clientclosed. Do notrepeatobserver-only run; nextoffline replication/eventdispatch andphysicalroom/contact evidence. Noexactobserverfailurecauseknownbecauseconditionnotlogged.


Experiment13 prepared: passive callback address corrected from GUI minus720 to minusD20, derived from pinned payload32E3/25C3. Address/relocation regression and Win32 build pass. Per-condition validation added; optional failure no longer suppresses old lifecycle observers. No packet change. Runtime pending. Use selected launcher, load and stand still to verify installed/startup callback coverage before doorway attempt. See experiment13 record.

Experiment13 final observer also accepts byte-verified deferred entity callbacks at CRT depth0; final DLL/build pins refreshed. VerifyOnly passes, no processes launched. Character-state callback acceptance remains pending live evidence.

Experiment13 live22:05:03 observer installed and independently exercised by startup phsPhase update/oracle new instanceFF5F184AAA9ECE77. Doorway22:05:35 CRT17 stream1B502E updates same entity but only entity-update-entry, not phase-field-matched or oracle callback;24 checkpoints below cap. Named destroy returns. Investigate changed-field notification/record semantics; raw storage value not independently read. Evidence live-20260930-220503/RESULTS.md. User visible outcome pending; client was live when saved.

Operator confirms experiment13 Still blocked. No additional movement/run needed. Offline comparison of recognized startup phase field versus exit record is next.


2026-09-30 correction: native style7 class field states are ONE bit per field; style8 TWO bits. Previous shared two-bit decoder invalidates style7 field-selection reports. Explicit style support and main/dump callers corrected. Old phase-clear style7 mask selected51 chrCurrentInteraction, not25 phsPhase. Serializer now style8, one-byte change only, opt-in. Experiment14 prepared; native regression and relevant packet tests pass, existing fade-in observer offline failure remains. Live outcome pending. See Diagnostics/PhaseFormat-20260930/FINDING.md.


Experiment14 result:22:21:51 corrected phase field recognized for local player; PHASE resolves no current instance, executes exit and gateway/UI branches, returns. Operator UI confirms leaving phase; invisible barrier persists. Phase-state portion behavior-verified, traversal failed. Evidence PhaseFormat-20260930/live-20260930-222139/RESULTS.md. Client closed. Next collision/contact/controller/room boundary evidence, not another phase-clear/observer repeat. Retain opt-in.

Phase-exit script-chain audit completed after experiment14: read Diagnostics/PhaseExitChainAudit-20260930/AUDIT.md. No additional transfer/movement-release call found in reviewed entity/oracle/participant/retreat exit chain. Phase exit is verified; full physical transition is not. Gateway nested decision/cache/registered trigger membership remain unmeasured, and referenced dynamic Hydra server actions remain unavailable as semantic export. Five tracked targets exclude Collidable bit at selection snapshots; do not claim these identify actual wall. Next offline reuse native collision/controller/room filter findings to identify blocking contact and room residency; correlate against phase trigger list before a bounded new run. No runtime edits, no launcher changes, no new run requested in this audit.

User requests Jedipedia cross-check of HeroScript plus all relevant metadata, fields, signatures and formatting. Added PhaseExitChainAudit-20260930/JEDIPEDIA-FIELDS.md: inherited trigger lookup ID4611686071571749259 separate from FX list, Not stored/attribute0 metadata; reader reverse references only creation binding and collision setter. OnReplicationNodeCreate enumerates matching type3/type4 triggers, conditionalHydra init, gateway refresh; OnReplicationNodeUpdate displayed no work. Creation-time enumeration coverage is unresolved; do not declare race or add packet without native/runtime evidence. Continue using reader class/field references and assembly alongside local semantics.

Player movement audit progressed: Diagnostics/PlayerMovement-20260930/FINDINGS.md. Read Jedipedia chrBehaviorLocalPlayer and chrBehavior code plus exact name dictionary. Mobility/dead/vehicle/combat-animation/ballistic permission gates and chrBehaviorPreCollisionPosition snapshot recovered. HashD97553EA native registration pointsAFA420->AFA130. Pinned RTTI BehaviorPlayerCharacterBWA tables115098C/1150A28, CharacterNode1151154. Offline extraction byte verified; utility outputs retained. Candidate7228A0 collision-position rejection uses target node, directcallers7347BC/C1AA3E; not proven normal walking. DO NOT install candidate hook or broad ray observer just from this. Next follow CharacterNode native update around BehaviorPostAnimUpdate and actual walking collision/apply path, establish hit+room identity. No runtime/config edits or client run. Reader current chrBehavior info dictionary expanded; preserve all user tabs. Suspicious decompiled HIBYTE/BYTE10 arguments require assembly signature check.

Movement continuation: utility also verifies CharacterNode727000..7283B0 and AFA130..AFA620. HashesEEED7B75/D742E6A9 (Post/FinalAnimUpdate) absent in executable, not proof callbacks absent. 727CD0 saved-vector application via6D5D60 and behavior slot28 is unclassified; don't install as walking observer. All work remains file-only. Native AFA420->AFA130 permission input handling established; actual walking physical query unresolved.

## Continuation: native movement path and public reference comparison
See ../PlayerMovement-20260930/NATIVE-COLLISION-PATH.md. Jedipedia April stand/grounding/movement debug scripts reviewed. Behavior update722250 reaches controller737120, movement collision737520/7B7450 and supporting-floor branch739AE0/738F80/CEF540. Normal walking coverage is stronger than prior target-relative7228A0 but remains unverified live. Need bounded proposed/output delta, collision record identity and supporting-surface result for same player/frame. No runtime/launcher change or run requested.
User-provided https://github.com/trespa/SwTor-1.3 reviewed at877fc9b268c30b575a85e1a68e62f54ebe331383: all86 server files SHA256-identical to existing swtoremu/Server. No additional phase-exit implementation; reference checkout D:/SWTORClassic/References/trespa-SwTor-1.3. See ../ReferenceAudit-20260930/TRESPA.md and per-file comparison CSV.

## Experiment15 ready � bounded physical movement evidence
Implemented Client/Hook/Src/MovementCollisionTrace.h plus PE-generated MovementCollisionPrefixes.h and ToR.cpp opt-in wiring. ReleaseWin32 build passed. Launcher Run-SWTORClassic-MovementCollision.cmd prepared; Diagnostics/MovementCollision-20260930/Launch.ps1 -VerifyOnly passed with unchanged experiment14 server/phase baseline, CRT3off, retry disabled. identity.csv pins new DLL and source; old manifest preserved. No game started by agent. Native query/contact output, not final character position; hit flag is collision result. 48 attempt samples/48 supporting checks at250ms, first4 contacts, stationary samples excluded. After manual load, approach door/hold3sec/step back/close. Read MovementCollisionHook prepared and normal update coverage then doorway samples. Missing coverage is inconclusive. See experiment15 record and BUILD-AND-CONFIG.md. User-supplied22:22:01 room excerpt preserved; exterior selection and linked-room activation returns verified, physical readiness unproved.

Experiment15 run pid2604: normal player query coverage confirmed23:36:36; snapshot saved MovementCollision-20260930/live-20260930-233249. Operator phase departure/tutorial confirms; barrier remains. All sampled sweeps clear/empty hits; all supporting-floor queries succeed. Player room98 changed from retreat D2ADA500 to exterior F4A69500. Not proof of no collision elsewhere: sampling and zero-delta bypass limit. Next offline resolve desired-displacement virtual slot+CC call7223A4 in CharacterNode table and later application; do not repeat identical run or guess transition packet. Processes were active when captured; user advised can close. Runtime left unchanged.

## Movement tether repair prepared
Read MovementTether-20260930/AUDIT.md. Native739D80 calls GetMovementLeashingInfo before physical sweep and can restore old horizontal position. Captured CRT4 final fields200/206: leash2.4, anchor spawn(-64.8741,-6.9062,-127.6710); live stop radius2.3988. User clarifies wall beyond green gateway; inward return did not restore phase UI. Opt-in finite movement anchor refresh206 every250ms implemented; captured leash preserved. Separate per-connection reentry service recreates only captured phase-info before restoring player25 with hysteresis/corridor detector. Shared existing stream allocator prevents anchor/phase/ability ID collision. Server Debug/x86 build passes; routing/blob/wire/workbench/custom8packet checks pass; known WorldEntryOffline fade observer failure remains. New manifests/VerifyOnly pass; no processes launched. First manual Run-SWTORClassic-MovementTether.cmd (reentry0, collisiondiagnostic0). Later Run-SWTORClassic-RetreatReentry.cmd after first outcome verified. Experiments16/17 pending. Restore/cause acceptance unverified.


## 2026-10-01: movement tether behavior verified
Operator passed former barrier with anchor refresh enabled. Full small live logs preserved in MovementTether-20260930/prelaunch-20261001-001118-779; see RESULTS.md and movement-summary.json. Phase exit logged00:02:19. Next: close client and servers, manually run Run-SWTORClassic-RetreatReentry.cmd; walk out beyond old boundary and return through gateway to verify phase UI restoration. Reentry remains pending; do not claim complete gameplay.


## 2026-10-01: reentry verified; gateway timing ready
Run17 full small logs saved RetreatReentry-20260930/prelaunch-20261001-002114-440; four exits/four returns, operator entering-story UI restored and barrier gone. Weller inside renders/nameplate fine; exterior NPCs incomplete, conversation work deferred per user. New final timing launcher Run-SWTORClassic-RetreatGateway.cmd enables authored-center symmetric crossing. See RetreatGateway-20261001/AUDIT.md; timing live test pending. ExistingWorldEntryOffline observer failure unchanged; E7 decoder rejects noted. Do not claim a general production phase engine.


## 2026-10-01: Tython retreat baseline accepted
User reports gateway timing better. Saved full small logs RetreatGateway-20261001/prelaunch-20261001-003805-442 confirm exit/entry/exit, corresponding callbacks resolve None/retreat/None. Combined with runs16/17: movement past old tether barrier and repeated retreat phase membership work. Use Run-SWTORClassic-RetreatGateway.cmd as known-good opt-in baseline; preserve runtime identities. Local phase work can move to Weller conversation/story interaction and exterior NPC replication, per user goal. General phase/group/quest trigger engine remains separate scope; do not claim it implemented.
`n2026-10-01 Weller interaction: all four clicks selector1279C371:99EB62D0 node1AC6F6DC6D; target-selection9738A931 separate. Opt-in initial conversation instance/schema60 then controller/schema59 implemented and offline checked. Working retreat flags retained in new Run-SWTORClassic-WellerStory.cmd; effective configuration verified. Historical gateway manifest retained and rejects new server build by design. See WellerStory-20261001/FINDINGS.md and experiment2026-10-01-02. Client scene acceptance pending; then implement exact completion/escape RPCs and quest hooks/persistence. No additional observer installed.

2026-10-01 Weller cinematic and conversation now Behavior-verified by operator, final camera stuck. Logs saved WellerStory-20261001/prelaunch-20261001-012911-086. End selectors70C14D2A/14CDD239 one owned controller ID, previously swallowed. Implemented bounded opt-in SWTOR_WELLER_END active-controller cleanup: controller removal then instance removal, clear server state. Experiment03, tests pass, new launcher pins/config refreshed. User next finish conversation, check camera/movement, repeat then Escape; preserve logs before rebuild. Quest hooks/progression/persistence still pending; precise finish/escape name mapping unresolved.
