# Tython phase-exit investigation checkpoint — 2026-09-28

## User-visible result

The character can move through the visible phase doorway far enough to reach
the invisible boundary, but the client does not transition out of the phase.
In the 14:08–14:09 test the character ran out, back in, and out again. Behaviour
was unchanged after relocating the phase instance and phase-info child to
CRT11.

## Preserved evidence

The exact logs from this run are preserved under
`Diagnostics/PhaseExit-Checkpoint-20260928/`:

- `NexusToR-1409.log`, 399,634 bytes,
  SHA-256 `A83C22523402CB7D1704FFDBBCA7914BC01BA2E7222F5B13A3FB2E81861465CF`
- `nexus_hook-1409.log`, 69,226 bytes,
  SHA-256 `05339921E2D4B614EC4B5DA8BED8D9CCA5D723C810474BC3C93E3226BD0EDA05`

All four diagnostic overrides were emitted and accepted without a client
serialization exception or `SendScriptError`:

- CRT1 `86DA2F5B07773E260FC6B6A39A7163628FE9541788A9324B84852D661AE580D5`
- CRT3 `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`
- CRT4 `5EEC86299E359D49CDB5572689CB0F446C6EAE7461667F211A86D17DCE7B7A86`
- CRT11 `1CE8AE7F2B9F1A45D06B180DA731FCF09525A011764CBF90F3A7F6010EABE8F0`

Awareness 2 was sent before CRT11. CRT11 therefore created the exact captured
master-retreat `phsClassPhasedInstance` and its exact `phsClassPhaseInfo` child
after the `gnarls_new` room object was delivered.

## Packet result

The doorway attempts are visible as movement packets from approximately
14:09:00 through 14:09:25. They cross between the phase-room and exterior
coordinate spaces, consistent with the reported out/in/out movement.

No new phase-gateway RPC accompanies those crossings. In particular:

- operation `0x852644E5` appears once at 14:08:56, during startup immediately
  after the replication bundle, not during a doorway crossing;
- operation `0xF5F540F2` appears at startup and once again at 14:09:23, but it
  is a parameterless nine-byte call and does not correlate consistently with
  the three crossings;
- no ability-shaped or phase-exit-shaped `CMsgF96DCDB0` payload is emitted at
  the boundary;
- no `SendScriptError` or native exception explains the absence.

This keeps the failure on the client side before a usable phase-exit request is
constructed. There is no server rejection to fix yet.

## Confirmed static data

The April Tython area contains the expected doorway trigger:

- room: `gnarls_new`
- static instance: `4611686037462170014` (`0x400000046E8FB99E`)
- asset: engine trigger `4611686019869492758`
- `TriggerClassType`: `INSTANCE_GATEWAY`
- `TriggerParam`: `tyt_jedi_knight_masters_retreat`
- position: `(-63.6167984009, -6.73430013657, -126.88469696)`
- dimensions: width `0.407692998648`, height `0.346105009317`, depth
  `0.130021005869`
- player sensitive, active, enter/leave enabled

The active phase identifier is `0xFF5F184AAA9ECE77`, and the replicated phase
instance is `phs.tyt_jedi_knight_masters_retreat` at node
`0x1AC688C97E`. The instance record retains its three captured anchor mappings
and Hydra script reference. The phase-info child remains parented to that node.

## Conclusions from the two ordering experiments

1. Creating the phase instance in CRT1, before awareness, did not produce a
   working exit.
2. Moving it to CRT4, after Awareness 1, did not produce a working exit.
3. Moving the instance and child together to CRT11, after Awareness 2 delivers
   `gnarls_new`, also did not produce a working exit.

Therefore replication order alone is not sufficient. The prior assumption
that delivery of the `gnarls_new` room object guarantees registration of its
static `INSTANCE_GATEWAY` with `GetTriggersByType(4)` is unproven and is now the
main question.

## Recommended next steps

### 1. Observe the client trigger registry directly

Instrument the 32-bit client at or immediately around `GetTriggersByType(4)`
or `phsPhasedInstance.OnReplicationNodeCreate` and record:

- returned trigger count;
- each trigger's node identity, class type, `TriggerParam`, position, and
  active/player-sensitive flags;
- whether `tyt_jedi_knight_masters_retreat` is present;
- whether `_AttachGatewayTrigger` is called and whether `ActivateInstance`
  succeeds.

This is the highest-value next step because it distinguishes three otherwise
indistinguishable cases: missing static trigger, failed stable-ID match, or
failed dynamic gateway attachment.

### 2. Trace trigger-enter dispatch rather than general area RPCs

Add a narrow hook/log at `phsGateway.TriggerEnter` and, if possible, the native
trigger-volume enter dispatcher. Record the trigger node and player node. This
will show whether collision/volume entry occurs but HeroScript dispatch is
missing, or whether the dynamic gateway volume was never active.

### 3. Validate the runtime stable identifier

Capture the actual result of
`ComputeStableIdentifier("tyt_jedi_knight_masters_retreat")` in the client and
compare it with `0xFF5F184AAA9ECE77`. The prototype/static-data relationship is
strong evidence that they match, but a direct runtime value removes possible
string normalization, case, or signed-width ambiguity.

### 4. Inspect room/trigger activation lifecycle

Determine which event actually registers static server-side triggers after a
room stream. Awareness 2 contains a `gnarls_new` dynamic placeable, but it may
not be the event that populates `GetTriggersByType`. Relevant candidates are a
room-loaded callback, area stream/visibility update, or a missing server
awareness object specifically representing the static engine trigger.

### 5. Only after observing the missing stage, choose a wire experiment

Depending on the trace:

- if the static trigger is absent, reproduce the missing trigger/room
  activation message or create a correctly typed trigger object;
- if the trigger exists but does not match, correct the runtime parameter or
  phase identifier;
- if `_AttachGatewayTrigger` runs but activation fails, reproduce the required
  property-bucket/init lifecycle;
- if `TriggerEnter` runs, decode and implement the resulting phase-exit RPC and
  server state transition.

Do not perform further blind CRT reordering. The three tested placements have
already shown that ordering changes without visibility into the trigger
registry do not advance the boundary.

## Root cause located — 2026-09-28 offline audit (supersedes "ordering" hypotheses)

Three offline checks closed the question that the CRT reordering experiments
could not.

### 1. The phase identity is correct, not mismatched

April prototype data for the captured instance resolves to
`phs.tyt_jedi_knight_masters_retreat` (`0xE000E8E230304F84`),
class `phsClassPhasedInstance`, with:

```text
phsNameID               = -45290762281234825  = 0xFF5F184AAA9ECE77
phsExitMapNoteID        = 4611686069191632234
phsConditionalHydraScript = 16141075611876778500
phsClassRequirements    = { 16141119516274073244: True }   (Jedi Knight)
```

`phsNameID` is byte-identical to the phase key decoded from CRT3. So
`Me.phsNameID`, the player's active phase, and the doorway's `TriggerParam`
all refer to the same phase. No identifier, class, or key is wrong.

### 2. Every static Tython trigger is a server-side engine trigger

Enumerating the April area (`4611686019869492753`) yields 536 trigger static
instances, and every one declares `ExistsOn=Server`:

```text
335 MAP              114 INSTANCE_REGION    52 HYDRA
 22 INSTANCE_GATEWAY   7 EXHAUSTION_VOLUME   5 GENERIC
  1 COMPANION_PRIVATE
```

The doorway itself, in room `gnarls_new`:

```text
Id              4611686037462170014
Asset           4611686019869492758  =>  engine\trigger   (hcaKey_engineTrigger)
TriggerClassType INSTANCE_GATEWAY
TriggerParam     tyt_jedi_knight_masters_retreat
Position        (-63.6167984009, -6.73430013657, -126.88469696)
PlayerSensitive  true     Active true     Enter true     Leave true
```

The matching phase-boundary volumes are `INSTANCE_REGION` instances
`4611686141633615041`, `4611686037853470885`, and `4611686037462170015`, all
carrying the same `TriggerParam`. A second `INSTANCE_GATEWAY`
(`4611686037462170018`, `tyt_jedi_consular_masters_retreat`) sits beside it.

### 3. Our replicated area-object stream contains no engine trigger at all

Replaying the two awareness fixtures gives the complete replicated object set:

```text
tython_blockout-...-1.1.aaw  flags=0x01 objects=77
    35 hydTriggerEntity   15 effContainer   5 eqpContainer   1 plcPlaceable
tython_blockout-...-1.2.aaw  flags=0x01 objects=9
     3 effContainer        1 eqpContainer
```

Every trigger we replicate is `hydTriggerEntity`, and those correspond one-to-one
with the static `HYDRA` instances — matching by position and by identity:

```text
static 4611686036538870008  (-58.9079017639, -5.40999984741, -127.919799805)
        TriggerParam        hyd.location.tython.hearth_stone.suppress_travel_trigger
streamed node 0x1ac688d54a  (-58.907902, -5.410000, -127.919800)
        hydRunScriptProtoId 0xE000AB389E7B29C4 =
        hyd.location.tython.hearth_stone.suppress_travel_trigger
```

So static trigger instances do become replicated nodes. Neither
`INSTANCE_GATEWAY` instance and neither `INSTANCE_REGION` volume is present
anywhere in the stream.

### Consequence

`phsPhasedInstance.OnReplicationNodeCreate` scans `GetTriggersByType(4)` for a
trigger whose `ComputeStableIdentifier(cur["TriggerParam"])` equals
`Me.phsNameID`. With no `INSTANCE_GATEWAY` node replicated, that scan can never
match, `_AttachGatewayTrigger` never runs, no `phsGateway` node is created, and
the doorway volume is inert. `phsGateway.TriggerEnter` therefore never fires and
no phase-exit request is ever built. The collision wall beyond the door is the
consequence, exactly as the live runs showed.

The engine trigger node class is `TriggerInstance` (`0xDFFE87FD`, id
`3758000125`) — the very class the phase script tests with
`cur is kindof 0xDFFE87FD`. It is an engine class with no GOM fields; its
properties come from the engine static-instance schema, which is why the GOM
class/field tools show it empty.

The preserved live dump corroborates this: the ASCII string
`tyt_jedi_knight_masters_retreat` occurs only twice, both inside the
`phs.tyt_jedi_knight_masters_retreat` prototype load buffer
(`phs.…\0tyt_jedi_knight_masters_retreat\0`). There is no independent live
trigger-node string instance for it.

### What this reclassifies

The phase door is a *symptom*, not a special case. The emulator replays two
small captured awareness fragments (~15 KB) and therefore replicates only a
fragment of the area's static content: 35 Hydra triggers, some child
containers, one placeable. All other server-side static engine triggers
(`INSTANCE_GATEWAY`, `INSTANCE_REGION`, `EXHAUSTION_VOLUME`, `GENERIC`) are
absent, which is also consistent with the missing enemies reported earlier.

### Ranked next steps (revised)

1. **Establish whether the client materialises static `TriggerInstance` nodes
   from its own area assets or expects them replicated.** This is now the only
   open question, and it decides between a small fix and a subsystem.
2. If client-local: the registry is populated late, so re-running
   `OnReplicationNodeCreate` later in the session (for example, destroying and
   recreating the phase instance once the room is fully loaded) should attach
   the gateway.
3. If server-replicated: implement emission of the missing `engine\trigger`
   static instances for the player's current rooms, starting with
   `4611686037462170014` and the three `INSTANCE_REGION` volumes for
   `tyt_jedi_knight_masters_retreat`.
4. Only after the gateway attaches does `phsGateway.TriggerEnter` produce the
   phase-exit request, which the server must then answer.

Instrumentation of `phsPhasedInstance`/`phsGateway` script methods is no longer
the first step: the trigger registry — not the phase scripts — is the proven
missing input.

## Probe result — 2026-09-28 14:29–14:30 run

`SWTOR_PHASE_INSTANCE_RETRY=10 / START=25 / CRT=11 / MAX=10` was enabled and
the doorway was walked out, in, and out again.

The probe itself worked exactly as designed:

```text
14:29:46  PhaseInstanceRetry: enabled, CRT 11, first delay 25s, interval 10s, max 10.
14:30:10  CRT diagnostic override [...-1.11.acrt] bytes=756 sha256=1ce8ae7f...
14:30:10  PhaseInstanceRetry: resend 1/10 of CRT 11 ...
14:30:23  PhaseInstanceRetry: resend 2/10 of CRT 11 ...
```

Both transactions were loaded and emitted with the validated CRT11 payload, and
the client neither errored nor disconnected. There was **no client reaction
whatsoever**: no script dispatch, no gateway RPC, no `SendScriptError`. The only
outbound RPC in the window is the unrelated periodic `0xF5F540F2` readiness poll
at 14:30:13.

This result is **confounded and therefore not yet decisive**. A replication
create for a node that already exists does not re-fire
`phsPhasedInstance.OnReplicationNodeCreate`, so the retried transaction was most
likely accepted and ignored.

### Corrected probe

> **Superseded.** This first "corrected" probe was still invalid three ways; see
> the 2026-09-28 correction section at the end of this file. The two identifiers
> quoted below — `0x1AC688C980` and stream `0x001B5023` — are precisely the ones
> that broke it.

`Diagnostics/Generate-PhaseInstanceDuplicate.py` emits
`tython_blockout-4611686019869492753-1.18.acrt` (97 bytes, sha256
`6752695e7bcca413…`), which creates a **duplicate** `phsClassPhasedInstance`
from the identical captured template on a fresh unused node ID:

```text
stream 0x001B502E (next free id)  node 0x0000001AC688C97E -> 0x0000001AC688C981
87-byte record, only the 6-byte packed node ID changed
template 0xE000E8E230304F84  structure 3 (phsClassPhasedInstance)
```

A fresh node guarantees a real create-handler run, removing the confound. The
four validated fixtures are untouched (CRT1 `86DA2F5B…`, CRT3 `EFE780D0…`,
CRT4 `5EEC8629…`, CRT11 `1CE8AE7F…`), and the duplicate carries no phase-info
child, so the player's own phase membership is not modified.

## Duplicate-create probe result — 2026-09-28 14:36–14:38 run

CRT18 was armed (`RETRY=10 / START=25 / CRT=18 / MAX=10`) and the doorway was
walked out, in, and out again.

The probe fired six times and was itself entirely successful:

```text
14:36:34  PhaseInstanceRetry: enabled, CRT 18, first delay 25s, interval 10s, max 10.
14:36:57  duplicate-instance create 1/10 sent via CRT 18
14:37:07  duplicate-instance create 2/10
14:37:17  duplicate-instance create 3/10
14:37:27  duplicate-instance create 4/10
14:37:37  duplicate-instance create 5/10
14:37:48  duplicate-instance create 6/10
```

Every emission was a valid 105-byte `AreaClientReplicationTransaction` carrying
the fresh node ID and the captured template:

```text
AREA-PAYLOAD type=AreaClientReplicationTransaction bytes=105
  23-50-1B-00 00-00-00-00 01 01 CC-1A-C6-88-C9-80 6A CF-E0-00-E8-E2-30-30-4F-84 ...
```

### Client response: none

Every inbound `CMsgF96DCDB0` in the window is a periodic readiness poll, and the
only non-sync inbound traffic is the 30-second `0xF5F540F2` poll at 14:37:02 and
14:37:32:

```text
14:37:02  CMsgF96DCDB0 rx  ... 09 00 00 00 C7 71 C3 79 12 F2 ...
14:37:32  CMsgF96DCDB0 rx  ... 09 00 00 00 C7 71 C3 79 12 F2 ...
```

Six genuinely new nodes of the correct class, ten seconds apart, produced no
phase RPC, no `SendScriptError`, no script dispatch and no exception. The user
also confirmed no on-screen phase message appeared, at any point.

### The larger finding: the server streams nothing after startup

The complete server→client traffic for the entire in-world window is:

```text
23 Ping          23 AreaClientReplicationTransaction (4..17 startup + 6 probe)
10 AreaRequestRPC 7 AreaEffEventMessage   6 AreaModulesList
 2 AreaAwarenessEntered   1 each of the one-shot startup packets
```

There is no awareness update, no object create, no room transition, nothing
keyed to the player's movement. The client's world is a fixed startup snapshot.

### Combined conclusion

- The engine trigger is not client-side: no `INSTANCE_GATEWAY` or
  `INSTANCE_REGION` node is replicated, and re-running
  `phsPhasedInstance.OnReplicationNodeCreate` six times on fresh nodes changed
  nothing.
- The user reports no phase-entry message on loading in, so the client never
  performs a phase entry at all.
- Because nothing is streamed after startup, the invisible wall is most
  plausibly a **room boundary** whose neighbouring room was never delivered,
  rather than a phase boundary. That also explains the absence of enemies.

This makes the unmet requirement **the area server's dynamic object and room
streaming**, of which "the missing gateway trigger" is now just the clearest
single case.

### Next step taken

`AreaStartupBundle` now accepts `SWTOR_SPAWN_POSITION=x,y,z`, and the trace
launcher places the character at the Gnarls arrival point
`(-16.0, -2.2, -99.5)` instead of the captured retreat doorway. That point sits
inside the captured object footprint — awareness node 26 is the
`hydTriggerEntity` at exactly `(-17.047001, -1.977500, -100.847801)` — which is
the only region the client has actually received content for.

This is a diagnostic, not a fix: it tests whether the client renders and moves
normally once the character stands where replicated content exists, and whether
the wall and the missing enemies are both simply the edge of the snapshot.

Clarification of what is actually there: a float-triple scan of both awareness
fixtures finds exactly five distinct positions in that camp box, and all five
are static HYDRA triggers of `gnarls_new`:

```text
(-17.047, -1.977, -100.848)  4611686038403572001  trig_gnarls_arrival
(-14.314, -2.299,  -93.310)  4611686060140231372  trig_gnarls_vendors
(-13.801, -2.462,  -99.647)  4611686060140231367  trig_gnarls_trainers
( -9.980, -3.169,  -92.293)  4611686170144650002  hyd.codex.bestiary.uxibeast
( -8.412, -2.682,  -99.525)  4611686067309731978  hyd.codex.location.tython.the_gnarls
```

No replicated `chrNonPlayerCharacter` position falls in that box, so this run
tests the snapshot-edge hypothesis and general rendering, and should not be
expected to produce visible enemies. The three NPCs present in the stream
(awareness records 3, 16 and 31, each with `effContainer`/`eqpContainer`
children) carry no position triple in the transmitted fields, so their location
cannot be derived from the capture.

## Current runtime state

No runtime or fixture changes were made after this final test. The active
diagnostic candidate remains the CRT1/CRT3/CRT4/CRT11 set documented in
`Diagnostics/GeneratedPhaseCandidate/README.md`. It is useful as a stable
starting point for the direct client instrumentation above, but it is not yet
a phase-exit fix.

## Fix #1 validated in-game — 2026-09-28

The CRT1 phase-info-child-before-player-create ordering was confirmed live:

- the yellow **"Entering Story Area"** banner reappeared,
- the **"(Owner: \<character name\>)"** line resolved, and
- the phasing help pop-up and the `setGuiPhaseData` UI both reflected the
  character's phase.

So `pc.GetPhaseInfo()` is non-null at `OnPlayerCharacterNodeReady`, the enter
branch of `phsoracle.OnPhasedInstanceUpdated` executes, and
`phsClassPhasedInstance.DeterminePhaseEligibility()` now reaches `phsCanExit`.
The ordering model in `Phase-Mechanics-20260928.md` is confirmed, including the
prediction that the doorway would be unaffected by this fix alone.

Two offline findings narrow the remaining work. Neither is a new runtime change.

### 1. The phase boundary is not the blocker

`GetInstanceGatewayState` leaves its collision out-param unset for `phsCanExit`
*only* — every other gateway state sets it to `1` — and `_SetGatewayState`
writes `Collidable` on the type-3 `INSTANCE_REGION` triggers only when the cached
value **changes**. With the phase child present from the very first evaluation,
the cache (initially `0`) already equals the new value, so the write is skipped.
The full table and the `_SetGatewayState` listing are in
`Phase-Mechanics-20260928.md` section 5. The wall is consequently world content
at the interior/exterior transition, not a phase-system artefact, so
`phsInstanceAllowAll` would not have been a fix even if it were deliverable.

### 2. CRT3 is inert, and its shape is undersized for structure 107

CRT3's 22-byte value region decodes coherently as `phsActivePhases` (field 0)
followed by `phsAuthorityID` (field 1), but the record carries a single trailing
state byte and its value is `0x00`. `Decode-Style7Replication.field_states`
reads that stream as 2 bits per field (`1` = present, `2` = absent), so `0x00`
means *four fields absent* — contradicting the two values that are physically
present — and `phsPlayerPhaseData` (candidate structure 107) declares 5 fields,
which needs 10 state bits and therefore 2 bytes. Byte-exact layout, confirmed by
`read_object_record` walking the record to EOF at offset 0x37:

```text
0x1B field_version 5   0x1C style 7   0x1D field_size 25
0x1E structure 107     0x1F inner_size 22
0x20..0x35 values (22) 0x36 state byte 0x00
```

`field_size` reconciles exactly as `1 + 1 + 22 + 1 = 25`, so the one-byte state
region is genuinely part of this record and is genuinely too small for a
five-field structure. The phase entry that fix #1 produces comes from the CRT1
child alone and does not depend on CRT3. Setting `phsInstanceAllowAll`
(`0x40000018B68A60B2`, the only `*AllowAll` field in any of the 107 session
structures) is therefore not reachable through the current CRT3 shape, and per
finding 1 it is not the fix anyway.

The counterpart name that `phsParticipantClassMethods.GetCharacterAllowInstances`
reads, `phsDebugInstanceAllowAll`, appears in no structure of the session schema
at all, so a properly rebuilt CRT3 would first have to settle whether
`phsPlayerPhaseData` carries a sixth field that the current reconstruction
misses.

### Remaining work

Unchanged, and not a phase-system fix: the `INSTANCE_GATEWAY`
(`TriggerInstance`, `0xDFFE87FD`) and `INSTANCE_REGION` static instances are
never instantiated client-side, because the emulator has no dynamic
area-object/room streaming. That single missing subsystem accounts for the
doorway, the missing enemies and the inert boundaries. It should be implemented
starting with the player's current room.


## The engine-trigger question, corrected — 2026-09-28

The earlier conclusion recorded in this file — that the engine trigger is not
present client-side — was drawn from a probe that was invalid three independent
ways, and it is withdrawn.

### What the captured session schema actually proves

Decoding the full compact schema out of production CRT1 yields 104 structures
whose base classes are all GOM **game** classes:

```text
chrNonPlayerCharacter x17   effEffect x11   dynPlaceable x9   plcPlaceable x8
dynVisual x2  dynVisualState x2  itmItem x2  ...  hydTriggerEntity x1
```

`TriggerInstance` (`0xDFFE87FD`) is **not declared**, and neither is any room,
area or engine-node class; across the whole schema the only trigger class is
`hydTriggerEntity`. So engine triggers really are never delivered by the
replication stream — but that is a statement about the *wire*, not about the
client, and it does not show the client lacks them.

Three counterweights, all from the extracts:

- `chrCharacter._createPreloadTrigger` builds an engine trigger node on the
  client from a prop bucket (`$STATIC.GetHardcodedAssetPath(hcaKey_engineTrigger)`
  plus `CreateInstanceFromPropBucket` and `GlomClass`) and sets exactly the
  property bag `_AttachGatewayTrigger` later reads.
- `phsoracle.GetTriggersInPhase` enumerates triggers by phase and
  `ShouldDisplayPhaseTooltip` tests `utlNode:isTrigger` plus `TriggerClassType`,
  which only works if the engine holds the area's trigger set.
- `Scriptdef.listdump.csv` (867 definitions) contains **no** area, room,
  streaming or engine-trigger script class, so no script-side piece is missing
  from the emulator that would obviously account for this.

### The probe was invalid three ways

1. Its "fresh" node ID `0x1AC688C980` is a live CRT1 object (record 4), so the
   transaction was an update and `OnReplicationNodeCreate` never re-ran. A
   node/parent scan cannot see this; raw bytes are required.
2. It reused CRT11's stream id `0x001B5023`, which the startup bundle had
   already delivered. Stream ids are unique per transaction in the capture
   (`0x001B5012` for CRT1 stepping to `0x001B502D` for CRT17), so the client can
   discard the resend as a duplicate stream.
3. Re-sending an existing instance node cannot re-fire the create handler
   regardless.

Note this also corrects an intermediate finding of the same session: a scan for
node/parent *record* fields reports `0x1AC688C980` as unused, because parsing
CRT1's object list needs the schema-aware offset. Only the raw-byte scan sees
the true picture.

### The regenerated probe is proven, not asserted

`Diagnostics/Generate-PhaseInstanceDuplicate.py` derives both identifiers and
refuses to write unless the proofs pass:

```text
free node ID 0x0000001AC688C981 (20 .acrt files scanned, zero references)
CRT1: object 3 of 54 at 0xB52B, record 87 bytes
stream 0x001B502E (next id after the capture's 0x001B5012..0x001B502D range)
node 0x1AC688C97E -> 0x1AC688C981
verified: unreferenced by 20 other .acrt files, so this is a create
```

The source is CRT1's own record, not the `-1.11.acrt` fixture the first version
pointed at: CRT1 carries all 54 phase instances and its object list sits after
the compact schema, so finding the record needs the schema-aware offset
(`8 + decode_schema_bytes(CRT1[8:])`). Framing still comes from a non-CRT1
fixture, because CRT1's bytes 4..7 are the schema length.

Output verification — 97 bytes, sha256 `6752695e7bcca413…`:

```text
flags=1 count=1   node=0x1AC688C981  tmpl=0xE000E8E230304F84  struct=3
walk end=0x61 of 0x61 -> EXACT
source 87 bytes vs payload 87 bytes; differing offsets [5]   (the node ID only)
```

Re-running the generator reproduces the same sha256, and `CapturedCharacterRemap`
only rewrites `0x4000010E218A839C`, so it leaves the new node untouched.

### How to run it

The launcher already points `SWTOR_CRT_OVERRIDE_DIRECTORY` at the generated
directory. Give the interval a value and the probe fires once, 25 s after world
entry:

```text
set SWTOR_PHASE_INSTANCE_RETRY=40
```

Observable: if the client holds the `INSTANCE_GATEWAY` trigger, the create
handler attaches a gateway and a `phsGatewayFx` portal appears at the phase
door. Nothing appearing means the trigger is absent client-side and must come
from server-side area-object streaming.

The free behavioural cross-check that needs no probe at all: walk over a
replicated Hydra trigger — the Gnarls camp has five, including codex triggers at
`(-8.412, -2.682, -99.525)` and `(-9.980, -3.169, -92.293)` — and see whether a
Codex entry is granted. Replicated triggers working end-to-end there would
localise the failure to engine triggers specifically.

