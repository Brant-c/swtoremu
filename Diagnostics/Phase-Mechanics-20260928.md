# How the SWTOR phase system actually works — 2026-09-28

Source-grounded reading of the client's phase scripts. Everything below is taken
from the `_JPEXTRACT` class methods, not inferred from packet behaviour.

## 1. Phase membership is a child node, not a flag

There is no "player is in phase X" field. Membership is structural:

```text
phsPhaseInfo.GetPhasedInstance()   -> GetParentOfNode(Me)
phsPhaseInfo.GetPhaseInfoOwner()   -> Me.phsPhaseInfoOwner        (who leads the phase)
phsPhaseInfo.GetPhaseAuthorityID() -> Me.phsPhaseInfoOwner
pc.GetPhaseInfo()                  -> the player character's phsPhaseInfo child
```

So "the player is in a phase" means exactly: the player character node has a
`phsPhaseInfo` child whose **parent node** is the `phsPhasedInstance`. That is
why `DeterminePhaseEligibility` can decide exit from it directly:

```text
phsClassPhasedInstance.DeterminePhaseEligibility()
  if pc2.GetPhasedInstance() == Me
    out = phsCanExit
    UpdateGatewayStateIfInCombat(pc2, &out)
    Me.UpdateGatewayStateIfInRaidGroup(pc2, &out)
    return out
```

## 2. The banner you remember

`phsPhasedInstanceClassMethods.UpdateGuiForPhase()` is the indicator:

```text
if node2 = pc.GetPhaseInfo() != None
  enum1 = Me.GetPhaseType()
  v43   = node2.IsQuestProgressionAllowed()
  str2  = node2.GetPhaseAuthorityName()
  list1 += str2
else
  list1 += ""

str4 = "(Owner: <<1>>)"                    // STR_GUI_CHAT | 4
str7 = "Entering Story Area"               // STR_GUI_CHAT | STR_PHASE_AREA_TEXT

$GUI_API.getApi().BannerMessageTwoExWithSize(str7, YELLOW, 25, str4, YELLOW, 20)
$CHAT.ChatPlayerLocalized_Old(chatChannel_SystemFeedback, str7 + " " + str4)
$GUI_API.getApi().setGuiPhaseData(enum1, str2, "", v43)
```

The exit counterpart, `UpdateGuiExitingPhase()`:

```text
if Me.phsMapNote != 0
  str3 = "Leaving <<1>>"   // $MAPNOTE.getMapNoteDisplayString(Me.phsMapNote)
  $GUI_API.getApi().systemMessage(str3)
setGuiPhaseData(phsTypeClass, "", "", false)
```

Note `Me.phsMapNote` and the prototype field `phsExitMapNoteID =
4611686069191632234` for the master-retreat instance: the "Leaving ..." text is
built from the phase's own map note.

The **concrete** class chains to the base and then adds a group-only path, so a
solo player only ever gets the base behaviour:

```text
phsClassPhasedInstance.UpdateGuiForPhase()
  UpdateGuiForPhase = HM.PrepareCallBaseMethod2(26, Me, &_callFrame)   // base, always
  UpdateGuiForPhase(_callFrame)
  ...
  else if pc2.IsInGroup()        // <- concrete class only fires when grouped
    ... setGuiPhaseData(...)
```

Both branches need `pc.GetPhaseInfo() != None`. **Nothing else.**

## 3. It runs exactly once, at the local player character's create

```text
chrCharacter.Replication_Create(Me, a1)
  var pc2 = GetPlayerCharacterNode()
  if Me == pc2                                  // local player only
    Me.CachePlayerTitles()
    call event Me:OnPlayerCharacterNodeReady    // <-- fires the phase UI update
    $BASECLIENT._SetGameState(GAMESTATE_WithinArea)
    $BASECLIENT.RequestWorldFadeIn()
    ...
  if Me != pc2                                  // other players only
    Me["Render"] = Me.chrPlayerLoaded
```

```text
phsParticipant.OnPlayerCharacterNodeReady(Me)
  $PHASE.OnPhasedInstanceUpdated()
```

```text
phsoracle.OnPhasedInstanceUpdated()
  var node6 = pc2.GetPhaseInfo()
  if node6 != None
    var node7 = node6.GetPhasedInstance()
    int2 = node7.GetInstanceNameID()
    node6.RefreshGui()
  if Me.phsCurrentInstanceNameID == int2
    return                                      // <-- no change, no GUI call
  ...
  Me.phsCurrentInstanceNameID = int2
  if node7 != None
    node7.UpdateGuiForPhase()                   // banner ON
  else
    node2.UpdateGuiExitingPhase()               // banner OFF
```

`phsCurrentInstanceNameID` starts at 0. So if the player has **no** phase-info
child at that moment, `int2` stays 0, the comparison `0 == 0` holds and the
method returns immediately. `UpdateGuiForPhase` is never called, and nothing
re-fires it later in the session.

**Therefore: the banner appears only if the player's `phsPhaseInfo` child already
exists when the local player character node is created.**


## 4. Which transaction creates the local player character

Decoding every `.acrt` for the character's node `0x4000010E218A839C`:

```text
prod  CRT1   bound=44001  objs=53  INSTANCE   i=3  flags=0x6A
prod  CRT2   bound=0      objs=85  PLAYER     i=82 flags=0xAA  class=0x400000000056B3C1
                                                              structure=26 chrPlayerCharacter  <- CREATE
prod  CRT4   bound=0      objs=11  PLAYER     i=0  flags=0x09
                                   PHASEINFO  i=1  flags=0xAA  parent=0x1AC688C97E
prod  CRT5..17                    PLAYER     i=0  flags=0x09   (updates only)

override CRT11  objs=3  INSTANCE i=0 flags=0x6A
                        PHASEINFO i=1 flags=0xAA parent=0x1AC688C97E
                        PLAYER     i=2 flags=0x09
```

`flags 0xAA` = class + parent + value + metadata, i.e. a create. `0x09` =
value + metadata only, i.e. an update. So the local player character is created
by **CRT2**, and the phase-info child arrives **after** it in both
configurations (CRT4 in production, CRT11 in the candidate).

**Prediction: the banner is absent in both.** That matches the current run. If
the banner was visible in an earlier run, that run must have had the phase-info
child in place *before* the player create, i.e. the child delivered in CRT1 or
in the world-side startup ahead of CRT2.

## 5. The player's create record also carries the position

Decoding the CRT2 player record:

```text
  1  character_position = vec(-64.8741, -6.90622, -127.671)
  2  character_rotation = vec(0, -90.0002, 0)
  4  chrXpNeeded        = 535
  9  staMobility        = enum=2
 10  chrGender          = enum=2
 11  chrScale           = 1
 12  chrMeleeDistance   = 0.1
 15  staWeaponState     = enum=2
 16  ablUserClearCasting= -1
 25  phsPhase           = 1
 26  eqpEquipment       = ...
```

`AreaStartupBundle` sends in this order:

```text
line 47   AreaTeleportCharacter(...)              <- SWTOR_SPAWN_POSITION lands here
line 55   AreaClientReplicationTransaction(2)     <- sets character_position back
```

So the teleport is applied and then **immediately overwritten** by the player's
own create record. That is why the spawn override produced identical behaviour:
it was never observable. `phsPhase = 1` is the player's phase-group field, not
the instance identity.

## 6. The gateway volume is built client-side

```text
phsPhasedInstance.OnReplicationNodeCreate(Me, a1)
  $PHASE.phsActiveInstances[Me.phsNameID] = Me
  list1 = GetTriggersByType(4)
  foreach cur in list1
    if ComputeStableIdentifier(cur["TriggerParam"]) == Me.phsNameID
      add back cur to Me.phsGatewayList
      $PHASE._AttachGatewayTrigger(Me, HM.CopyConstructNodeRef(7, cur))
```

```text
phsoracle._InitGatewayPropBucket()
  CreatePropBucket("Phase Gateway Trigger Volumes")
  Me.phsGatewaySpec = AddAssetSpecToPropBucket(..., $STATIC.GetHardcodedAssetPath(hcaKey_engineTrigger))

phsoracle._AttachGatewayTrigger(Me, a1, a2)
  id1 = CreateInstanceFromPropBucket("Phase Gateway Trigger Volumes", Me.phsGatewaySpec)
  SetParentOfNode(node, a1)
  node["Name"]         = a2["TriggerParam"]
  node["TriggerParam"] = a2["TriggerParam"]
  node["Width"/"Height"/"Depth"] = a2[...]
  node["Position"/"Rotation"/"Scale"] = a2[...]
  node["Enter"]=true  node["Leave"]=false  node["PlayerSensitive"]=true
  node["Active"]=true  node["Disappear"]=false  node["NPCSensitive"]=false
  GlomClass("phsGateway", node)
  ActivateInstance(id2, "")
```

Two consequences worth stating plainly:

1. The walkable gateway volume is a **new client-side node** created from a
   client prop bucket and the hardcoded engine-trigger asset. The static
   `INSTANCE_GATEWAY` trigger is used **only as a source of parameters**
   (`TriggerParam`, `Width`, `Height`, `Depth`, `Position`, `Rotation`,
   `Scale`).
2. So the single missing input is a type-4 trigger node whose `TriggerParam`
   hashes to `phsNameID`. Everything downstream is client-side.

`phsGateway.TriggerEnter` then resolves
`$PHASE.GetPhasedInstanceNode(ComputeStableIdentifier(Me["TriggerParam"]))`,
which is only populated by `phsActiveInstances` from the method above.

## 7. What this means for the current state

| Symptom | Cause |
|---|---|
| No phase banner | The phase-info child is created after the player create, so `OnPhasedInstanceUpdated` returns early and never runs again. |
| Identical behaviour from the spawn override | CRT2's `character_position` overwrites the teleport sent moments earlier. |
| Doorway inert | No type-4 `INSTANCE_GATEWAY` trigger is ever replicated, so `_AttachGatewayTrigger` cannot run and no `phsGateway` node exists. |

These are three independent defects, and the first two are pure ordering.

## 8. Ordered next steps (not yet applied)

1. **Deliver the phase-info child before the player create.** Put `PHASEINFO`
   (and its parent instance) into CRT1, which is sent before CRT2. This should
   restore the banner and make `pc.GetPhasedInstance()` valid, which is a
   precondition for `phsCanExit`.
2. **Make the spawn override observable.** Either send `AreaTeleportCharacter`
   after CRT2, or rewrite `character_position` / `character_rotation` inside the
   CRT2 record. Otherwise any placement experiment is silently discarded.
3. **Then** revisit the doorway. The trigger is still missing, so this is
   necessary but not sufficient. Confirm the banner first: it is the cheapest
   proof that the client considers the player to be inside the phase.

## 9. Step 1 applied — 2026-09-28

`Generate-MatchedPhaseCrtCandidate.py` now builds the arrangement from section 8
item 1. Verified output:

```text
candidate CRT1: bytes=57636 listStart=44215 flags=1 objects=54 walkToEOF=True
  idx 3 node=0x1AC688C97E struct=phsClassPhasedInstance  parent=0x0
  idx 4 node=0x1AC6F6DC1F struct=phsClassPhaseInfo       parent=0x1AC688C97E
inserted child == production CRT4 child : True  (48 bytes)
```

- The phase instance keeps its original position at index 3 and the captured
  48-byte `phsClassPhaseInfo` record is inserted at index 4, directly after it,
  so both are applied before CRT2 creates the player character.
- The inserted record is byte-identical to the one production CRT4 delivered.
- CRT4's object count drops 11 -> 10; the record is no longer duplicated.
- CRT11 is no longer overridden, and the generator deletes a stale CRT11
  override from its output directory so the superseded arrangement cannot linger.
- No structure definition was fabricated: CRT1's captured table already contains
  structure 3 (`phsClassPhasedInstance`) and structure 75 (`phsClassPhaseInfo`).
- Production `AreaServer/CRT` fixtures were not touched.

CRT1 is now `ADC5A0CB3468D827821EED4D6B9773A83624548F34CFE8E38231BC3371A39B3C`;
CRT3 and CRT4 are unchanged.

### Two probe defects this uncovered

The production record at CRT1 index 5 is node `0x1AC688C980` — the exact ID the
retired duplicate-create probe used as its "fresh" node. That probe therefore
sent an update to a live node rather than a create, so even the corrected probe
never forced `OnReplicationNodeCreate` to re-run. There were two independent
reasons it was inconclusive: the same-ID resend, and this ID collision. The
generator's docstring is annotated so the file is not reused.

### Expected observable result

A yellow banner **"Entering Story Area"** with **"(Owner: <character name>)"**,
plus the same text on the SystemFeedback chat channel. The child's
`phsPhaseInfoOwner` is `...839C`, which `CapturedCharacterRemap` rewrites to the
real character `...839B`, so `GetPhaseInfoOwner() == player`,
`GetPhaseAuthorityName()` resolves and `IsQuestProgressionAllowed()` is true.

If the banner returns, the client genuinely considers the player to be inside the
phase, `pc.GetPhasedInstance()` becomes valid and `phsCanExit` is reachable. If
it does not, this ordering model is wrong and the next thing to find is a second
caller of the phase GUI update; no second caller appears in the extracts, but the
extracts are not the whole client.


## 5. The boundary volumes are released only by `phsCanExit`

`phsPhasedInstanceClassMethods.GetInstanceGatewayState` fills a fourth
out-parameter that is the phase boundary's collision flag:

| eligibility | `*o2` portal FX | `*o4` collidable |
| --- | --- | --- |
| `phsCannotEnter` | `fxInstancePortalRed` | 1 |
| `phsOpsGroupDisallowed` | `fxInstancePortalRed` | 1 |
| **`phsCanExit`** | **`fxInstancePortalGreen`** | ***never assigned*** |
| `phsInCombatCannotOwn` | `fxInstancePortalGreen` | 1 |
| `phsInCombatCannotJoin` | `fxInstancePortalBlue` | 1 |
| anything else | `fxInstancePortalRed` | 1 |

`phsCanExit` is the only state that leaves the boundary passable. That
out-param is consumed by `phsoracle._SetGatewayState`:

```text
node2.GetInstanceGatewayState(node2.DeterminePhaseEligibility(), &enum1, &enum2, &bool2)
$PHASE._SetGatewayState(node2, enum1, enum2, bool2)
```

```text
_SetGatewayState(a1 = instance, a2, a3, a4):
  v41 = a4
  if $BASECLIENT._GetInstanceID() == 0 or pc.GetCharacterAllowInstances()
    v41 = 0
  ...
  if ((phsCollisionStatePerInstance[a1] ^ v41) & 1) != 0      // change gate
    foreach key in a1.phsPhasedInstanceToTrigger
      phsPhasedInstanceToTrigger[key]["Collidable"] = v41
    phsCollisionStatePerInstance[a1] = v41
```

So the phase boundary consists of the `INSTANCE_REGION` (type 3) triggers that
`phsPhasedInstance.OnReplicationNodeCreate` cached in
`phsPhasedInstanceToTrigger`, and this is the only code in the client that ever
writes their `Collidable` property.

`UpdateGatewayForInstance` is gated on `node2.RequiresGatewayUpdate()`, whose
base implementation returns an unconditional `true` and which
`phsClassPhasedInstance` does not override. `_SetGatewayState` therefore always
runs whenever `UpdateGatewayForInstance(instanceID)` is called, including from
the enter branch of `OnPhasedInstanceUpdated`.

### Consequence for the delivery-order fix

Because the phase-info child is now delivered in CRT1 *before* the player
character is created, the first evaluation already sees
`pc.GetPhasedInstance() == instance`, i.e. `phsCanExit`, i.e. `a4 = 0`. The
cached collision state starts at `0`, so the change gate evaluates
`(0 ^ 0) & 1 = 0` and **skips the write**; the region volumes keep their
authored `Collidable`. The real game instead evaluates while the player is
*outside* the phase (`phsCanOwn`/`phsCanJoin`, which set `*o4 = 1`, recording a
cached `1`), then transitions into the phase, and only that transition makes the
gate fire and clear `Collidable`.

**The invisible wall at the doorway is therefore not the phase boundary.**
Either the type-3 `INSTANCE_REGION` volumes were never created — in which case
there is nothing for the script to block with — or they exist and were left
passable. Both cases leave the wall unexplained by the phase scripts, so it is
world content: the edge of the loaded room set at the interior/exterior
transition. That is the same root cause as the missing enemies, and it puts the
doorway, the enemies and the inert boundaries behind one missing subsystem.

