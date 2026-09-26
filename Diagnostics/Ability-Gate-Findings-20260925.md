# Ability "not ready yet" gate — 2026-09-25

Read-only analysis. No fixture bytes, packets or client memory were modified to
produce this. Source of truth is the decompiled HeroScript the user exported to
`_JPEXTRACT/ablUserComponentClassMethods.txt` and `_JPEXTRACT/playercharacterclassmethods.txt`.

## The chain

`AbilityValidate` refreshes the cache before validating:

```heroscript
public method AbilityValidate(a1, a2, o3 references Enum effResult) as Boolean
  Me._CacheAbilityUserValues(a2)
  ...
  return _AbilityValidateCached(a1, a2, &o3, false, &classView) & 1
```

`_CacheAbilityUserValues` computes the frozen flag (line 705, 713):

```heroscript
Me.ablUserCacheIsLucid = Me.CharStateIsLucid()
...
if not $CONVERSATION.IsInConversation()
  if Me is kindof chrPlayerCharacter and (not Me.IsRemoteHolo() and Me.IsPlayerLoaded() ? (bool8 = false) : (bool8 = true), bool8)
    bool5 = true
  else
    bool5 = false
  .
else
  bool5 = true
.
Me.ablUserCacheIsFrozen = bool5
```

`_AbilityValidateCached` consumes it (line 251):

```heroscript
if (v133 & 1) != 0 and Me.ablUserCacheIsFrozen
  *o3 = effResultNotReady
  ...
  return false
```

`effResultNotReady` is the "not ready yet" text: `_DisplayAbilityResultMessage`
(line 1930) special-cases exactly that enum and then localizes the failure
string into `ablUserLastResult` / the on-screen message.

So, decompiling the ternary, the gate is:

```
ablUserCacheIsFrozen  ==  isKindOf(chrPlayerCharacter)
                          and ( IsRemoteHolo() or not chrPlayerLoaded )
```

Both inputs matter. `IsPlayerLoaded()` is a direct field read
(`playercharacterclassmethods.txt:1774`).

## Corrected earlier hypothesis

`IsRemoteHolo()` is **not** a client-local flag. It is an effect query
(`playercharacterclassmethods.txt:1777`):

```heroscript
public method IsRemoteHolo() as Boolean
  return HasEffectByAbilitySpec(16141077505857215666)  // abl.player.comport
```

It is backed by `effContainerAblSpecMap`, populated by
`effContainerComponentClassMethods._CacheEffectSpecAndTags` during
`Replication_Create` and maintained by `PostContainerAdd`/`PostContainerRemove`.

Offline check: the Comport ability spec `0xE000A078F4AADCB2` appears in **0 of
the 19** `.acrt`/`.aaw` fixtures, so replicated data should not produce it.
This was not observed live.

## Existing patch verified

`AreaSafeLoginRemoval.ApplyMobilityFreeToFinalCapturedTransaction` writes field
9 (`staMobility`) and field 129 (`chrPlayerLoaded`) into CRT17. Decoding the
merged state stream `DC E7 5D CB 2E 74 80` with
`Diagnostics/Decode-Style7Replication.py` reproduces three present fields:

```
MERGED present: [(9, state=1), (100, state=1), (129, state=1)]
bits used merged: 6 of 7 bytes
```

and `--dump-fields` names them `9 staMobility [Enum]`, `100
modMetaStatComputed_Shared`, `129 chrPlayerLoaded [Boolean]`. The encoding is
correct. Whether the client *applies* it was never observed: the run that
proved movement had `PlayerLoadedWatch: disabled`.

## What the last run could not answer

`Diagnostics/last-compatibility-run.log` line 4: `PlayerLoadedWatch: disabled`.
Searching all four run logs for `RemoteHolo`/`IsPlayerLoaded`/`chrPlayerLoaded`
returns only the server's own "integrated ... chrPlayerLoaded=true" line. No
client-side value was ever observed. Server-side confirmation is not evidence of
client-side state.

## Next run: SWTOR_TRACE_ABILITY_GATE=1

Three schema-resolved fields on the player's own hero node, watched with
read/write data breakpoints in Dr0-Dr3:

| Field | GOM id | Role |
|---|---|---|
| `chrPlayerLoaded` | `0x4000000D5DF53477` | replicated input the CRT17 patch sets |
| `ablUserCacheIsFrozen` | `0x4000003548CCDCC1` | the cached gate result |
| `ablUserCacheIsLucid` | `0x400000002758AA0B` | lucid/stun check |

Each hit logs the value, the RVA, and the return address, so a store from
`_CacheAbilityUserValues` is distinguishable from the load in
`_AbilityValidateCached`. Hits are capped (first 40, then every 2000th) and a
summary prints at teardown.

Outcomes:

- `chrPlayerLoaded=1` and `ablUserCacheIsFrozen=0` at the consuming load — the
  gate is not the blocker; look at the later `IsAbilityReady` /
  `effResultNotReady` paths (cooldown timers in `ablUserCacheTimersRunning`,
  line 272/284).
- `chrPlayerLoaded=0` — the CRT17 write is not landing; the merge reaches a node
  the client is not reading.
- `ablUserCacheIsFrozen=1` with `chrPlayerLoaded=1` — `IsRemoteHolo()` is true,
  i.e. a Comport effect exists client-side.

No other change is authorized until one of these is observed.

## Runtime observation, 18:44 run — the gate IS confirmed, the patch is NOT landing

`SWTOR_TRACE_ABILITY_GATE=1` was already enabled (run script line 69), so this
run answered the question the previous run could not.

```
last-compatibility-run.log:5    AbilityGateWatch: enabled (3 fields)
last-compatibility-run.log:902  chrPlayerLoaded      address=CEA4D176 initial=0
last-compatibility-run.log:903  ablUserCacheIsFrozen address=CEA4CB4A initial=1
last-compatibility-run.log:904  ablUserCacheIsLucid  address=CEA4CB44 initial=1
last-compatibility-run.log:948  state (t=24110): chrPlayerLoaded=0 ablUserCacheIsFrozen=1 ablUserCacheIsLucid=1
last-compatibility-run.log:971  state (t=24359): chrPlayerLoaded=0 ablUserCacheIsFrozen=1 ablUserCacheIsLucid=1
last-compatibility-run.log:977  summary: chrPlayerLoaded      final=0 accesses=0
last-compatibility-run.log:978  summary: ablUserCacheIsFrozen final=1 accesses=0
```

**Outcome 2 from the table above: `chrPlayerLoaded=0` — the CRT17 write is not
landing.** `ablUserCacheIsFrozen=1` and `ablUserCacheIsLucid=1` are exactly
consistent with that (`frozen == IsRemoteHolo() or not chrPlayerLoaded`), so the
"not ready yet" text is fully explained and no second gate is needed to explain
it. The client is behaving correctly; the replicated value never arrives.

This also retires the Jedipedia question: no ability data is needed, because
the client rejects nothing — it is never told the player is loaded.

### The merged transaction was re-verified offline and is byte-correct

Every structural assumption in `ApplyMobilityFreeToFinalCapturedTransaction`
was re-checked against the captured fixtures:

| Assumption | Verification |
|---|---|
| outer/inner size arithmetic | outer = 4 (struct id + inner size) + inner + state bytes. Captured 4+600+4=608=0x260; merged 4+602+7=613=0x265, which is what the patch writes. |
| record framing | outer size packed at 0x16, struct id 0x1A=26, inner size 0x258 at 0x1A, body start 0x1D, state start 0x275, removal list 0x279. All match the fixture. |
| value-body ordering | values must ascend by field index. Patch writes 0x00 (f9 staMobility) at 0x1D, captured field 100, then 0x01 (f129 chrPlayerLoaded) — the correct order. |
| Boolean/Enum width | captured `effSlotType` (Enum) and `effIsPaused` (Boolean) in a size-1 record prove scalars are 1 byte, so 0x00/0x01 are right. |
| merged state stream | `DC E7 5D CB 2E 74 80` decodes to exactly three present fields: 9, 100, 129, consuming 6 of 7 bytes. |
| target node | `0x4000010E218A839C` is the player node in CRT2 **and** in every other CRT that touches structure 26, so the patch is not aimed at a stale node. |
| send order | CRT2 at 18:39:47, CRT3 suppressed, CRT17 merged at 18:39:49 — the patch is sent after the create, so nothing overwrites it afterwards. |
| reaches the wire | `AreaClientReplicationTransaction.WriteImplementation` writes `_acrt` after the merge, so the merged bytes are transmitted. |

So the bug is **not** in the encoder. Two possibilities remain:

1. The client's replication reader stops applying fields before index 129
   (schema/version field-count limit, or it stops when its own state stream is
   exhausted). This fits the evidence neatly: field 9 is early and clearly did
   land — `staMobilityFree` is what unblocked movement — while field 129 did not.
2. The GOM-to-address resolution used by the watcher is wrong, making
   `chrPlayerLoaded=0` a measurement artefact.

`accesses=0` on all three fields means the hardware breakpoints never fired,
which is evidence for (2) at least in part; the polling path and the
breakpoint path therefore disagree in reliability and the polling value is the
one that matches the user's symptom.

### Next run

Resolve the real storage of `chrPlayerLoaded` on the player's concrete type by
a second, independent route and compare against `0xCEA4D176`, and arm the
breakpoint before the player node exists rather than after. If the address is
confirmed and the value is still 0, the remaining question is whether the
client applies fields past some index, and the fix is to stop relying on field
129 and instead ship the load-complete signal the way the client expects it.

## Measurement fix, for the next run

The measurement itself had three defects, all now fixed in
`Diagnostics/CompatibilityLauncher.cpp` (rebuilt, compiles clean).

1. **`accesses=0` was self-inflicted, not evidence.** `installDataBreakpoints`
   wrote all four debug registers, destroying whatever another watcher had
   armed, and the `installed[tid]` map then skipped those threads forever. The
   ability gate's breakpoints could be taken and never restored, while the
   passive poll kept reading correctly — which is exactly the contradictory
   "zero hits next to a live value" in the log. It now takes a `force` flag so
   the poll re-asserts its slots every cycle, and a `displaced` counter that
   logs once per process when it has to take a foreign slot, so contention is
   visible rather than silent.

2. **The slot-to-field mapping was wrong whenever a field failed to resolve.**
   `armedNow` was built with `push_back` over resolved fields only, but the
   debug-register number and the name lookup both index that vector by slot.
   If `chrPlayerLoaded` had been the field that failed to resolve, slot 0 would
   have been `ablUserCacheIsFrozen` while the log printed
   `chrPlayerLoaded`, and the breakpoint would have watched the wrong byte.
   All three resolved in the last run so it did not bite, but it would have
   produced a confidently wrong answer. Slots are now full-length and
   field-ordered, with zero for unresolved fields.

3. **No independent route existed.** The resolver reached the field address by
   finding the id's index in the concrete type's id table and then trusting that
   the descriptor array is parallel to it with a 12-byte stride and the value
   offset at +8. That indexing is precisely the assumption a wrong address would
   come from, and it was unverified — so a bad stride or offset would have
   produced a plausible address that reads a plausible 0. A second route now
   scans the descriptor array for the field id itself and reads the offset
   beside it, sharing no indexing assumption. Both addresses, the concrete type,
   the storage base, the offset and the id index are logged per field with an
   explicit `AGREE`/`DISAGREE`.

### Reading the next run

- `route2` equal to `address` and `AGREE` — the address `0xCEA4D176` is sound,
  so `chrPlayerLoaded=0` is real and the client genuinely is not applying field
  129. That confirms hypothesis (1) and the fix moves to how the load-complete
  signal is delivered.
- `DISAGREE` — the descriptor indexing was wrong and the old reading was an
  artefact; the correct address is in `route2`.
- `displaced N foreign debug-register breakpoint(s)` — the old `accesses=0` was
  register contention, now logged and self-healing.
- Non-zero `accesses` on `ablUserCacheIsFrozen` — the gate is being recomputed
  per frame as expected, and the `caller` column distinguishes the store in
  `_CacheAbilityUserValues` from the load in `_AbilityValidateCached`.

No server-side change is proposed until one of these is observed, because the
encoded transaction has already been shown byte-correct and changing it now
would confound the measurement.

## Regression from the fix above, caught by the 19:34 run

The full-length slot change (item 2) silently disabled the resolver. A run
that reached world entry resolved nothing at all:

```
AbilityGateWatch state (t=27421): chrPlayerLoaded=unreadable ablUserCacheIsFrozen=unreadable ...
summary pid=34852: chrPlayerLoaded address=00000000 final=255 accesses=0
```

Cause: the retry guards tested `abilityGateAddress[pid].size()` to mean "already
resolved". With one slot per field that vector is always size 3, even when every
entry is zero, so a resolve attempt that found nothing was recorded as a
success and no further attempt was ever made. The previous run resolved fine
precisely because the packed vector was empty on failure. `=unreadable` was the
same fault showing through the poll: `ReadProcessMemory` was being handed the
null placeholders.

All six guards now call `anyArmedSlot`, which tests for a real address rather
than for emptiness, and a zero slot reports `=unresolved` instead of
`=unreadable` so the two faults stay distinguishable. The other two fixes from
the previous section — the independent route and the forced re-arm — were never
exercised by that run, so both are still unverified.

## 19:40 run — resolver converged, and the gate reading is now in doubt

The regression fix worked: the resolver armed (`pid=58584`) and polled. But:

```
chrPlayerLoaded      address=CD95CFC6 initial=0 route2=00000000 DISAGREE type=ED3AA9A0 storage=CD95BFC0 offset=00001006 idIndex=401
ablUserCacheIsFrozen address=CD95C99A initial=0 route2=00000000 DISAGREE type=ED3AA9A0 storage=CD95BFC0 offset=000009DA idIndex=561
ablUserCacheIsLucid  address=CD95C994 initial=0 route2=00000000 DISAGREE type=ED3AA9A0 storage=CD95BFC0 offset=000009D4 idIndex=14
```

Three things follow, and together they mean the earlier conclusion must be withdrawn.

1. **`route2=0` is my bug, not evidence against the address.** The second route
   assumed a 12-byte descriptor stride with the field id at `+0`. That layout
   was never verified — I invented it when writing the cross-check. It found
   nothing, so it disagrees with everything, including fields it would have to
   agree with. `DISAGREE` here is meaningless and the cross-check is worthless
   until the descriptor layout is actually established.

2. **Zero breakpoint hits is the real signal.** `ablUserCacheIsFrozen` is
   written by `_CacheAbilityUserValues` on every ability-bar refresh, and the
   user was clicking abilities. With the forced re-arm in place and no
   `displaced` line (so no register contention), zero hits on a byte the client
   must be writing means the address is wrong, or single-step delivery is
   broken. The earlier "register contention" explanation for `accesses=0` was
   wrong; contention was never happening.

3. **The initial values changed between runs** — `ablUserCacheIsFrozen
   initial=1` last run, `initial=0` this run, for a field whose real value is
   1. A real field does not change like that across runs of the same build.

So `chrPlayerLoaded=0` is **not yet evidence** that the client ignores field
129. The hypothesis that the reader stops before field 129 is untested, and the
possibility that every address so far has been wrong is live.

### Positive control added

The decisive missing piece was a known-good field resolved through the *same*
path. Three ids with independently established runtime values now resolve in the
same pass as the gate fields, on the same hero node and the same descriptor
table:

| Field | Id | Expected |
|---|---|---|
| `chrIsMe` | `0x4000000365D249CB` | 1 |
| `chrCharacterPlayMode` | `0x400000077CDF593B` | 1 |
| `chrCharacterPhaseMode` | `0x4000000886E130D2` | 1 |

They get no debug-register slots, which are fully committed to the gate, and
each run prints a verdict line:

```
PlayerControl pid=NNNNN verdict: N pass, N fail -- resolver is SOUND/SUSPECT
```

- **SOUND** — the addresses are right, `chrPlayerLoaded=0` becomes a real
  finding, and hypothesis (1) can finally be tested.
- **SUSPECT** — every gate reading to date is void and the descriptor layout
  has to be recovered properly before anything else is worth measuring.

## 19:48 run — resolver validated, and `chrPlayerLoaded=0` is now real

`pid=21188` resolved, and the controls came back exactly as expected:

```
PlayerControl pid=21188: chrIsMe              address=CF3AD7DD value=1 expected=1 PASS
PlayerControl pid=21188: chrCharacterPlayMode address=CF3AD784 value=1 expected=1 PASS
PlayerControl pid=21188: chrCharacterPhaseMode address=CF3AD794 value=1 expected=1 PASS
PlayerControl pid=21188 verdict: 3 pass, 0 fail -- resolver is SOUND
```

Same pass, same hero node, same descriptor table, so these gate readings now
stand:

```
chrPlayerLoaded      address=CF3AD7E6 initial=0
ablUserCacheIsFrozen address=CF3AD1BA initial=1
ablUserCacheIsLucid  address=CF3AD1B4 initial=1
state (t=28174): chrPlayerLoaded=0 ablUserCacheIsFrozen=1 ablUserCacheIsLucid=1
```

**The gate is confirmed closed, and confirmed to be closed by
`not chrPlayerLoaded`, not by any second gate.** The earlier "the client stops
before field 129" theory remains possible, but the competing explanation — the
client applies the field and then clears it — is equally consistent with
everything seen so far, and nothing yet distinguishes them.

The addresses also rule out a whole class of theory: the six resolved fields
span `CF3AD1B4`..`CF3AD7E6`, 0xD2 bytes, with `idIndex` values of 14, 401 and
561. The concrete type has at least 561 fields, so field *index* is not the
limit — a 215-field server schema is not truncating a 129th field, because the
client's own field numbering is far larger.

### Still outstanding

Data breakpoints produced **zero hits and zero `displaced` lines** even with the
resolver now proven correct and the user clicking abilities. Since the poll is
independently validated by the controls, this does not block the finding above,
but single-step delivery is evidently not working and should not be trusted as
evidence either way until fixed.

`route2` remains `00000000` on every field. That is the known-bad descriptor
assumption from the previous section, not new information.

### Next step: distinguish "never applied" from "applied then cleared"

Both remaining theories predict `chrPlayerLoaded=0`, so no amount of further
polling separates them. The server can, because it controls *when* the update
is sent. A diagnostic mode that re-sends the update after world entry splits
them:

- `chrPlayerLoaded` becomes 1 — the field applies fine and something clears it
  afterwards, so the client owns the value and the fix is in the load-complete
  path rather than in replication.
- still 0 — the client is not applying this field at all, and the next question
  is whether a minimal single-field update behaves differently from the
  three-field merge.

A minimal `chrPlayerLoaded`-only update is the stronger first probe, because
it also rules out the merge and value-ordering as causes in one step.

## Retraction: the "field order is wrong" lead was a false alarm

I claimed the client's field order and the CRT1 schema's order disagreed,
because `chrCharacter.txt` lists `index 9 = ablUserCacheAngle` and
`index 129 = statHealth` where CRT1 says `staMobility` and `chrPlayerLoaded`.
**That comparison was invalid and the conclusion is withdrawn.**

The two listings are not the same field set. Only **75 of CRT1's 215** field
names appear in the Jedipedia listing at all, and the ones that are missing
include obvious `chrPlayerCharacter` fields such as `chrIsMe`, `chrGender`,
`invEquipment` and `chrQuickTravelForbidden`. The Jedipedia file is a partial
listing of the parent `chrCharacter`; CRT1 covers the child with the
replicated fields. Indices from two different sets cannot be compared, and I
should have checked set overlap before drawing a conclusion from them.

So the CRT1 field order is **not** contradicted, and the "the reader stops
before field 129" theory is not undermined by this.

### Offline value walk: inconclusive, and where it stands

`Diagnostics/Decode-CrtValues.py` walks the ordered value body so decoded
values can be sanity-checked against the field names. Current state:

- Field *states* decode cleanly and name the expected fields.
- Values do **not** reconcile. CRT2's player record consumes 28 of 2773 value
  bytes; the shortfall is almost entirely container fields, so the Map/List
  encoding model is wrong, not demonstrably the field order.
- Two 64-bit encodings were tried (`packed` and `fixed8`); `fixed8` walks all
  present fields without erroring, which is progress, but its scalar values are
  nonsense (a melee distance of `-2.9e+38`).
- `0xC0` appears throughout the captured value bodies and is not a valid token
  in the current packed-integer reader. That is the most likely missing piece: a
  token class between the literal bytes and the multi-byte `0xC8..0xCF` range,
  most plausibly the negative/small-value encoding.

This is the right thing to finish offline, because it is the only remaining way
to prove the patch is correct without the client, but it needs the packed
integer encoding resolved first. It should not be treated as evidence either
way until `0xC0` is understood.

## The differential: `SWTOR_PLAYERLOADED_ONLY=1`

Two theories remained, and both predict `chrPlayerLoaded=0`, so no amount of
polling separates them: the client never applies field 129, or it applies it and
something clears it. The server can separate them, because it controls the
*shape* of the update, not just its timing.

`AreaSafeLoginRemoval.ApplyPlayerLoadedOnlyToFinalCapturedTransaction` emits a
CRT17 record whose **only** present field is 129, with a single value byte of
`0x01`. Everything else in the three-field merge is removed: no `staMobility`,
no `modMetaStatComputed_Shared`. A null result can then only be about the field
or about the client, because the merge is no longer a variable.

The state stream is uncompressed — two bits per field for all 215 fields, 54
bytes, no run codes. The client walks it by field index, so a larger stream is
valid; it is simply bigger than the captured one. It was generated offline and
round-tripped: 54 bytes decoding to exactly one present field, index 129,
consuming 53 of 54 bytes.

The three size words are variable-length packed integers, so writing 59 and 1
narrower than the captured 608 and 600 would shift every following offset. Both
are re-encoded at the captured width (`c9` = two-byte big-endian payload), which
keeps `body_start` at `0x1D`:

```
outer  = 4 (struct id + inner size) + inner 1 + states 54 = 59 = 0x3B
inner  = 1
value  = 0x01
states = 54 bytes
```

Verified end to end by re-deriving the exact bytes in Python and decoding them
with the independent reader:

```
merged length = 0xBB (187)      node = 0x4000010E218A839C
struct = 26   inner = 1         value body len 1 == inner_size
present: [(129, 'chrPlayerLoaded', 'state=1')]
value byte = 0x01
removal tail: count = 17, 102 bytes
4 + 1 + 54 = 59 = header 0x3B   OK
```

Server rebuilt clean; `git diff` on `AreaClientReplicationTransaction.cs` shows
only the pre-existing Safe Login work plus the new dispatch, so the file is
back to its intended state after an accidental truncation during editing.

### Reading the next run

Leave the flag **off** first to confirm the baseline still behaves, then set
`SWTOR_PLAYERLOADED_ONLY=1` in `Run-SWTORClassic-Trace-Tython.cmd`:

- `chrPlayerLoaded=1` — the three-field merge was the problem. The fix is to
  drop the merge and ship the field on its own.
- `chrPlayerLoaded=0` — the client does not apply this field regardless of
  shape, which removes the merge as a suspect entirely and moves the work to
  the native load-complete path.

Caveat to keep in mind: in this mode the stat map and mobility are not
delivered, so movement may be immobilised and stats may look wrong. That is
expected and is not part of the result.

### The next gate, and why it cannot be patched

`ablUserCacheGlobalTimerRunning` ("is the global timer running") is now a fourth
watched field, `0x400000004C19FF53`. `GetTimeUntilAbilityReady` gates on
`IsGlobalCooldownRunning()` and `IsAbilityReady` returns `effResultNotReady`
whenever it reports time remaining, so if it reads 1 while idle it becomes the
next "not ready yet" the instant the frozen gate clears.

Jedipedia reports it as **"Shared with server DOM: no"** — client-local. Unlike
`chrPlayerLoaded`, which is "yes", it cannot be set by replication, so there is
no server-side fix for it and none will be attempted. It is watched purely to
find out whether unblocking `chrPlayerLoaded` would just hand us the next gate.

### GOM ids do not need to be requested

`Tools\tor_tools\gom_type_names.xml` is a local name-to-id table in exactly the
id space the resolver uses — `chrPlayerLoaded` is `4611686075838313591` there,
which is `0x4000000D5DF53477`, the value already hardcoded in the launcher.
Every watched id is now verified against that file rather than copied by hand:

```
chrPlayerLoaded                 0x4000000D5DF53477
ablUserCacheIsFrozen            0x4000003548CCDCC1
ablUserCacheIsLucid             0x400000002758AA0B
ablUserCacheGlobalTimerRunning  0x400000004C19FF53
chrIsMe                         0x4000000365D249CB
```

Asking for these by hand was avoidable; the table was already in the tree.

## SOLVED — 20:30 differential, and the cause was our own encoder

`SWTOR_PLAYERLOADED_ONLY=1` worked. Behind a SOUND resolver (3 pass), the
single-field record produced:

```
chrPlayerLoaded                initial=1   ← applied
ablUserCacheIsFrozen           initial=0   ← gate OPEN
ablUserCacheIsLucid            initial=1
ablUserCacheGlobalTimerRunning initial=0   ← no second gate
```

and in the client abilities fired: GCD ran, animations played. So the field,
the value, the node, the framing and the client were all fine. **The three-field
merge was the defect.**

### What was actually wrong

The merge used a 7-byte run-length-encoded state stream
(`DC E7 5D CB 2E 74 80`). It decoded correctly in *our* reader — which is why
it survived every offline check, including round-tripping the field states and
reconciling the sizes. The client did not accept it, so `chrPlayerLoaded` never
became present and `ablUserCacheIsFrozen` never cleared.

The successful diagnostic differed in exactly one respect: its state stream was
**generated** (two bits per field for all 215 fields, 54 bytes, no run codes)
rather than hand-packed. That is now what the merge emits:

```csharp
byte[] mergedState = new byte[54];
mergedState[2]  = 0x10;   // field 9    staMobility
mergedState[25] = 0x40;   // field 100  modMetaStatComputed_Shared
mergedState[32] = 0x10;   // field 129  chrPlayerLoaded
```

Verified offline before rebuilding, by re-deriving the exact bytes and decoding
them with the independent reader:

```
len = 0x314 (788)      node = 0x4000010E218A839C
struct = 26            inner = 602,  value body len 602 == inner_size
present: [(9,'staMobility'), (100,'modMetaStatComputed_Shared'), (129,'chrPlayerLoaded')]
field   9 value = 0x00   (staMobilityFree)
field 100 value = captured bytes, 600, byte-identical
field 129 value = 0x01   (chrPlayerLoaded = true)
outer 4 + 602 + 54 = 660 = 0x294  matches header
removal tail count = 17, len 103
```

`outer` moves 0x260 -> 0x294 because the state stream grew from 7 to 54 bytes;
`inner` stays 0x25A. Both size words remain three bytes wide, so `body_start`
stays at `0x1D`.

The lesson worth keeping: a state stream that round-trips in our own decoder is
not thereby accepted by the client, and no amount of offline self-consistency
proves it. The differential was what separated the two, and it only worked
because the measurement had first been validated by three independent control
fields. Every earlier conclusion in this investigation that rested on the
resolver alone was unsafe.

Movement should be restored as well, since field 9 is delivered again. The
diagnostic flag is back off; the fix is the default path.

## Ability execution: the echo is the prime suspect

The gate is solved, so the next stage is exposed. The chain in the client
script is:

```heroscript
public method AbilityActivate(...)
  Me.InitClientCastingTime(a1)     -> SetClientCastingTime -> ablCastTimeEnd = $NOW + duration
  Me.DoClientAnticipation(...)     -> the animation
  $ABILITY.RequestAbilityActivate(Me, node, id1, Me.ablActiveRequestId, queue)
```

The cast bar is driven by `ablCastTimeEnd`, which is set **client-side, before
the request is sent**. So a channelled ability should show its bar without any
server involvement at all. It does not, which means something is cancelling it
after the fact:

```heroscript
public method OnAbilityResult(Me, a1, a2, a3, a4 as Enum effResult)
  if (a4 != effResultOk and a4 != effResultNotReadyQueue) and a1 != 0
    ...
    if Me.IsCastingAppearanceInUse(id1, a2)
      Me._InternalAbilityCancel(cbtOutcomeCancelled, a2, true)
```

`OnAbilityResult` only runs on failure, and it cancels. That is precisely the
reported symptom: animation plays, then no cast bar and no buff.

The server has been answering every `CMsgF96DCDB0` with:

```csharp
else if (mode == RpcReply.Mode.Echo)
    client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, _body));
```

`AreaRPCPollAck` is the poll-ack shape that belongs to `AreaModulesList`, and
it is being handed an ability-activation body. The client has no reason to treat
that as a successful result, and a misread is the most economical explanation
for a consistent cancel.

### The test

`SWTOR_RPC_REPLY_MODE` goes back to `swallow`, which was the original default
before echo was added experimentally. Nothing is sent, so the client's own cast
timer is the only thing in play.

- **A cast bar appears** — the echo was the poison, and the remaining work is
  only the server applying the ability so the cast completes and the effect
  lands.
- **Still nothing** — the cancel is coming from somewhere else, and the next
  probe is `ack` (an empty poll-ack, no request bytes) to separate "any reply
  cancels" from "this reply cancels".

This is worth trying before writing an effect encoder, because it costs one
run and could remove the need for one entirely.

## Handoff: the ability-effect reader (option b)

`SWTOR_RPC_REPLY_MODE=swallow` disproved nothing and changed nothing in game.
It is still the configured value and should be left there for the reader run,
since it removes a variable at zero cost.

### What is known

The chain from ability to effect is mapped in the schema, not guessed:

```
chrPlayerCharacter field 148  ablContainer         0x40000002F8C347F1  (ClassRef)
  ablContainer field 0        conContents          0x400000027E3ED716  (Map)
    ablAbility node          ablEffectIDs         0x4000000A1D6B4918
    ablAbility node          effAbilitySpec       0x4000000A1D6B491C  (labelled
                                                      "effEffect" but resolves to
                                                      effAbilitySpec)
Also on the hero node, possibly useful:
  field 149 ablContainerAbilityRanks   0x400000118A7E6089
  field 151 ablPackageSpecList         0x400000118D870CA7
```

All ids verified against `Tools\tor_tools\gom_type_names.xml`, which is in the
same id space the existing resolver uses. Do not hand-copy ids; look them up
there.

From the last run, 18 casts produced 18 requests with byte 29 counting 1..18
with no gaps, so the request path is clean. Bytes 16-19 are the ability spec and
resolve to four distinct abilities, which are the ones to target:

| Spec bytes | Casts |
|---|---|
| `F2 9A 7B A7` | 8 |
| `F0 0B 2A A2` | 4 |
| `E5 03 AF 68` | 4 |
| `40 01 01 F5` | 2 |

### The plan, and why it is not a small change

Gate it behind `SWTOR_TRACE_ABILITY_EFFECTS=1`, default off. Resolve
`ablContainer` on the hero node with the existing
`resolvePlayerFieldAddresses` — that part is covered, it is a plain ClassRef at
schema index 148. Read the 4-byte node ref, then walk to that node and read
`conContents`.

The obstacle is the second step. `resolvePlayerFieldAddresses` only works for
the player node, located through a hardcoded character-tree lookup keyed on
`0x4000010E218A839B`. Turning an arbitrary node id into a node object, and then
resolving a field on it, means generalising the resolution path — that is a
refactor, not an addition.

### The known-good instance to validate against

The captured `ablContainer` `0x1AC6F6DBD7` has 208 bytes of `conContents`
holding 26 real node refs, alternating `CC 1A C6 F6 DB D8` upward, structure 10
(`ablAbility`) and structure 11 (`effEffect`) in turn, ending at
`0x1AC6F6DC0A`. A live read that does not match this shape means the node
reference is wrong, not the field.

The effect objects in that container are templates, not instances: structure 11
records are `inner=1` with only `effSlotType` = `0x1E` and no timing. The live
form is **structure 40** (`effEffect` + `effStackLimitComponent`), which adds
`effStartTime`, `effEndTime` and `effCasterId` — that is what a buff needs.

### Blocked on: container value encoding

Parsing `conContents` is a container value, which is the wall
`Decode-CrtValues.py` hit: it consumed 28 of 2773 bytes on the CRT2 player
record and never reconciled, and the `0xC0` token class in value bodies is still
unexplained. So the first read of this probe depends on code that has already
been shown not to work.

Two ways forward, and the second is cheaper:

1. Solve the container value encoding offline first. Verifiable, but it is a
   problem that already defeated one attempt.
2. Make the probe dump **raw bytes** for `conContents` and diff against the
   208-byte capture above. One known-good instance is enough to derive the
   layout, and it turns the first run into a measurement rather than a guess.

Recommendation is (2), scoped as narrowly as possible: read `ablContainer`, dump
raw, compare. Do not build the full reader until that comparison is understood.

### Do not do this yet

Do not build the effect encoder. It requires inventing an effect type, and the
captures contain only two live effects, both Safe Login and invisible by design.
There is no known-good instance of a visible buff to model against. The reader
above is the thing that has to come first, because it is the only route to a
real effect id.

### Unrelated but still open

The quest giver is a **content** gap, not a protocol one. `sub=0x10` requests
node `0x1AC6F6DC6D`, which is structure 62 `chrNonPlayerCharacter`. CRT12 is the
only struct-62 record in all 17 captures and it is an empty shell (`inner=0`,
only `staEnterIdle` reset to default), so the client re-requests it ~21 times.
Re-sending the same bytes cannot populate an NPC; the data was never captured,
most likely because it arrives in the initial world-state packet.

## Correction: not solved. The generated stream was necessary, not sufficient

The next run used the three-field merge with the generated 54-byte stream. Result:

```
PlayerControl verdict: 3 pass, 0 fail -- resolver is SOUND
state (t=31329): chrPlayerLoaded=0 ablUserCacheIsFrozen=1
```

**Movement came back. Abilities did not.** So the generated stream is a real
improvement — field 9 now demonstrably applies, which the hand-packed stream may
never have done — but `chrPlayerLoaded` still does not, and the earlier
"SOLVED" heading was wrong. What the differential actually proved is narrower:
*the client accepts this field when it is the only present field.*

### The bisect

Three record shapes are now measured:

| Present fields | chrPlayerLoaded | Observed |
|---|---|---|
| `{100}` | — | captured, client accepts it, nothing changes |
| `{129}` | **1** | gate opens, abilities fire, buffs do not land |
| `{9, 100, 129}` | 0 | movement restored, abilities greyed |

The three-field record delivers field 9, so the state stream is accepted and the
failure is specific to combining these fields. `SWTOR_MOBILITY_AND_LOADED=1`
emits `{9, 129}`, which isolates which of the two companions is responsible:

- **passes** — field 100's 600-byte value is what desynchronises the client's
  value stream, and the ordering/alignment model for multi-field records is
  still wrong. Then the work is to carry field 100 correctly, which probably
  needs the container encoding solved (the same open problem
  `Decode-CrtValues.py` stalled on).
- **fails** — field 9 is the poison field, and the 1-byte `staMobility` enum
  before another value is what breaks alignment.

Either way the stat map is absent from both passing shapes so far, which lines
up with the report that buffs did not land: without
`modMetaStatComputed_Shared` the client may not be computing the stats an effect
needs to resolve. So a working end state still requires field 100, and these
bisects are narrowing the problem rather than solving it.


---

# Phase (a) result: container value encoding — SOLVED, and it was not the containers

The handoff above assumed the blocker was the container value encoding. It was
not. The container encoding in the task brief is correct and was not re-derived.
The actual defect was in the **field-state bitstream width**, which is what made
every walk stall. This is the corrected account.

## The defect: field states are 1 bit per field, not 2

`Decode-Style7Replication.py::field_states` reads 2 bits per field plus a
run-length code. That is wrong for these records, and it is wrong
*arithmetically* — not merely suboptimally. A 5-field container (structures
9/12/13/14/17/18/19/20/21/22) carries exactly **1 state byte = 8 bits**:

| structure | fields | state bytes | bits | 2-bit needs | 1-bit needs |
|---|---|---|---|---|---|
| 9/12/13/14/17/18/19/21/22 | 5 | 1 | 8 | **10 — impossible** | 5 |
| 20 (trdContainer) | 7 | 1 | 8 | **14 — impossible** | 7 |
| 26 (chrPlayerCharacter) | 215 | 27 | 216 | **430 — impossible** | 215 |

Every one of these has fewer state bytes than 2 bits/field requires. There is no
run-length escape: the count is fixed at read time, so the bits simply are not
present. The 2-bit model was fitting nothing — it was producing plausible-looking
field names from noise, which is exactly how the earlier "transmitted=17/215"
reading arose.

Checked across **all 17 captures**: 2-bit fails the `bits >= 2*nf` test for every
record in the set, including the player and every update record. 1-bit is the only
reading that is not contradicted.

## The container encoding, as verified (not re-derived)

`ablContainer 0x1AC6F6DBD7`, inner_size 208, reconciled to the byte:

```
1b                                          count = 27
[1B][CC 1A C6 F6 DB D8] x27                 7 bytes each: slot index + CC + 5-byte node
[CF E0 00 4E A6 02 37 38 70] x2             9 bytes each: CF + 8-byte ref
1 + 27*7 + 2*9 = 208                        exact
```

Token scheme, confirmed: `< 0xC0` literal, `0xC8 + n` → n bytes big-endian.
`0xC0..0xC7` are not part of it; the dead signed-byte branch has been deleted
from `Decode-CrtValues.py` rather than left in place.

**The rule for the trailing repeated refs** (the item the brief asked to be worked
out rather than hard-coded): they are **not** map entries. `conContents` is a Map
whose parts are `[8, key, value]`; the count is followed by exactly that many
entries, so the walk lands on an entry boundary by construction. The repeated
9-byte `CF` refs that trail some containers are the *following fields* —

## Validation: every container, one verdict each

`python Diagnostics/Decode-CrtValues.py --containers` — each container is a
separate pass/fail check, and the tool exits non-zero if any fails. It requires
the walk to consume **precisely `inner_size` bytes and land on an entry
boundary**; a short or over-long entry list is a failure, not a near-miss.

**All 14 CRT2 containers PASS**, including the 208-byte ablContainer at 208/208
and the 100-byte qckContainer at 100/100:

```
CRT2  9  ablContainer 0x1AC6F6DBD7 -> 208/208  PASS   <- the reference capture
CRT2 12  tmrContainer 0x4000010E56DA93C0 ->  19/19   PASS
CRT2 13  effContainer 0x1AC6F6DC0E ->  33/33   PASS
CRT2 13  effContainer 0x1AC6F6DC0F ->  18/18   PASS
CRT2 13  effContainer 0x1AC6F6DC10 ->  18/18   PASS
CRT2 14  eqpContainer 0x4000010E56DA93C6 ->  69/69   PASS
CRT2 17  invContainer 0x4000010E56DA93C1 ->  29/29   PASS
CRT2 17  invContainer 0x4000010E56DA93C2 ->  19/19   PASS
CRT2 18  vndBuybackContainer 0x4000010E56DA93C3 -> 19/19 PASS
CRT2 19  bnkContainer 0x4000010E56DA93C4 -> 18/18   PASS
CRT2 20  trdContainer 0x1AC6F6DC11 ->  18/18   PASS
CRT2 21  malMailContainer 0x1AC6F6DC12 ->  18/18   PASS
CRT2 22  qckContainer 0x1AC6F6DC13 ->  27/27   PASS
CRT2 22  qckContainer 0x4000010E56DA93C5 -> 100/100 PASS
```

The decoded `conContents` of the ability container is the deliverable:

```
[27]{1:0x1AC6F6DBD8, 2:0x1AC6F6DBDA, 3:0x1AC6F6DBDC, 4:0x1AC6F6DBDE, ...}
```

27 ability slots, each pointing at an `ablAbility` (structure 10) child, which in
the same capture is followed by an `effEffect` (structure 11) child. That is the
chain the effect reader needs to walk.

## Two bugs found in my own probe, both the documented failure mode

1. `s_.p+n.__gt__(s_.e)` parses as `s_.p + (n > s_.e)`, not `(s_.p+n) > s_.e`.
   It threw `eof` on **every** record and made a working encoding look broken.
2. Truncating the *display* after 6 entries also truncated the *read*, stalling
   the ablContainer at 50/208. Display limits must never gate the walk.

Both are the same shape as the three wrong turns already in this file: an
unverified step producing a confident false signal. Fixing (2) is what took
ablContainer from 50 to 208.

## Known-open, not solved: the player record

**Structure 26 still does not reconcile.** It consumes 40 of 2773 bytes before
stopping. This is *not* the state width (now settled) and *not* the token table.
Under 1-bit the walk reaches `staWeaponState` and the next byte is `0xC0`, which
the confirmed token scheme rejects. Something upstream is still mis-sized — most
likely a field whose assumed width is wrong (`Time`, `Vec3`, or the embedded
`prfOriginSchematic` class), not the packed-integer reader.

Full sweep under 1-bit: **49/96 records reconcile exactly.** All 14 containers
reconcile; the player and the item/effect records do not. So the container work is
sound and independently useful, but phase (a) is **not** complete in the sense the
handoff meant, and I am not going to relabel it as done.

## The flags=0x09 fork — a real difference, still open

Update records (`flags 0x09`, e.g. CRT4 obj2) do not follow the 1-bit model:

```
CRT4 obj2 effContainer flags=0x09 inner=43
  1-bit states [2,1,1,1,1]  -> conContents ABSENT, consumes 9/43
  body 0d 01 cc 1a c6 f6 dc 2d 02 cc 1a c6 f6 dc 36 03 ... 06 cc 1a c6 f6 dc 62
```

The body is plainly a map, and `0d` is a **delta count**: 13 entries changed,
6 present on the wire, `1 + 6*7 = 43` exactly. So on `0x09` records the count is
not the number of entries written, and the state word disagrees with the body.
This is a genuine second encoding, not a variation, and I have not proven the
rule. I am flagging it rather than folding it in with a guess — the earlier
"route2 DISAGREE" came from exactly that move.

## What is needed to close the rest

The bit-width question is now closed by arithmetic, so the remaining asks are:

1. The native packed-int/value writer, to resolve the `0xC0` at the player
   record's byte 40 and the widths of `Time` / `Vec3` / embedded classes. The
   doc already cites the MSB-first bit reader at RVA `0x1B0E00` / `0x1B0EB0`; the
   value writer is the counterpart that is still missing.
2. Whatever distinguishes the `0x09` update record — specifically whether the
   leading byte is a delta count and where the true entry count comes from.

Per the brief I have **not** begun the phase (2) resolver refactor, and I have
**not** built the effect encoder. Phase 2 should not start until the player
record reconciles, or an explicit decision that the container result alone
unblocks the `conContents` dump.

`conSharedData` (ClassRef) and `conContainerSpecName` (UInt64) — and are consumed
by them. There is no offset to hard-code: read the map to its declared count,
then continue with the next present field. Confirmed by the value equality
across every container: `conSharedData` and `conContainerSpecName` always carry
the same id (e.g. `0xE0004EA602373870` for ablContainer), which is why they look
like a repeated pair.

HeroScript corroborates the shape independently:
`chrCharacterClassMethods.txt:860` does `var lookup = Me.eqpEquipment.conContents`
then `foreach key in lookup` / `lookup[key]`, and
`effCOntainerComponentClassMethods.txt` does
`Me.effContainerPositive.GetContents()` returning `List of NodeRef of
conContainableComponent`. Key-to-value map, consumed as a list of node refs.




---

# Phase (2): resolver generalised, gated, and ready to run

Decision recorded: phase 2 starts before the player record reconciles, because
its deliverable is a *measurement* and the measurement now has a known-good
expected value. The container decode is proven offline (14/14 CRT2 containers,
ablContainer 208/208), so a live `conContents` read is directly comparable to the
capture. If the live bytes match, the resolver is right; if they do not, the node
reference is wrong. That is the pass/fail the handoff specified, and it does not
require the player record.

This is stated plainly because it is the one part of the work with **no offline
proof**: the code compiles and the logic is reviewed, but whether it reads the
right address can only be established by running it against the client.

## What changed in CompatibilityLauncher.cpp

**1. New `resolveFieldAddressesForNode` — the actual generalisation.**

The old `resolvePlayerFieldAddresses` found exactly one node: the local player,
by the hardcoded key `0x4000010E218A839B` in the character tree. The new
function takes the node address directly and walks the same chain the old memory
scan walked, minus the scan:

```
node+0x4C       -> heroObject
heroObject+0x14 -> context
context+4       -> concreteType
context+8       -> storage
concreteType+0x4C/0x50 -> id table begin/end
concreteType+0x9C      -> descriptor array
```

It keeps both resolution routes: the id-table index, and the independent
descriptor scan for the id itself. They share no indexing assumption, and the
probe reports when they disagree.

**2. The player path is untouched.** `resolvePlayerFieldAddresses` is unchanged.
The `chrPlayerLoaded` probe and the three positive controls
(`chrIsMe`, `chrCharacterPlayMode`, `chrCharacterPhaseMode` — must report 3 pass)
depend on it, and their SOUND verdict is what makes gate readings meaningful.
Changing them would invalidate an established result for no gain, so they keep the
behaviour they were validated with.

**3. `SWTOR_TRACE_ABILITY_EFFECTS=1`, default off.** Prints
`AbilityEffectWatch: enabled/disabled` at startup, so a run's log always states
whether it was on. This matches the existing `SWTOR_TRACE_ABILITY_GATE` convention.

**4. Raw bytes, not a decode.** The probe resolves `conContents`
(`0x400000027E3ED716`) on the ablContainer node `0x1AC6F6DBD7` and dumps 256 raw
bytes. It deliberately does **not** implement the map decode: that rule is
already verified in `Decode-CrtValues.py`, and a second implementation here could
disagree with it without either being noticed. The dump is the evidence; the
Python reader stays the single decoder.

**5. Failures name their cause.** Three distinct messages, because these are
three different bugs:
- node not found in the character tree -> *the node key is wrong, not the field*
- field not present on the concrete type -> *the field is absent, or wrong node*
- descriptor routes disagree -> *the descriptor indexing is the bug*

A silent failure here would be the "register contention" mistake all over again:
a missing hit with no explanation, indistinguishable from a real zero.

**6. Own clock.** `nextAbilityEffectAt`, 5s, deliberately not shared with the
gate's poll loop. The existing comments explain why: a shared timer lets one
watcher's `continue` starve the other indefinitely.

## Build status

`Diagnostics/build-compatibility-launcher.cmd` — clean compile, no errors, no
warnings. `CompatibilityLauncher.exe` rebuilt 2026-09-25 22:27.

Field ids were looked up in `Tools/tor_tools/gom_type_names.xml` (the resolver's
id space), not hand-copied:

```
0x40000002F8C347F1  ablContainer
0x400000027E3ED716  conContents
0x4000000D5DF53477  chrPlayerLoaded
```

## How to read the next run

```
set SWTOR_TRACE_ABILITY_EFFECTS=1
```

Look for, in order:

1. `AbilityEffectWatch: enabled` — confirms the gate was on.
2. `conContents address=... crossCheck=... (descriptor routes agree)` — the two

## First live run: the probe failed loudly, and named the cause

Run 2026-09-25 22:30, `last-compatibility-run.log`. The gate was on and the
binary was the new one:

```
AbilityGateWatch: enabled (4 fields)
AbilityEffectWatch: enabled
AbilityEffect pid=73196: ablContainer node 0x0000001AC6F6DBD7 not found in the
character tree -- the node key is wrong, not the field.
```

Seven times, across both client processes, across every 5s cycle. **No raw bytes
were dumped** — the probe never reached the field, so the 208-byte comparison did
not happen this run.

### What the run established

**The probe works, and its failure message was accurate.** It named the right one
of the three failure modes before any of them could be confused. Had the failure
been silent, this run would have produced an empty log and three indistinguishable
hypotheses: broken resolver, wrong node key, or absent field. The specific
message is the only reason the cause is now known.

**The resolver itself is fine.** Later in the same log:

```
PlayerControl pid=73196 verdict: 3 pass, 0 fail -- resolver is SOUND
chrPlayerLoaded address=CC23D6D6 initial=1
```

So `resolvePlayerFieldAddresses` and the descriptor path are both healthy. The
failure was confined to node acquisition.

### Root cause: wire key vs live key

`0x1AC6F6DBD7` is a **replication stream key** — an id the wire assigns to a node
in a capture. The character tree at `manager+0x38` holds **live character
objects**. Wire keys are not tree keys. Feeding a wire key to a live-tree lookup
could never have worked, and retrying it would not have helped.

The live route is already described by the data: `chrPlayerCharacter` field 148
(`0x40000002F8C347F1`, `ablContainer`) is a ClassRef whose *value* is the
container's live node. So the correct acquisition is two hops:

1. `resolvePlayerFieldAddresses(..., ablContainerClassRefId, ...)` — the live
   player, via the function whose controls just reported SOUND.
2. Read the ClassRef's 8-byte value. That is the live container node.

`resolveFieldAddressesForNode` then takes that node directly, which is the
generalisation doing exactly the job it was written for: resolving a field on a
node the caller supplied rather than on the hardcoded player.

**Field ids were never implicated.** `0x400000027E3ED716` (`conContents`) came
from `Tools/tor_tools/gom_type_names.xml` and was never wrong; the probe simply
could not reach the node holding it.

### Unrelated pre-existing observation

`route2=00000000 DISAGREE` appears on the ability-gate fields throughout the log.
This is the existing descriptor cross-check in `resolvePlayerFieldAddresses`, not
the new code, and it predates this work. The controls still report 3 pass, so the
primary route is evidently correct; the cross-check route appears to be

## Verified offline from a minidump: the handoff's field id was wrong

Before spending another client run, the chain was checked against the existing
full dumps in `Diagnostics/*.dmp` using the same manager/tree walk the launcher
uses (`world-entry` / `tython-live` dumps, 0.9-2.2 GB each). The resolver was
reproduced in Python and driven end to end. This found a defect that no amount of
client time would have surfaced cleanly.

### The controls reproduce, which validates the harness

On `tython-live-current-34984.dmp` (hero node found by the same back-pointer scan
the launcher performs):

```
chrIsMe               idIndex=117  value=01
chrCharacterPlayMode  idIndex=253  value=01
chrCharacterPhaseMode idIndex=311  value=01
chrPlayerLoaded       idIndex=401  value=00
```

The three controls read 1 and the gate input reads 0 — the same verdict the live
run produced. The dump harness is therefore trustworthy for this comparison.

### The defect: ablContainer has two ids, and the handoff used the wrong one

`Tools/tor_tools/gom_type_names.xml` contains **two** entries named `ablContainer`:

```
0x40000002F8C347F1  ablContainer     <- the id in the handoff
0x400000118A7E6088  ablContainer     <- the one the live client actually has
```

The handoff listed `chrPlayerCharacter f148 ablContainer 0x40000002F8C347F1`.
That id is **not in the live player's id table**. The correct id for f148 is
`0x400000118A7E6088`, and it *is* present, at `idIndex=452`:

```
f148 ablContainer (correct id)  idIndex=452  addr=CAA10608  value=a0 be ba d6 ...
```

All 215 schema fields for chrPlayerCharacter are present in the live table, so
this is not a missing-field problem — it is specifically a wrong id. Note also
that the correct id is one below the `ablContainerAbilityRanks` id
(`0x400000118A7E6089`) given in the handoff, which is a plausible
off-by-one-in-the-transcription signature.

**This is why the first live run could not have worked even with a correct node
route.** The probe was asking for a field the concrete type does not have. Had it
been silent, that would have read as "field absent"; it would have taken another
run to distinguish that from a wrong node. The `conContents` id
(`0x400000027E3ED716`) is unchanged and is a ClassRef on the container type, not
on the player, so it was never the problem.

## Two live runs: the probe advanced, and the dump caught a bug of mine

### Run 2 (22:30) — the node-key route, and the loud failure that paid off

```
AbilityEffectWatch: enabled
AbilityEffect pid=73196: ablContainer node 0x0000001AC6F6DBD7 not found in the
character tree -- the node key is wrong, not the field.
```

Seven times across both processes. **Root cause: wire key vs live key.**
`0x1AC6F6DBD7` is a *replication stream* key — an id the wire assigns. The
character tree at `manager+0x38` holds *live* objects. Wire keys are not tree
keys, so that lookup could never have succeeded.

The probe naming the cause is the whole value of the explicit failure paths. Silent,
this would have been an empty log and three indistinguishable hypotheses.

### Offline check against the dumps — an id defect, found without a run

The chain was reproduced in Python against `Diagnostics/*.dmp` using the same
manager/tree walk. Harness validated first: the three controls read 1 and
`chrPlayerLoaded` read 0, matching the live verdict.

**`ablContainer` has two ids.** `gom_type_names.xml` lists both, and they name
different things:

| id | what it is |
|---|---|
| `0x40000002F8C347F1` | the ablContainer **node** id — names the container record |
| `0x400000118A7E6088` | the `chrPlayerCharacter.f148` **field** id |

All 215 schema fields are present in the live player's id table; the field id
`0x400000118A7E6088` is there (idIndex=452) and `0x40000002F8C347F1` is not,
because it is not a field on the player at all. The handoff was not wrong — I
conflated the two id spaces, and the code paid for it.

### Run 3 (23:28) — the corrected id works; the last hop exposed my 8-byte bug

```
AbilityEffect pid=22680: ablContainer live node=D238A800E642BF80
AbilityEffect pid=22680: f148 resolved via id 400000118A7E6088
AbilityEffect pid=22680: container object ... neighbourhood (+/-0x100, 512 bytes):
AbilityEffect pid=22680: no Hero node for the container object after 2
  back-pointer candidate(s)
```

**The corrected id worked.** f148 resolved, the ClassRef was followed. The failure
moved to the final hop and `concreteType=00000000` said why: the player's
`object - 0x50` geometry does not hold for an object reached by ClassRef. That
offset is only meaningful for a back-pointer, which is how the character tree
happens to reach the player — an assumption transplanted onto a different route.

The neighbourhood dump then paid for itself by catching the actual bug:

```
D238A800E642BF80
  full 8-byte read  : 0xD238A800E642BF80
  low  dword (ptr)  : 0xE642BF80      <- the real object
  high dword        : 0xD238A800      <- the NEXT field
```

This is a 32-bit process. I read 8 bytes where the field is 4, so the "pointer"
was two fields glued together and the address nothing lives at. The low dword is a
real allocation, and the dump's payload is a table of **0x20-byte records** with
each record's id at `+0x10`/`+0x14` — and the record at `obj+0x10` carries
`0x40000002F8C347F1`, the container.

So the third correction, all three evidence-backed:
1. Read the ClassRef as **4 bytes**, not 8.
2. Locate the container by its **node id** at `record+0x10`, not by a back-pointer.
3. Validate every candidate by walking the full chain before use.


## Offline attempt to close the last hop: the dump disagrees with the code

Before spending another client run, the record-id route was tested offline
against `tython-live-current-34984.dmp`. **It fails, and I am recording that
rather than shipping it as if it worked.**

```
id 0x40000002F8C347F1 found at 23 location(s)
validated records: 0
```

All 23 hits have a neighbouring field that looks like a pointer
(`D6BB6400`, `7BFD4876`, ...), and `rec+0x04 = 40000004` is plainly a vtable
slot rather than a concrete type. Reading the record as a 0x20-byte structure
with the id at `+0x10` and a Hero node at `-0x10` therefore validates nothing.

Re-reading the bytes with no assumption at all shows the record is **0x30 bytes,
not 0x20**:

```
rec+00 = B75E565E     rec+10 = 00000000     rec+20 = F8C347F1  <- id low
rec+04 = 40000004     rec+14 = 00000000     rec+24 = 40000002  <- id high
rec+08 = D20CD390     rec+18 = 00000000     rec+28 = D6BB6400
rec+0C = D20E4680     rec+1C = 40260000     rec+2C = 7BFD4876
```

Probing every field, and every nearby offset, for a walkable Hero chain
(`+0x4C` -> heroObject -> `+0x14` -> context -> concreteType/storage) finds
many valid chains near the hits — the client has hundreds of registered GOM types
in that heap, so a chain is easy to stumble into and proves nothing. The two that
were probed for `conContents` turned out to belong to unrelated classes whose
`conContents` is a wide-character path, not a container map:

```
cand D6BABE54  010 01 00 00 00 ... 0c 00 00 0c 00 00 00 00 00 32 00 00 00
              040 20 00 5c 00 73 00 70 00 6e 00 ...   <- UTF-16 " SPEC \spn\c"
```

### Conclusion: the layout is still unknown, and the staged code should not be trusted

The `record+0x10` route is **falsified** — it was read off a 0x20-byte stride in
a live neighbourhood dump without confirming the stride, which is precisely the
"built on an invented layout" mistake this investigation has already retracted
once. The probe's validation would have caught it at runtime and printed a
failure, but it would have consumed a run to learn nothing.

**What this means for the next step.** Three candidates, in order of preference:

1. **Send the native assembly.** The specific thing wanted is the client's
   container/ClassRef resolution — the function that turns a `NodeRef` into a Hero
   node. The `_JPEXTRACT` HeroScript is the layer *above* this and cannot show it;
   `Diagnostics/jedipedia-*.html` is the public game site with zero hits for
   `conContents` or `ablContainer`. If assembly for the GOM/container accessors can
   be exported, that is ground truth rather than another inference.
2. **Let the probe scan and report structure.** Make the probe walk memory around
   the ClassRef target and print *every* candidate record with its id pair, so the
   layout is read off the real thing. Costs one run but cannot be wrong.
3. **Abandon live resolution and note it.** The container encoding is already
   proven offline; the remaining gap is only the in-memory read.


## The node layout, established from the known player id

Found offline by checking the *known* record against its *known* id, which needs
no assumption at all. The manager pointer is at `image+0x10929DC`; the character
tree node is reached at `manager+0x04`:

```
manager+0x04 = E9CDC720
   t+0x00 = 01331154      t+0x10 = 218A839B   <- id low
   t+0x04 = 013313D0      t+0x14 = 4000010E   <- id high
   t+0x08 = 013313F0      t+0x18 = D2980018   <- object/character pointer
   t+0x0C = 459C6F2D      t+0x1C = 04C67850   <- tree root at +0x0C
   id at t+0x10 = 4000010E_218A839B
```

That is the player, whose id `0x4000010E218A839B` is independently known and is
the very key `resolvePlayerFieldAddresses` searches for. So the node layout is
**confirmed, not inferred**:

```
node+0x00  left child
node+0x04  right child
node+0x08  (third link)
node+0x0C  tree root / parent link
node+0x10  id low  \
node+0x14  id high  }  the searched key pair
node+0x18  live object pointer
node+0x1C  secondary pointer
```

This is why the earlier record-id route failed: the container's record was being
read as `id@+0x10, node@+0x18`, but the record found near the id was a **different
structure** (0x30 bytes, `rec+0x04 = 40000004` is a vtable slot). The nodes the
resolver walks are a BST, and the container's node is somewhere in that tree — not
adjacent to a raw id in a flat array.

### What is still needed, precisely

The tree is a BST keyed on the id pair. Given a *node id* rather than a character
id, the route is a plain BST search from the root — the same walk already in
`resolvePlayerFieldAddresses`, with a different target. So the remaining question
is only: **what is the live node id of the ability container**, and the answer is
already in hand:

```
chrPlayerCharacter.f148 ablContainer = 0x400000118A7E6088
```

That is a *field* id naming a slot on the player, whose ClassRef value points at
the container's *node*. If the container's node id is a BST key in the same tree,
the search finds it directly and no record-layout guess is needed at all.

**So the concrete ask for assembly, in priority order:**

1. **The ClassRef/`NodeRef` dereference routine** — whatever turns a stored
   ClassRef value into a live node handle. The value read at f148 was
   `0xE642BF80` (4 bytes, 32-bit process). Knowing what that is, and whether it
   is a BST key or a direct object pointer, is the single missing fact.
2. **The container's own node id** if the client stores it anywhere reachable —
   e.g. the id table entry or the `conSlotted` registration that
   `ablContainerComponentClassMethods.txt` implies via `FindSlotByID`.
3. Failing both, the **GOM node/ClassRef class layout** (vtable + members) so the
   record can be read directly.

Item 1 is the one that closes this. It is a small function — a load, a mask, and
a lookup — and everything else follows from it.

Option 1 is best if the assembly is available, because it is the only one that
cannot repeat this failure mode. Option 2 is the safe fallback.

### What `_JPEXTRACT` and Jedipedia can and cannot answer

## The container node chain, established end to end (offline)

The BST was walked in full from the root and the container located. This is the
complete, verified route:

```
f148 (chrPlayerCharacter.ablContainer, 0x400000118A7E6088) -> 0xCAA10608
  4-byte value                                          -> 0xD6BABEA0   (object pointer)
  obj+0x00        = 0xEB1AA214   heroObject
  heroObject+0x14 = 0xEC93F380   context
  context+4       = 0xEC164700   concreteType
  context+8       = 0xD1752410   storage
  concreteType+0x4C/+0x50/+0x9C -> id table (13 ids) and descriptor array
```

**`obj+0x00` is the heroObject.** That is the missing link, and it is why every
previous attempt failed: the object does not sit at `character - 0x50`, is not
found by a back-pointer scan (**0 validated candidates** — verified, not assumed),
and is not a BST key (`0xD6BABEA0` has no matching high word; the tree's key high
words are `0000001A`, `00000000`/3B9B…, and `4000010E`). The heroObject is simply
the object's own first dword.

The resulting class is unambiguously a container — 13 ids, all con*:

```
conContents  conMaxSize  conSharedData  conContentsRepPrevious  conSlotByID
conSlotsByTimer  conSlotsBySpec  conContainerSpecName  conOwnerNode
conRestrictedSlots  conExpansionLevel  conContainerType  conSlottedBeingCreated
```

### The finding that changes the plan: the live map is not the wire map

`conContents` on this live object reads:

```
D1752428: c0 2c f3 ec 80 30 bb d6 80 2c f3 ec 40 2c f3 ec
D1752438: c0 2e f3 ec 80 2e f3 ec e0 ff 97 fe 40 2e f3 ec
D1752448: 01 00 00 00 00 00 00 00 00 00 0c 00 00 0c 00 00
D1752458: 00 00 00 00 00 00 00 00 2f 00 61 00 6e 00 69 00
          -> UTF-16 "/ani/droid/new/droid_prototype/ad_route_360.jb"
```

That is a **runtime C++ container's internals** — bucket pointers, a count, and
an inline character buffer — not the serialized `count + N x (slot, node ref)`
form the wire carries. The two are the same data in different representations.

**This is the important consequence, and it corrects the premise of the phase (2)
plan.** The handoff assumed the live `conContents` could be dumped and diffed
byte-for-byte against the 208-byte capture. It cannot: the capture is the
*serialized* form produced when the server wrote the packet, and the client's
memory holds the *live* map. A byte diff was never going to match, no matter how
correct the resolver became. The right comparison is structural — read the
runtime map's entries out and check they are the 27 ability slots — not raw bytes.


## conSlottedClassMethods: the container API, and a corrected model

`_JPEXTRACT/conSlottedClassMethods.txt` (19 KB) is the class that owns
`conContents`, and it settles the *semantics* completely even though, like the
other extracts, it is HeroScript and shows no byte layout.

### `conContents` is a reverse map: node -> slot, not slot -> node

This is the correction. Every consumer reads it as an index from a node to its
slot:

```heroscript
public method FindSlotByID(a1 as NodeRef of conContainableComponent) as Integer
  var lookup = Me.conSlotByID
  if lookup has a1
    return lookup[a1]
  else
    return 0
  .
```

Note it consults **`conSlotByID`**, a *separate* field, and not `conContents`.
`onObjectAdded` maintains both:

```heroscript
public method onObjectAdded(Me, a1 as NodeRef of conContainableComponent, a2 as Integer)
  if Me.conContents has a2
    Me.onObjectRemoved(a1, a2)
  .
  Me.conSlotByID[a1] = a2
  var id1 = a1.GetSpec()
  Me.conSlotsBySpec[id1][a2] = true
  .
```

And `_prebuildConSlotsBySpec` rebuilds the two indices *from* `conContents`:

```heroscript
  var lookup3 = Me.conContents
  foreach key in lookup3
    var cur = lookup3[key]
    if cur != None
      lookup2[cur] = key          <- conSlotByID[cur] = key
      var id1 = cur.GetSpec()
      lookup[id1][key] = true     <- conSlotsBySpec[spec][key] = true
    .
  .
```

So the real runtime structure is **three** maps, not one:

| field | type | keyed by | value |
|---|---|---|---|
| `conContents` | map | **slot index (Integer)** | NodeRef of conContainableComponent |
| `conSlotByID` | map | **NodeRef** | slot index (Integer) — the reverse index |
| `conSlotsBySpec` | map | spec ID | map of slot index -> true |

`conContents` is still slot-keyed, which matches the wire encoding. But the
*reverse* index `conSlotByID` is the cheaper thing to walk when the question is
"what is in this container", and it is keyed by the node pointer itself — exactly
the value the f148 ClassRef gave us.

### Two useful facts for the effect reader

- `GetContents()` returns only non-null entries:
  `foreach key in lookup / var cur = lookup[key] / if cur != None / add back cur`.
  So a null value means an occupied-but-empty slot, not an absent one.
- `GetContentsLength()` returns `Me.conContents.length` — the live entry count,
  which for the ability container should be **27**, against `conMaxSize` = 256.
  That is the cheapest possible structural check: one read of two fields
  confirms the container resolved, without walking the tree at all.
- `conSharedData` is a *node* (it has methods: `CalculateTotalSlotCount`,
  `GetExpansionCost`, `GetSlotCountForExpansionLevel`), not a raw id. So the
  `conSharedData` field in the wire capture, which carried an `E000...` value,
  is a ClassRef to that node.

### What this does and does not settle

**Settled:** the field roles, the map keying, that `conContents` is slot->NodeRef,
that `conSlotByID` is the reverse index, that null values mean empty slots, and
that the live entry count is directly readable.

**Still open, and it is now a much smaller question:** the byte layout of a
`std::map` node in this binary — where `pair<const int, NodeRef>` sits relative to
`_Parent`/`_Left`/`_Right`, and where the header keeps root and size. That is
still only answerable from native code or from a dump of a known container.

The `conSlotsBySpec` third map also hints at `_RepairContainerIndexLists` being
touched when the indices disagree, which is worth watching for if a walk ever
returns a count that does not match.


### `conContents` is a `std::map`, and that is now identifiable


## conSlotted field types from Jedipedia: the three-map model was wrong

The `_JPEXTRACT/conSlottedClassMethods.txt` bodies read as if `conContents`,
`conSlotByID` and `conSlotsBySpec` were three separate runtime maps, and I wrote
that down as a correction. **Jedipedia's field table shows that is a
misreading**, and it matters because it changes what the walk has to find.

Declared types:

```
conContents            LookupList indexed by Int of NodeRef of conContainableComponent
conMaxSize             Int
conSharedData          NodeRef of conContainerData
conContentsRepPrevious LookupList indexed by Int of NodeRef of conContainableComponent
conSlotByID            LookupList indexed by ID of Int
conSlotsByTimer        LookupList indexed by String of LookupList indexed by Int of Boolean
conSlotsBySpec         LookupList indexed by ID of LookupList indexed by Int of Boolean
conContainerSpecName   ID
conOwnerNode           NodeRef
conRestrictedSlots     LookupList indexed by Enum conSlotId of LookupList indexed by ID of Boolean
conExpansionLevel      Int
conContainerType       Enum ConPersistentContainerType
conSlottedBeingCreated Boolean
```

All thirteen ids match the live container field-for-field
(`0x400000027E3ED716`…`0x40000035535E3EE0`), so the schema in CRT1 and the
client agree, and the class is confirmed.

### `conContents` and `conContentsRepPrevious` are the same shape

Two fields, identical type: `Int -> NodeRef of conContainableComponent`. That
pair is almost certainly the **current and previous** contents, and it is very
likely the mechanism behind the `flags=0x09` delta encoding that is still open:
an update record would carry the new value against the retained previous one.
`conContentsRepPrevious` is the field to read next time the delta count needs
explaining — it is a replication-only field ("Shared with server DOM: yes" on
the class), so it should not appear in a create capture, which is consistent with
it being absent from CRT2.

### The indices are derived, not independent

`conSlotByID` is `ID -> Int` and `conSlotsBySpec` is `ID -> (Int -> Boolean)` —
both keyed by **ID**, not by the node reference. In HeroScript
`conSlotByID[a1]` took a `NodeRef`, which is the VM coercing a NodeRef to the ID
that names it. So the runtime picture is: `conContents` is the authority, and the
other two are lookup structures derived from it, rebuilt by
`_prebuildConSlotsBySpec` when the lengths disagree.

That is good news for the reader: **`conContents` is a single flat
`LookupList<Int, NodeRef>`**, which is the same shape as the wire encoding, and
the derived indices need not be read at all.

### Revised, and now better-grounded

The pass/fail check does not depend on any of this layout detail:

1. f148 (`0x400000118A7E6088`) on the player — **verified**
2. 4-byte ClassRef value — **verified**
3. `obj+0x00` = heroObject, then the existing chain — **verified**
4. `conContents.length` and `conMaxSize` — expect **27** and **256**
5. Only then walk the `Int -> NodeRef` entries for slot-to-node detail

Step 4 is two field reads with no layout assumption, and `LookupList.length` is
the one primitive the HeroScript uses most (`conContents.length` appears in four
separate methods as the validity check). It is the cheapest decisive test
available, and it does not depend on the red-black node layout at all.

The object at the resolved address is an MSVC `std::map` header, not a serialized
buffer:

```
M+00 = ECF32CC0   M+10 = ECF32EC0   M+20 = 00000001
M+04 = D6BB3080   M+14 = ECF32E80   M+24 = 00000000
M+08 = ECF32C80   M+18 = FE97FFE0   M+28 = 000C0000
M+0C = ECF32C40   M+1C = ECF32E40   M+2C = 00000C00
```

The first four dwords are node pointers, `M+0x20 = 1` reads as a count, and the

## The probe, as built: a count check, not a byte diff

`SWTOR_TRACE_ABILITY_EFFECTS=1` now does four verified steps and stops at a
single field read. No layout is assumed anywhere in it.

```
1. f148 on the player, field id 0x400000118A7E6088     verified
2. 4-byte ClassRef value -> container object             verified
3. obj+0x00 -> heroObject -> context -> concreteType      verified
4. conContents.length, compared against 27               NEW
```

Step 4 is the point. The live `conContents` is a `std::map` whose node layout is
**not known**, and every previous failure came from assuming it. The entry count
is a single field read, and it is the same validity check the client itself
performs — `conContents.length` is compared against the derived index lengths in
four separate conSlotted methods.

Both candidate size offsets (`+0x14` and `+0x20`) are read and **both printed**,
so the log shows which is populated rather than the code asserting one and being
wrong a fourth time. The map header's first 0x40 bytes are dumped with it, so the
subsequent walk has its starting evidence in the same log.

`conMaxSize` is resolved alongside so capacity appears next to the count.

### What the offline dump says about the expected value — and a caveat

Measured on `tython-live-current-34984.dmp`, at the verified address
`0xD1752428`:

```
+14 = ECF32E80 (a pointer)   +20 = 00000001
```

So `size@+0x20 = 1`, **not 27**. Two things follow, and both matter:

1. `+0x20` is the populated size field, so the probe's fallback picks the right one.
2. That dump is a **2026-09-24 live session**, not the CRT2 capture session. A
   container holding 1 entry then is a fact about that session, not a defect in the
   check. The 27 figure belongs to the captured state.

This is worth stating plainly because it cuts both ways: the check will report
`FAIL` if a run's live container legitimately holds a different number of
abilities, and that would be a **finding about the run**, not a probe fault. The
capture is the 2012 baseline; a live client today may well have a different
ability set. The log makes the reported number and the expectation both explicit
so the distinction is never ambiguous.

A BST walk from the map's first dwords reaches 30-33 nodes in that same dump,
which is in the neighbourhood of 27 but not equal to it — not close enough to
claim a match, and not worth fitting an offset to until the size field is
confirmed. That walk is the natural next step, and this log now carries the
evidence it needs.


## Run 5: a probe bug, not a resolver bug — the wait was being reported as a failure

The probe printed:

```
AbilityEffect pid=73804: chrPlayerCharacter.ablContainer (f148) did not resolve
on the player -- the ref field is missing, so the container cannot be reached this way.
```

and then **stopped emitting at log line 572**, while the resolver in the same log
did not report SOUND until **line 792**. The ordering is the whole finding: the
probe gave up roughly 220 lines before the player was even resolvable.

`resolvePlayerFieldAddresses` returns 0 while the character tree has no player
entry, which for tens of seconds is the normal state during world entry. The probe
treated that as "the ref field is missing" and, worse, kept asserting it every
five seconds for the rest of the run.

Two defects, both mine:

1. **Wrong diagnosis.** "The field is missing" and "the player has not loaded yet"
   are different things, and the message picked the one that was wrong. That is the
   same class of error as the retracted "register contention" theory in this file:
   a missing value explained as a defect in the thing being measured.
2. **No recovery.** A transient condition was treated as terminal, so the run
   produced no measurement at all.

Fixed by announcing the wait once per process (`abilityEffectWaiting`), wording
it as a wait rather than a fault, and continuing to retry on the existing 5s clock.
The probe now prints "waiting for chrPlayerCharacter to resolve… keeps retrying"
and then "chrPlayerCharacter resolved, proceeding to f148" when it succeeds.

This is the first failure in this work caused by the probe rather than by the
data, and it is worth recording as such: every previous failure was a wrong

## Correction: the "width bug" was my fourth wrong inference — there isn't one

I claimed `initial=111` was a DWORD-vs-byte reporting fault and proposed fixing
the read width. **That was wrong, and no code change was made.** Both read paths
already read exactly one byte:

```cpp
// snapshot path, line ~1604
BYTE value = 0; SIZE_T got = 0;
ReadProcessMemory(it->second, (void *)resolved[field], &value, 1, &got);

// event path, line ~3775
BYTE value = 0; SIZE_T got = 0;
ReadProcessMemory(process, (void *)resolved[field], &value, 1, &got);
```

and so does the poll. So `111` is not a misread width. Decoding it as hex:
`111 = 0x6F`, `6 = 0x06`, `15 = 0x0F` — ordinary byte values, which a
one-byte read returns faithfully.

The offline dump at the same offsets shows what those bytes should be:

```
storage+0x9D4 = 01     ablUserCacheIsLucid            = 1
storage+0x9D5 = 00     ablUserCacheGlobalTimerRunning = 0
storage+0x9DA = 01     ablUserCacheIsFrozen           = 1
```

Three adjacent one-byte Booleans, three adjacent offsets — the reads land within
six bytes of each other and pick up neighbouring values. That is what a stale
address looks like, not a formatting problem.

### The actual state of things

Verified against the offline dump, the resolver is **correct**:

| field | offline offset | live log offset | |
|---|---|---|---|
| chrPlayerLoaded | `0x1006` | `0x1006` | match |
| ablUserCacheIsFrozen | `0x9DA` | `0x9DA` | match |
| ablUserCacheIsLucid | `0x9D4` | `0x9D4` | match |
| ablUserCacheGlobalTimerRunning | `0x9D5` | `0x9D5` | match |

So the address arithmetic and the descriptor indexing are right, and the
byte-width handling is right. What is unexplained is the *values* in one
particular run: the same offsets that read 1/0/0 in the 2026-09-24 dump read
0x6F/0x06/0x0F in the 2026-09-25 run. The most likely explanation is the
concrete type or storage differing at that moment — the run reports
`idIndex=559` for IsFrozen where the dump has 561, so the two are not the same
type instance — but that is a hypothesis, not a conclusion, and it needs the
run's own addresses compared rather than the dump's.

### On the process failure

This is the fourth consecutive wrong inference about the same log, and the
pattern is consistent enough to name:

1. "the probe stopped at 572" — it ran to 1021; I read a filtered tail.
2. "f148 did not resolve is a timing problem" — unproven, contradicted by the

## SOLVED: the container encoding, and the flags=0x09 fork, from Tools/Hero

The repo already contains a reference implementation of this encoding, and it
answers everything that was open. `Decode-CrtValues.py` is a reimplementation of
`Tools/Hero`; it now cites that code as the authority, and the two agree.

### Packed integers — `Tools/Hero/Hero/PackedStream.cs::Read(out ulong)`

```csharp
if (TransportVersion > 1) {                       // PackedStream_2 pins 5
    if (num1 >= 192) {
        if (num1 < 200 || num1 > 207)
            throw new SerializingException("Invalid token in stream");
        ReadPacked(out value, num1 - 199);
    } else value = num1;
} else if (num1 >= 128) { ... 175 + length ... }
else value = num1;
```

So, at the version these captures use: `< 192` literal, `0xC8..0xCF` carries
1..8 big-endian bytes, and **`0xC0..0xC7` (192..199) raise**. The handoff's
retraction of the signed-byte hypothesis was correct, and this is where it is
confirmed. `CC` = 204 - 199 = 5 bytes, which is exactly the 5-byte node in the
capture, and `CF` = 8 bytes for the shared refs.

Note the scheme is **version-dependent**: version 1 uses a 176-base instead. That
is a second reason not to treat any single token table as universal.

### Container counts — `SerializeLookupList.cs` / `DeserializeLookupList.cs`

```csharp
// writer
if (stream.Style == 8 || stream.Style == 10) stream.Write(Count * 2, Count * 2);
else                                        stream.Write(Count, Count);
// reader
this.m_30 = (Count & 1) == 1;
this.Count = Count >> 1;
```

**This is the `flags=0x09` fork, and it is not a delta count.** The earlier
reading — "13 changed, 6 present on the wire" — was invented and wrong. The
leading `0x0D` is simply `6 * 2`: the count is doubled on those styles and the
low bit is a flag. Verified end to end:

```
CRT4 obj2  effContainer 0x1AC6F6DC10  43/43  PASS
   conContents [6]{1:0x1AC6F6DC2D, 2:0x1AC6F6DC36, 3:0x1AC6F6DC47, ...}
```

Six entries, where the raw byte said thirteen. The keys and refs it now prints
are the six effect nodes the same capture creates, which is a further check the
decoder did not have to be told about.

### The style is the single discriminator for both differences

| | style 7 (CRT2 creates, flags 0xAA) | style 8/10 (updates, flags 0x09) |
|---|---|---|
| field states | 1 bit per field | 2 bits per field, with run codes |
| container count | plain | doubled, low bit a flag |

Both CRT4 records report `style=8`. Under 1-bit they read `[2,1,1,1,1]`
(conContents *absent*, 9 of 43 bytes); under 2-bit they read `[1,2,2,2,2]`, which
is correct once the count is also halved. Two independent differences, one
discriminator. This is why the earlier "the state word disagrees with the body"
observation was a real signal rather than noise — it was pointing at the style.

### Final state: 16/16 containers

```
python Diagnostics/Decode-CrtValues.py --containers    ->  containers: 16/16 pass
```

Every container in every capture reconciles to its exact `inner_size` and lands on
an entry boundary, and the tool exits 0. Phase (a)'s container half is complete,
and it is now validated against the project's own implementation rather than only
against byte arithmetic.

   probe retrying successfully on its own clock.
3. "the resolver reads the wrong addresses past the start of a type" — the
   offsets match exactly.
4. "the value read is a DWORD width bug" — every path already reads one byte.

In each case the claim came from a partial view, and in each case checking the
whole artifact first would have prevented it. The next claim about this log
should be made only after reading it end to end.

assumption about layout, and this was a wrong assumption about *timing*. Both
produce the same visible symptom, an empty log, and neither is visible without
reading the whole file rather than the last few lines.

UTF-16 at `M+0x38` (`/ani/droid/...`) is an inline string from the surrounding
allocation. The node-pointer density plus the count is the `std::map` shape, and
`conMaxSize` reads `00 01 00 00` = 256.

**I am stopping here rather than continuing to guess the node layout.** Two
consecutive offset assumptions (0x20-byte records, then the `_Myhead` sentinel
position) both failed, and a third guess would be the same mistake twice over.
What is established is enough to be useful and is all verified:

| Fact | Status |
|---|---|
| f148 field id `0x400000118A7E6088`, addr `0xCAA10608` | verified |
| ClassRef is 4 bytes, value `0xD6BABEA0` | verified |
| `obj+0x00` = heroObject | verified |
| `heroObject+0x14` → context → concreteType/storage | verified |
| concreteType has 13 con* ids incl. `conContents` | verified |
| `conContents` is an MSVC `std::map` | verified |
| map node layout (value/parent/left/right offsets) | **open** |

**The one thing that closes it, and it is a single field:** the offset of
`std::pair<Key,Value>` inside the tree node, i.e. where the key (the slot index)
sits relative to the `_Parent`/`_Left`/`_Right` pointers. For `std::map<int,NodeRef>`
that is the standard MSVC layout, and the reader is a short in-order walk, but
"standard" is exactly the word that has burned this investigation three times.

Assembly for the container's accessor — or failing that, one more run with a
probe that dumps a few candidate node addresses and their surroundings — settles
it definitively. The offline work above does not need repeating either way.

So the resolver work was not wasted: the chain above is real, verified, and it is
exactly what a structural reader needs. What must change is the last step, from
"dump raw bytes" to "walk the runtime map".

Note also that the BST dump contains `id=0000001A_C6F6DC6D` — that is
`0x1AC6F6DC6D`, the **quest giver** the handoff asked about, present as a live
node in the character tree. The quest-giver gap is therefore a *replication*
problem (the data was never sent), not a lookup problem, which matches the
"content gap, not a protocol one" conclusion already reached.

### What the phase (2) probe should become

1. Resolve f148 on the player (works; proven).
2. Read the 4-byte ClassRef (proven).
3. `heroObject = obj+0x00`, then the existing chain (proven).
4. Resolve `conContents` (proven) and read the **runtime map structure** — the
   count and the key/value entries — rather than the wire encoding.

Step 4 needs the runtime map's own layout, which is the one thing not yet
determined. The class is confirmed and the field is confirmed; only the internal
arrangement of the map object is open.


Checked properly, since the layout was the open question:

- `_JPEXTRACT/*.txt` is **HeroScript method bodies** — the gameplay layer. `NodeRef`
  appears 81 times in `ablUserComponentClassMethods.txt`, all script-level handles
  passed between methods. The Hero node, the object pointer, the 0x20-byte record
  and the `+0x10` id offset are native C++ structures *beneath* the VM and appear
  in no script. It usefully documents the slot-type routing
  (`effCOntainerComponentClassMethods.txt`: `GetContainerForEffect()` switches on
  `GetEffectSlotType()` and returns `effContainerPositive/Negative/Other`, i.e.
  the three effect containers hang off the *player*, not off f148 — relevant to the
  effect reader later), but not the node layout.
- `Diagnostics/jedipedia-*.html` is the public game site (patch notes, 6.5 MB of
  release 48). Zero hits for `conContents` or `ablContainer`. The C++ comment
  citing Jedipedia at line 938 is about field metadata only.

Neither can answer a native layout question. That has to come from memory, which
is why the dump stays in the probe.


### What is still unverified

`f148` at `CAA10608` holds `0xD6BABEA0`, which is a **mapped object pointer**, so
the two-hop shape is right: player -> f148 -> container object. But the container
hero node was not recovered from this dump, so the final hop
(`resolveFieldAddressesForNode` -> `conContents`) remains unexercised. The
back-pointer relationship the existing scan relies on did not present for this
object in this dump; the two references to `0xD6BABEA0` found are a weak-ref slot
and a vtable-adjacent entry, neither of which yields the hero chain.

So: the *route* is now understood and the *ids* are now correct, but the live read
still has to happen. A run is required — the question was whether one was needed
*before* fixing, and the answer turned out to be "no": the dump found the id
defect that had to be fixed first.

### Corrected target for the next run

```
chrPlayerCharacter.f148  ablContainer  0x400000118A7E6088   (NOT 0x40000002F8C347F1)
  -> f0 conContents     ClassRef      0x400000027E3ED716
```

non-functional. Worth a separate look, deliberately not conflated with the
ability-effect work.

   resolution routes agree, so the address itself is trustworthy.
3. `conContents raw N bytes: 1B01CC1AF6F6DBD8...` — **the comparison.** The
   capture is `1B` then 27x(`CC`+5) then 2x(`CF`+8) = 208. A live value starting
   `1B 01 CC 1A C6 F6 DB D8` matches the encoding already proven offline.

If (3) differs, the cause is the node reference, not the field — that is the
conclusion this probe exists to make falsifiable.
