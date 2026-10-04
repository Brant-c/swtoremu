# Room Streaming — Execution Plan (self-contained, for a fresh session)

> Goal: let a level-1 Jedi Knight walk OUT of the Masters' Retreat phase (Tython)
> into the exterior room `gnarls_new`. Right now an invisible wall at world
> **X ≈ -62.92** confines them just past the doorway.

---

## 0. The one-sentence root cause

The wall is the **room boundary** (an `engine/portal.p` at the doorway). The
client only loads a destination room's collision when the **server streams that
room's object set** as a `GomUpdate`/CRT. The emulator never does this. Build and
send the room-load stream.

The problem is **server-initiated room streaming**, not a missing client request.
The client *reports* its position (`CMsg61116AD5`); the real HeroEngine server
reads that, decides the player entered a new room, and pushes that room's
objects. The emulator swallows the position reports (correct) but never pushes
the room objects (the bug).

---

## 1. Already done / proven — do NOT redo

- Phase **entry** works (banner, owner line, phasing popup). Startup bundle is correct.
- Phase **exit destroy** is delivered AND applied end-to-end (proven with client hooks,
  `Diagnostics/Handover-20260928.md` §20, §24–§26).
- Abilities, movement, spawn all work.

## 1b. Proven DEAD ENDS — do NOT retry

1. **`_Room_Activate` RPC** → server-only. Selector correct (`class 0x2B7E4202` +
   `method 0x5086FADF`), but the client answered `unable to call function as server`.
2. **Re-sending awareness (`.aaw`)** → non-idempotent creation batches; client answers
   `Character already exists`.
3. **The three "area poll" messages** `0xCCACB51D`, `0x7CB9A193`, `0xC26464A9` →
   fire-and-forget sync (client SEND code exists, but **zero** client receive handlers).
4. **Readiness poll** `0xF5F540F2` (wire `C7 71 C3 79 12 F2 40 F5 F5`) → a periodic
   status notification, not a request.

The wall is **not** the phase boundary: `INSTANCE_REGION` triggers are
`ExistsOn: Server` / `Collidable: false`, so they never reach the client, and
`phsPhaseInfo.OnReplicationNodeDestroy` removes membership without calling the
only UI-clearing path (`OnPhasedInstanceUpdated`).

---

## 2. Key coordinates & IDs

World space. Asset coords from `instances.txt` are ÷10 with Y/Z swapped:
`asset(X,Y,Z) → world(X, Z/10→Y, Y/10→Z)` = `world = (assetX/10, assetZ/10, assetY/10)`.
Example: asset `(-636,-1269,-67)` → world `(-63.6, -6.7, -126.9)`.

| thing | value |
|---|---|
| spawn (inside retreat) | `(-64.87, -6.9, -127.67)` |
| gateway / portal (doorway) | world `X = -63.6` |
| **the wall** | world `X = -62.92` |
| area | `tython_blockout`, areaID `4611686019869492753`, areaCode `1` |
| room | `gnarls_new`, room id `4611686024647056040` |
| character node | `0x4000010E218A839B` |
| phase-info child node | `0x1AC6F6DC1F` (parent `0x1AC688C97E`) |
| destroy stream id | `0x001B502E` |
| `_BaseClient` class hash | `0x2B7E4202` |
| `_Room_Activate` method hash | `0x5086FADF` (server-only, unused) |

---

## 3. The 4 steps

### Step 1 — Find the "room" node type (the linchpin)
The room is almost certainly a replicated **node** whose creation makes the client
pull the room's static geometry from `gnarls_new.dat`. We need its
**ClassID / TemplateID / ParentNodeID** (the IDs that go into a `GomUpdateObject`).

Look in:
- `Diagnostics/swtor-disasm.txt` — search for room / portal / hydObject native code.
  Addresses are `image base 0x00400000` + RVA (e.g. `0x0064ED70`).
- `Tools/tor_tools/GomLib/bin/Debug/gom_type_names.xml` — already spotted:
  `plcRoom` (`4611686029370470004`), `RoomBoundName` (`4611686029370470044`),
  `vehRoom` (`4611686031029979983`), `hydObjectType` (`4611686031079276726`),
  `hydObjectSearchScope` (`4611686031022477486`).
- `_JPEXTRACT/Scriptdef.listdump.csv` (class→hash), `_JPEXTRACT/_BaseClient.txt` etc.

Deliverable: the concrete class/template/parent IDs (packed u64s) of one "room" node.

### Step 1 — RESOLVED: there is no client-callable room RPC
`_BaseClientClassMethods.txt` shows `_Room_Activate(Me, a1, a2, a3, a4)` whose body is
literally `Me._SetRoomName(a4)` — the actual room streaming is done by the **native
engine** on the server side, not by script. It answers `unable to call function as
server`. `_Area_Load/_Area_Preload/_Area_Unload` are AREA (not room) methods. So the
room load can only be reproduced by replaying the engine's **GomUpdate object stream**.

### Step 2 — RESOLVED: the stream's object IDs are NOT in instances.txt
`instances.txt` rows carry: instance node id (`0x40…`, e.g. heightmap
`4611686019889500324`), asset id, asset name, and X/Y/Z coords. The room stream
(CRT 1.2, 85 objects) creates `0xE000…` "world object" ids (e.g. `0xE0004EA602373870`)
with per-object class/template/parent and a packed field-data blob. The
`0x40…` instance id → `0xE000…` world-object id mapping and the field schema live in
CRT 1.1's ~44k-entry contract block and are **not derivable from instances.txt alone**.

### Step 3 — the byte format (fully mapped; data is the gap)
```
.acrt  = StreamID(u32) + schema-count(u32, =0) + flags(u8) + [object list] + [removed list]
object = packed NodeID + flags(u8: 0x80 class / 0x40 template / 0x20 parent / 0x10 lists / 0x08 field-data)
         + [class/template/parent] + field-data(version, format, count, bytes)
```
Packed = `0xC7+len` prefix then big-endian (0xCC=5B, 0xCF=8B). CRT 1.2's container is
`0x1AC6F6DBD7` (class `0x40000002F8C347F1`, parent `0x4000010E218A839C`) with 28
children `0x1AC6F6DBD8..0x1AC6F6DC0C`, each holding 2 `0xE000…` world objects.

### Step 4 — DONE (drop-in emission point)
`PhaseExit.SendRoomStream(client)` fires at the doorway crossing, after the destroy.
It replays `AreaServer/CRT/{area}-{areaID}-{areaCode}.18.acrt` (or
`SWTOR_CRT_OVERRIDE_DIRECTORY`) via `AreaClientReplicationTransaction`, with character
remap applied. `CRT.Has()` guards against emitting an empty stream when the fixture is
absent (logs a clear warning). StreamID must be `0x001B502F`.

## 3b. THE BLOCKER (why construction is stalled, not the format)

A correct room stream needs, per room: the `0xE000…` world-object ids, their
class/template ids, and their packed field data. None of that is in `instances.txt`.
It is either (a) captured live, or (b) reverse-engineered from the `.dat` + CRT 1.1's
contract block — a multi-week effort. **Do not** emit a hand-rolled stream: wrong ids
crash the client (same class of crash as the reverted awareness re-send).

## 3c. How to capture the room stream (the intended fix)

1. On a live/retail-adjacent capture rig, log the outbound area replication payloads
   for `tython_blockout` while a character walks the retreat doorway into `gnarls_new`.
2. The payload is `AreaClientReplicationTransaction` (opcode `0x0D446E80`): 4-byte
   MessageID, then `WriteAreaComponent()`, then the `.acrt` body. Save the body only.
3. Set its first 4 bytes (StreamID) to `2F 50 1B 00` and drop it as
   `AreaServer/CRT/tython_blockout-4611686019869492753-1.18.acrt` (or into
   `SWTOR_CRT_OVERRIDE_DIRECTORY`). No code change needed beyond what is already in place.

## 3d. What changed this session
- `SharpServer/AreaServer/PhaseExit.cs` — `SendRoomStream` + `RoomStreamCrtID`(18) /
  `RoomStreamID`(0x001B502F); doorway block now calls it.
- `SharpServer/AreaServer/CRT.cs` — added `Has()` existence check.
- Server builds clean (`dotnet build SharpServer\NexusToRServer.csproj -c Debug -f net48`).

## 3e. RE findings (reverse-engineering session, run 2)

Tools written: `Diagnostics/decode-acrt.py` (GomUpdate/`.acrt` decoder, validated on CRT 1.2),
`Diagnostics/parse-dat.py` (Room Specification `.dat` parser).

1. **Wire format confirmed** (decoded all 85 objects of CRT 1.2 cleanly):
   `.acrt = StreamID(u32) + schema-count(u32) + flags(u8) + object-list + removed-list`;
   object = `packed NodeID + flags(0x80 class/0x40 template/0x20 parent/0x10 lists/0x08 field)`
   `+ [class/template/parent] + field-data(version, format, count, bytes)`.
   Packed = `<0xC0` 1 byte, else `0xC7+len` + big-endian.

2. **The startup bundle (CRT 1-17) is NOT room streaming.** CRT 1.2 (85 objects) is the
   player's container set: `ablContainer`(0x40000002F8C347F1), `effContainer`, `invContainer`,
   `eqpContainer`, `vndBuybackContainer`, `bnkContainer`, `trdContainer`, `malMailContainer`,
   `qckContainer` — ability/inventory/equipment slots. The `0xE000…` values are **template
   (prototype) ids**, e.g. ability prototypes, not world-object ids. So there is **no
   captured room-load stream anywhere**; it is a separate, uncaptured native operation.

3. **`gnarls_new.dat` is a readable text "Room Specification"** (201,516 lines):
   `[INSTANCES]` = 5995 instances, each `instanceID=assetID` + `.Position/.Rotation/.Scale/`
   `.ParentInstance/.PortalTag/.Tag/.movable/...`; then `[VISIBLE]` (8 rooms) and
   `[SETTINGS]` (`RoomGUID=4611686024647056040`).

4. **The room's dynamic objects are tiny** — exactly 2 portals (`PortalTag=true`) and 1
   server-only trigger (`Tag=tyt_jedi_consular_masters_retreat`):
   - portal 4611686031438163603 asset 4611686020816413231 @ (28.3,-5.1,-87.1) rot(0,180,0)   (→ academy_main)
   - portal 4611686037462170005 asset 4611686025199172721 @ (-61.7,-8.5,-130.5) rot(0,45,0)  (→ the retreat doorway)
   - trigger 4611686127009745042 asset 4611686019869492758 (consular INSTANCE_REGION, server-only)
   Static geometry (rocks/cover) is client disk-loaded; only portals/triggers replicate.

## 3g. Correction to §3b (the "0xE000 blocker" was a misread) — 2026-09-29

§3b stalled construction because "the room stream needs `0xE000…` world-object ids
not derivable from instances.txt". That conclusion came from treating **CRT 1.2** as a
room-stream example. CRT 1.2 is **not** a room stream — it is the player's container
set (`ablContainer`/`effContainer`/`invContainer`/…, 85 objects, the `0xE000…` values
are ability/container **templates**). There is still no captured room stream, but the
**room's own data is available in `gnarls_new.dat`** and uses `0x40…` ids:

- exactly **2 portals** (`PortalTag=true`) + **1 server-only trigger**:
  - portal `4611686037462170005` asset `4611686025199172721` @ (-61.7,-8.5,-130.5) rot(0,45,0)  → the retreat doorway
  - portal `4611686031438163603` asset `4611686020816413231` @ (28.3,-5.1,-87.1) rot(0,180,0)  → academy_main
  - trigger `4611686127009745042` (consular INSTANCE_REGION, server-only, not streamed)
- so a room-load stream is ~2 objects, not 6000.

Also note: the room stream may be delivered as **`AreaAwarenessEntered`** (a `.aaw`,
opcode `0xA1D9E226`), not `AreaClientReplicationTransaction` (`.acrt`, `0x0D446E80`).
Both carry a GomUpdate; awareness is "nodes entered your awareness" (new room objects),
replication is "apply this update" (state change). `SendRoomStream` currently emits CRT
18 (`.acrt`). If a hand-rolled `.acrt` is rejected, try the same GomUpdate as a new
`.aaw` awareness set instead.

Still unknown before construction can be tested: the portal object's **class id** and
whether its stream **template** is the `0x40…` asset id or a `0xE000…` glom, plus the
exact Position/Rotation/Scale field encoding.

## 3h. Schema decoded (the "44k block" is 44k BYTES, 104 class contracts) — 2026-09-29

CRT 1.1's `schema bound` (u32 at offset 4) is `0xABE1 = 44001` **bytes**, not 44k
entries. After `StreamID(u32)` + `size(u32)` + a leading packed `104` (= the contract
count) there are exactly **104 `StreamContract`** records. Each = `ContractID(packed) +
BaseClassID(packed) + glommed-classes(count+list) + fields(count + [fieldID(packed) +
sub-count + [type/class/contract-id]…])`. Tools: `Diagnostics/decode-schema2.py`,
`lookup-classes.py`, `dump-contract.py`.

The 104 base classes (via `gom_type_names.xml`) are the **startup** set — player, NPC,
effect, containers, placeables, phase, conversation, etc. **There is no portal or room
class**: the engine `portal.p` is not a GOM class, so it is not represented in the
startup schema.

Placeable classes carry the room/transform fields (type code from `HeroTypes.cs`):
- `plcPlaceable` 0x400000027669D5F2, `dynPlaceable` 0x40000004950F6070
  - `plcPosition`  0x400000027669D5EE : Vector3 (0x12 = 3 floats)
  - `plcRotation`  0x400000027669D5EF : Vector3 (0x12)
  - `plcRoom`      0x400000028C422E74 : String (0x06)
  - `plcModelAssetSpec` 0x400000027669D5F4 : String (0x06)
- `hydTriggerEntity` 0x40000003986E8671 (the room trigger class)

HeroTypes codes: 1=Id, 2=Integer, 3=Boolean, 4=Float, 5=Enum, 6=String, 7=List,
8=LookupList, 9=Class, 0xE=ScriptRef, 0xF=NodeRef, 0x12=Vector3, 0x13=Guid.

Hack pack (`AreaServer/HackPacks/*.dat`, 560 bytes = 35 quads of 4×u32) is the room
connectivity graph for 15 rooms (quad[0].x=15). Sent at startup; not the room-load
signal itself.

**Bottom line:** the wire format, schema, field types and room data are now fully mapped.
The one thing still not reproduced is the native "activate room gnarls_new" operation —
it is neither the captured awareness sets (non-idempotent creation) nor the startup CRT
streams, and it is not a script RPC. Remaining: capture it live, or reverse the native
room-change primitive from the client disassembly.

## 3i. Gateway triggers are server-side; room load is native — 2026-09-29

`gnarls_new.dat` carries the doorway triggers (asset `\engine\trigger.trg`
0x4000000193AB7EF1 = 4611686019869492758), all `ExistsOn=Server` / `Collidable=false`:
- `INSTANCE_GATEWAY` `tyt_jedi_knight_masters_retreat` @ (-63.62,-6.73,-126.88)  (the doorway)
- `INSTANCE_GATEWAY` `tyt_jedi_consular_masters_retreat` @ (-58.10,-6.74,-132.40)
- `INSTANCE_REGION` (knight & consular), plus `HYDRA`/`GENERIC`/`EXHAUSTION_VOLUME` triggers.
These never reach the client, so `_AttachGatewayTrigger` cannot run from them. The doorway
wall (X=-62.92) is the room boundary; it opens only when the client loads gnarls_new's
collision, which is a server-initiated native operation.

**Decisive, zero-code experiment** (settles client-position vs server-signal): spawn the
character past the wall and see whether gnarls_new's floor loads. `SWTOR_SPAWN_POSITION`
is applied via `AreaTeleportCharacter` *after* CRT2 (AreaStartupBundle.cs :92), so it is
live. Run with `SWTOR_SPAWN_POSITION=-60,-6.9,-127.67`:
- player stands on a floor → room load is client-position-driven (portal pre-load is the
  gap); the fix is to stream/pre-load the room, not open the portal.
- player falls / nothing renders → room load is server-signal-driven; proceed to
  disassembly of the native room-change primitive.





