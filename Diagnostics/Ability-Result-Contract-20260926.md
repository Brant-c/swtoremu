# Ability cast completion — server reply contract

Read-only analysis. No packets, fixtures or client memory were modified to
produce this. Every claim below is traced to a file and line.

## Summary

Casts do not complete because the server never answers the ability request.
The client has a dedicated result path that only completes a cast when it
receives an explicit `effResultOk`. There is no timeout fallback, so a silent
server leaves the cast pending indefinitely.

All four existing reply modes (`mirror`, `results`, `echo`, `ack`) fail for
structural reasons, not tuning reasons. See "Why the existing modes cannot work".

## The chain

**1. Request.** `ablOracleClassMethods.txt:145`

```heroscript
public method RequestAbilityActivate(Me, a1 as ID, a2 as ID, a3 as ID, a4 as Integer, a5 as Boolean)
  ...
  call server untrustedMethods:OnRequestAbilityActivate(a2, a3, dateTime1, a4, a5)
```

This is the `sub=29` body observed in the server log. Confirmed working: the
request is decoded, `placed=` resolves a character, and the trailing requestId
counter increments 1, 2, 3 per press.

**2. Client records the pending request.** `ablOracleClassMethods.txt:87-88`

```heroscript
public method unk_5946648b(Me, a1 as Integer, a2 as DateTime)
  Me.ablOutstandingRequests[a1] = a2
```

`ablOutstandingRequests` is `LookupList indexed by Int of DateTime`
(`ablOracle.txt:30`). Response latency is computed on completion
(`unk_49196537`), so the client is explicitly waiting for a reply.

**3. Server replies on a separate endpoint.** `ablOracleClassMethods.txt:344`

```heroscript
remote function OnQueuedAbilityResult(Me, a1 as ID, a2 as Integer, a3 as Enum effResult)
  var pc = GetPlayerCharacterNode()
  if pc != None
    pc2.HandleAttemptQueueAbilityResult(a1, a2, a3)
```

**4. Cast completes or cancels.** `ablUserComponentClassMethods.txt:2000`

```heroscript
public method HandleAttemptQueueAbilityResult(Me, a1 as ID, a2 as Integer, a3 as Enum effResult)
  if a3 == effResultOk
    Me.AttemptQueuedAbility(a1, a2)
    Me.SetQueuedAbilitySpec(0)
  else
    var node3 = $ABILITY.GetAbility(a1)
    if node3 != None
      var id1 = node3.GetAbilityEffectSpecByNumber(0)
      Me.VerifyAbilityActivation(id1, a2)
      if a3 != effResultMiniqueueCleared
        if Me.IsCastingAppearanceInUse(id1, a2)
          if not Me.ablUserEffectEvent_Client.effEventDoNotCancel
            Me._InternalAbilityCancel(cbtOutcomeCancelled, a2, true)
```

Any result other than `effResultOk` (bar `effResultMiniqueueCleared`) reaches
`_InternalAbilityCancel`. No reply at all means neither branch runs.

## The reply payload

`onQueuedAbilityResult(ASSEMBLY).txt` — the `!sep` variant is the unpacking
shim the engine calls after decoding an inbound RPC:

```asm
OnQueuedAbilityResult!sep(Me, a1, a2, a3)
  MOV EAX, [ESP+0x2C]        ; pointer to the argument block
  MOV ECX, [EAX]             ; dword 0
  MOV EDX, [EAX+4]           ; dword 1
  MOV ESI, [EAX+8]           ; dword 2
  MOV EDI, [EAX+0xC]         ; dword 3
  MOV EAX, [EAX+0x10]        ; dword 4
  ; pushed in reverse, then:
  CALL OnQueuedAbilityResult
```

**Five dwords, 20 bytes.** No length prefix, no name string. Because the shim
pushes in reverse, dword 0 becomes the highest argument:

| Dword | Maps to | Notes |
|-------|---------|-------|
| 0 | `a1 as ID` (low) | 64-bit |
| 1 | `a1 as ID` (high) | |
| 2 | `a2 as Integer` | |
| 3 | `a3 as Enum effResult` (low) | **64-bit, see below** |
| 4 | `a3 as Enum effResult` (high) | `effResultOk = 0` remains a hypothesis |

`Me` is not in the block: `OnQueuedAbilityResult!sep` loads it from
`[ESP+0x28]`, separately from the argument block at `[ESP+0x2C]`.

`effResult` occupies **two** dwords, not one. `OnAbilityResult` (line 358) calls
`HM.ValidateEnum64(17, a5)` on its enum argument, and `OnRequestAbilityActivate`
serializes a `DateTime` as a 64-bit `EAX:EDX` pair — 64-bit values are common
and this enum is validated as one.

`OnAbilityResult!sep` reads ten dwords for its five-argument signature
`(ID, Int, ID, Int, Int)`, consistent with "each 64-bit value costs two
dwords". The outbound side confirms the serializer: `RequestAbilityActivate`
emits `RPCSerializeID`, `RPCSerializeID`, `RPCSerializeDateTime`,
`RPCSerializeInt`, `RPCSerializeBoolean` for `(ID, ID, DateTime, Int, Boolean)`
— 8 dwords, no padding.

## effResultOk = 0

`effResult.txt` lists 88 values in declaration order. Serialization as
sequential integers is the usual convention for engine enums, and
`effResultOk` being first is consistent with 0 meaning "no error".

```
[  0] 0x00  effResultOk
[  1] 0x01  effResultError
...
[ 73] 0x49  effResultNotReadyQueue
[ 85] 0x55  effResultMiniqueueCleared
```

**This is inferred from declaration order, not confirmed.** Jedipedia publishes
names, not ordinals. If a reply carrying 0 produces no effect, try 1 and read
`ablUserLastResult`.

## Why the existing modes cannot work

`CMsgF96DCDB0.cs` applies one uniform policy to every request type, with no
`sub` dispatch. Two independent problems:

**1. `echo` and `ack` send the wrong opcode.**
`AreaRPCPollAck.GetType()` returns `PacketType.CMsgF96DCDB0` — a
client-to-server opcode. The client has no inbound handler for its own request
opcode. The file comment already concedes this: "this reply is non-canonical".

**2. `mirror` and `results` use the wrong framing.**
`SMsgResults` writes two strings (result name, result value) and routes via
the Omega base proxy 0x65A7. A remote-function invoke carries a typed argument
block, not two strings. In `mirror` mode `ExtractNameBlob` reads the first
four bytes of the request as a length — `0x00000029` = 41 — and copies 41
bytes from a 45-byte body, so the "name" is the packed RPC id plus the
trailing counter rather than a readable name.

`SWTOR_RPC_REPLY_MODE=swallow` is the active setting, so the only two modes
that emit a real server opcode (`SMsgResults`) have never run against
`sub=29`. Every observed ability attempt was swallowed or echoed with the
wrong type.

## 2026-09-27 offline contract audit

This section supersedes the dword-order table above where they disagree.  No
reply packet was added.

### Captured request, field by field

The first complete activation at `last-server-full.log:1208-1214` is:

```
29 00 00 00                                      frame length = 41
C7 71 C3 79 12 D5 03 17 00                       opaque request procedure selector
01 CF 40 00 01 0E 21 8A 83 9B                    ID 0x4000010E218A839B
01 CF E0 00 9B 0D F2 9A 7B A2                    ID 0xE0009B0DF29A7BA2
15 CD 0C 38 10 39 AB 84                          DateTime
02 01                                               request ID = 1
03 00                                               Boolean = false
```

The following thirteen requests retain the same selector and player ID.  The
second ID switches between observed ability specifications, the DateTime bytes
increase, the value after `02` increments exactly from 1 through 14, and the
value after `03` alternates between 0 and 1.  This independently fixes all five
serialized values without assigning an unsupported byte order to the opaque
procedure selector.

Relative to the public HeroScript entry point
`RequestAbilityActivate(Me, a1, a2, a3, a4, a5)`, `a1` is the acting
character and is not serialized by the inner server call.  The inner call is
`OnRequestAbilityActivate(a2, a3, dateTime, a4, a5)` and the wire contains two
typed IDs, the synchronized time, request ID, and queue Boolean in that order.
The bytes establish the meanings of the two IDs: the first is the selected
player/target ID and the second is the ability specification consumed by the
ability path.  They do not justify renaming the decompiler's `a2`/`a3`
temporaries beyond the source call shown above.

The leading `29 00 00 00` is a frame length, not a subtype.  The current
handler calls it `sub=29` only because it reads the first byte of the framed
body.  `29` is hexadecimal `0x29`, or 41 decimal; it is not decimal 29 and is
not wire value `0x1D`.

### `OnQueuedAbilityResult!sep` argument block

The shim reads exactly five dwords from offsets `+0x00` through `+0x10`.
There is no sixth or trailing dword.  The correct mapping is:

| Dword | Argument | Ordering evidence |
|---|---|---|
| 0 | `a1 as ID`, low dword | the companion `RequestAbilityActivate!sep` passes its first ID dword in the normal x86 low slot |
| 1 | `a1 as ID`, high dword | second half of the ID |
| 2 | `a2 as Integer` | the activation request ID/correlation key |
| 3 | `a3 as Enum effResult`, low dword | enum is passed as a 64-bit Hero value |
| 4 | `a3 as Enum effResult`, high dword | second half of the enum value |

This corrects two errors in the earlier table: it labelled the ID halves
high/low in reverse and displayed a nonexistent dword 5.  `Me` remains a
separate shim parameter and is not part of this 20-byte block.

`effResultOk = 0` remains a hypothesis.  `effResult.txt` supplies declaration
order but no numeric ordinals, and no authoritative ordinal table was found.

### Existing server-to-client typed RPC envelope

The protocol implementation does already contain the generic inbound envelope:

- `PacketType.AreaRequestRPC = 0x0ADFF9BF`;
- `AreaRequestRPC.WriteImplementation()` writes the area component, an `Int32`
  blob length, and the opaque typed RPC blob;
- `AreaStartupBundle` sends several captured instances successfully;
- the parser's `HandleAreaRequestRPC` calls `ReadFrame`, then reads a procedure
  selector followed by typed values.

Therefore the missing primitive is not the outer packet class.  It is the
inner selector and authoritative serialization for this particular remote
function.

The activation request cannot supply that selector.  Its opaque selector is
for the opposite-direction endpoint, `OnRequestAbilityActivate`; completion
must address the distinct client remote function `OnQueuedAbilityResult`.
None of the existing captured `AreaRequestRPC` blobs is identified as that
function, and the script/assembly export exposes the `!sep` argument layout but
not its native wire selector.  The old parser is also insufficient as an
encoder: its packed-value reader treats `0xC7` as invalid under the generic
integer rules even though captured RPC selectors commonly begin with `C7` or
`CF`.

### Stop condition

Do not construct an `AreaRequestRPC` for ability completion yet.  The exact
remaining unknowns are:

1. the wire selector that dispatches `ablOracle.OnQueuedAbilityResult`;
2. the selector's byte-order/encoding rule (it must not be inferred merely by
   displaying the eight captured bytes as an integer);
3. the typed wire encoding of the 20-byte logical argument block, including
   the 64-bit `effResult` representation;
4. the authoritative numeric ordinal for `effResultOk`.

The narrow external unblocker remains a PCAP/PCAPNG containing one successful
ability press against a functioning compatible server.  Compare its client
activation frame with the immediately following server `AreaRequestRPC` (or
whatever packet actually invokes the result shim).  Process Monitor output
cannot answer this.

## Relevant client state

From `ablUserComponent.txt`. The server must not contradict these.

```
ablActiveRequestId        Int        correlation key; matches the log counter
ablQueuedAbilitySpec      ID         must be non-zero for a cast to be pending
ablCastTimeEnd            DateTime   cast bar deadline
ablCastDuration           Float
ablUserLastResult         Enum effResult
ablUserLastResultMessageTime DateTime
```

`SetQueuedAbilitySpec(0)` runs only *after* success, so the spec is set during
the client's own validation, before the request goes out.

## Diagnostic channel

`_DisplayAbilityResultMessage` surfaces failures by enum name
(`ablUserComponentClassMethods.txt:1053`). Sending a deliberately wrong
`effResult` produces a specific on-screen complaint that identifies how the
client decoded it. This is cheaper than guessing ordinals.

`OnAbilityResult` (`ablUserComponentClassMethods.txt:1886`) is a
four-argument variant whose guard only gates *display*:

```heroscript
public method OnAbilityResult(Me, a1 as ID, a2 as Integer, a3 as Integer, a4 as Enum effResult)
  if (a4 != effResultOk and a4 != effResultNotReadyQueue) and a1 != 0
```

Two inbound paths exist with different arities and different jobs. The
three-argument `OnQueuedAbilityResult` is the one that drives
`AttemptQueuedAbility`.

## Targeting is not the problem

The client reports "cannot buff the NPC when targeted". That is evaluated
client-side against `tgtRule*` checks before any request is sent, which
confirms the ability system, targeting and rule evaluation are loaded and
working. The failure is strictly in the server response path.

## Open questions

1. **The inner selector.** `AreaRequestRPC` is the outer packet type that carries
   a remote-function invoke, but how is this target function addressed?
   `utlOracle` is `ablOracle`'s parent and
   owns `utlOracleHeldMessages`, so it is the likely dispatcher.

   `utlOracle` is an abstract base class with 40 child classes, and its script
   dump contains no inbound dispatch function — all 43 methods in
   `ablOracleClassMethods.txt` are `Request*` initiators or `remote function`
   leaf handlers. The dispatch layer is engine-native, not HeroScript, so it
   will not appear in Jedipedia.

   `RequestAbilityActivate` assembly shows the outbound half:

   ```asm
   MOV dword [ESP+0x4], 0x8E3C86ED
   MOV dword [ESP],    0x2AFCE900
   CALL !HM.RPCBegin
   RPCSerializeID / RPCSerializeID / RPCSerializeDateTime / RPCSerializeInt / RPCSerializeBoolean
   ```

   `0x8E3C86ED` is a shared high half across `untrustedMethods` RPCs; the low
   dword selects the function. **Neither half appears in the transmitted
   activation frame** (verified: the logged bytes contain no `8E3C86ED`,
   `2AFCE900`, `00E9FC2A` or `ED863C8E` in any byte order), so the engine
   rewrites the id before the wire. Resolving this needs the native client
   disassembly or a captured real-server reply, not the script layer.
2. **Wire encoding.** The shim proves a 64-bit logical enum value, but not how
   the generic RPC serializer encodes that value inside an `AreaRequestRPC`
   blob.
3. **`effResult` ordinals.** See above.
4. **Effect replication.** `effResult.txt` lists `effEventResult`,
   `effEventActionDetailsResult` and `effAppearanceResultOverride` as consumers
   of `effResult`, which suggests the *visible buff* travels separately as
   replicated effect state. Both paths may be required for a complete cast.

## Status: 2026-09-26 — parked pending an external source

The logical reply arguments are verified from primary sources. The remaining
unknown, the inner RPC selector and its typed wire encoding, is **not obtainable
from the script layer**. The outer envelope is the existing `AreaRequestRPC`:

- `utlOracle` is an abstract base with 40 child classes; its dump has no
  inbound dispatch function.
- All 43 methods in `ablOracleClassMethods.txt` are `Request*` initiators or
  `remote function` leaf handlers.
- The dispatcher is engine-native client code, so Jedipedia cannot contain it.

### Sources checked and ruled out

- `Diagnostics/Captures/*.pml` and `*.csv` are **Windows Process Monitor
  traces** (`Process Profiling`, `QueryOpen`, `FAST IO DISALLOWED`), captured
  2026-09-10 for asset extraction. They contain file I/O, not network
  traffic. No real-server ability reply exists in the repo.
- A grep for `F96DCDB0`, `OnQueuedAbility` and `untrustedMethods` across the
  converted CSVs returns nothing.

### What is needed to unblock

1. **A network capture from a working server** showing a reply to an ability
   activation. This gives the envelope and argument encoding directly, and is
   far cheaper than option 2. ~30s of world entry plus one ability press is
   enough. The repo has PCAP tooling under `Parser\SWTORParser\` that nothing
   currently wires up to these files.
2. Failing that, **client disassembly** of the inbound RPC dispatch — the
   routine that decodes the argument block and locates a `!sep` shim.
   `0x8E3C86ED` is a useful search anchor.

Do not attempt a hand-built reply packet until one of these is available. The
four historical attempts failed because each guessed a different envelope; a
fifth guess is the same risk.

## 2026-09-27 continuation: exact April script and native receive bridge

The new `utlOracleClassMethods.txt` export closes one ambiguity but does not
contain a dispatcher. Its only message-related methods maintain
`utlOracleHeldMessages`; there is no selector table, decoder, or remote-call
entry point in the HeroScript base class.

The CSV name is not a different script from `_clientablOracleClassMethods`.
`Scriptdef.listdump.csv` row 44 maps the public name
`ablOracleClassMethods` to definition `0xD000EC5D4F0CCB18`, key
`0x54058C0E`; `ablOracle.txt` labels that same definition ID as the client
script. The matching April SDEF contains the same record in variants 0 and 1.
Its SCPT body is:

```
Diagnostics/GomCompatibility/ResourceCacheApril2012/scripts/CD33AD9CDCFA5395.scpt
```

This identity was verified independently from the compiled body: it is the
only April script containing all three `ablOracle`-specific GOM fields
`0x400000016F280971`, `0x40000009F4787F57`, and
`0x4000000A2D7B877A`.

After applying the SCPT v5 decrypt rule, the payload contains the exact x86
exported by Jedipedia. Code virtual offset zero begins at payload offset
`0x66B`; therefore:

| Function | Script VA | SCPT payload offset |
|---|---:|---:|
| `OnQueuedAbilityResult` | `0x3420` | `0x3B3F` |
| `OnQueuedAbilityResult!sep` | `0x3500` | `0x3C1F` |

The pre-code metadata has a distinct table of eight remote functions, matching
the eight `remote function` declarations at the end of
`ablOracleClassMethods.txt`. It supplies function/signature indices but not the
April wire receiver/operation pair. The compiled outbound request still embeds
the Beta logical ID `0x8E3C86ED'2AFCE900`; the April wire for that same call is
`target=0x1279C371, operation=0x001703D5`. This proves that copying the Beta ID
or hashing the method name cannot produce an authoritative reply selector.

Static client tracing now reaches the concrete inbound path:

```
AreaRequestRPC handler 0x0064ED70
  -> derived virtual slot 0x0113F084+4
  -> bridge 0x00642CA0
  -> global interface [0x01491A88], virtual slot 0
```

`Client/Hook/Src/ToR.cpp` now has an opt-in, read-only observer on
`0x00642CA0` under the existing `SWTOR_TRACE_RPC_CALLS=1` switch. It records
the global interface object, vtable, five slot targets/RVAs, both bridge
arguments, and a bounded message dump, then forwards the call unchanged. The
hook builds successfully with zero warnings and zero errors.

The 14:03–14:07 run exercised this observer 11 times. Every call reported the
global interface at `[0x01491A88]` as null. Static code and the live result
therefore agree: `0x00642CA0` skips the global slot and uses the listener stored
at bridge offset `+0x2C`, invoking listener vtable slot `+8`.

The captured message argument is also now identified as the client byte-vector
object rather than the packed bytes themselves. Its vtable is at `+0`, its
logical length is repeated at `+4` and `+0x0C`, and its data pointer is at
`+0x10`. The observed lengths `11, 9, 33, 13, ...` match the startup
`AreaRequestRPC` fixtures exactly. The first observer logged the object bytes,
not the pointed-to blob; this is why its dump began with a vtable pointer rather
than `C7`/`CF`.

The same run captured ability request IDs 1 through 12. Each remained
`target=0x1279C371, operation=0x001703D5` and the server logged
`ability:swallowed`, confirming the diagnostic did not alter the request path.

The observer has been refined and rebuilt to log the `+0x2C` listener object,
its first ten vtable slots/RVAs, and the actual pointed-to RPC blob. The next
run needs only reach area startup; no ability press is required. The decisive
value is `listenerSlotRvas[2]`, the exact implementation called by
`0x00642CA0`. No ability reply should be enabled during this measurement.

That measurement is now complete. Across all 11 startup calls the listener
was stable at runtime object `0x0120AEA8`, vtable `0x00EBF5A4`, with slot 2 at
runtime `0x004855E0`. After removing the live image base and applying the
disassembly's canonical `0x00400000` base, the exact static implementation is
`0x007155E0`. The actual blob dumps match the emulator's startup fixtures.

`0x007155E0` selects synchronous versus queued delivery using byte
`listener+0x0C`. Both modes converge on `0x00715760`. That routine wraps the
raw byte range in an engine stream and invokes virtual slot `+0x74` on the
process-global service rooted at `[0x014926F0]`. This moves the remaining
unknown from a generic network bridge to one concrete engine virtual method.

The observer is refined again to resolve and log that service object, vtable,
slot-`0x74` target, and target RVA. It remains read-only and forwards every
call unchanged. The rebuilt `MemoryMan.dll` completed with zero warnings and
zero errors. The next run again needs only world entry; ability presses are
not required because swallowed ability requests cannot create an inbound
acknowledgement.

## Landed

The 41-byte framed ability activation (`29 00 00 00`, logged by the handler as
`sub=29`) now has its own reply mode in
`CMsgF96DCDB0.cs`, set by `SWTOR_ABILITY_REPLY_MODE`. When unset it inherits
`SWTOR_RPC_REPLY_MODE`, so the current behaviour is unchanged. All decision
log lines are prefixed `ability:` so ability traffic is separable from the
keepalive in the log.

Built clean (0 errors) but **not yet exercised at runtime** — the next run
should confirm no regression and produce `ability:`-prefixed lines.

No `OnQueuedAbilityResult` packet class was written: the RPC id is not
transmitted in a usable form, so constructing one would be guesswork.

## 2026-09-27: exact inbound selector and typed completion implemented

The x86 client path below supersedes the earlier conclusion that the selector
required a real-server capture:

```
0x00715760 (listener synchronous delivery)
  -> service virtual +0x74
  -> adjustor thunk 0x00BD6610
  -> decoder 0x005BDA30
  -> compact signed-64 reader 0x004C9A10
```

`0x005BDA30` reads one style-5 compact signed 64-bit value, maps its high
dword to a loaded script, resolves the recipient, and passes the low dword to
recipient virtual `+0x38` to obtain the method descriptor. This interpretation
is independently confirmed by the first captured startup selector:

```
CF 2B 7E 42 02 2E 10 03 0D
   ^^^^^^^^^^^ ^^^^^^^^^^^
   script hash method hash
```

`0x2B7E4202` exactly matches `_BaseClientClassMethods` in
`Scriptdef.listdump.csv`. Therefore the first packed value is the inbound
script/method selector, not a node id.

The decrypted April `ablOracleClassMethods` SCPT begins with 159 packed symbol
SIDs. The first implementation incorrectly treated an auxiliary table entry,
index `0x50` (`0xD1DD59C2`), as the public function SID. The 2026-09-27 run
proved that interpretation false: the client resolved script `0x54058C0E` but
reported `Unable to find script entry point ... Using Function SID:
3520944578` (`0xD1DD59C2`).

The function-address metadata provides the authoritative mapping. Its entries
for the three adjacent functions are:

```
02 40 00 C9 34 D0   OnQueuedAbilityResult implementation
03 40 00 C9 35 B0   OnQueuedAbilityResult!sep
02 42 00 C9 35 F0   OnCustomGCDActivated implementation
03 42 00 C9 36 B0   OnCustomGCDActivated!sep
02 44 00 C9 36 E0   OnAbilityResult implementation
03 44 00 C9 38 D0   OnAbilityResult!sep
```

Adding the native-code base at payload offset `0x66F` places the first pair at
payload offsets `0x3B3F` and `0x3C1F`, exactly matching the Jedipedia assembly
VAs `0x3420` and `0x3500`. The descriptor number is the index into the opening
SID table: entries `0x40`, `0x42`, and `0x44` are respectively `0xE7DC09C4`,
`0x1C278F1E`, and `0x181B667F`. This interpretation is independently checked
against three startup RPCs that the client already accepts: `_BaseClient`
`0x2E10030D`, `prfOracle` `0x0311A4C8`, and `optOptionsAdapter`
`0x30110385` occur at SID-table indexes `0x44`, `0x5B`, and `0x4A`, and each
SCPT function-address table contains the corresponding descriptor number.
Therefore `OnQueuedAbilityResult` uses public function SID `0xE7DC09C4`.
Combined with the CSV's April script hash `0x54058C0E`, the corrected inbound
selector is:

```
0x54058C0E'E7DC09C4
CF 54 05 8C 0E E7 DC 09 C4
```

The decoder constructs stream style 5. The native typed-argument reader at
`0x005BB3F0` reads a type token before each value when the style-5 type flag is
set. This is also visible directly in captured activation requests:

```
01 <packed ID>       HeroTypes.Id
01 <packed ID>       HeroTypes.Id
15 <packed Date>     HeroTypes.Date (0x15)
02 <packed Integer>  HeroTypes.Integer
03 <packed Boolean>  HeroTypes.Boolean
```

Consequently the completion body is:

```
CF 54 05 8C 0E E7 DC 09 C4
01 <packed ability-spec ID>
02 <packed request ID>
05 01
```

`05` is `HeroTypes.Enum`. The serialized value for `effResultOk` is `1`, not
`0`: `HeroEnum` treats zero as “not set” and maps serialized value minus one
to the declaration-order index. Since `effResultOk` is the first declared
value, its wire value is one.

`CMsgF96DCDB0.cs` now exposes this as the opt-in ability mode `complete`. It
strictly parses the captured activation selector and all five typed request
arguments, reuses the request's ability-spec ID and request ID, and sends an
`AreaRequestRPC` with the typed completion above. The Tython trace launcher
enables this mode.

The first implementation accidentally treated the first serialized ID as the
ability specification. The source call and the runtime failure both disprove
that mapping: the first ID is the selected target/player and the second is the
ability specification. Sending the first ID (`0x4000010E218A839B`, the player
character) caused `AttemptQueuedAbility` to pass node 0 into
`InitClientCastingTime`, yielding `requested node ID (0) not found`. For the
captured request, the corrected ability ID is `0xE0009B0DF29A7BA2`; request ID
`12` therefore produces:

```
CF 54 05 8C 0E E7 DC 09 C4
01 CF E0 00 9B 0D F2 9A 7B A2
02 0C
05 01
```

Both the x86 server and the x86 diagnostic hook build successfully. The hook
now logs the selector returned by `0x004C9A10` only when its caller is the
inbound dispatcher return site `RVA 0x001BDA95`. The next controlled runtime
test should press one basic ability once and expect:

1. server decision `ability:queued-result-sent` with the matching ability and
   request ID;
2. client `AreaRpcSelectorHook` selector `54058C0E:E7DC09C4`;
3. either `AttemptQueuedAbility`/a visible cast, or a concrete client dispatch
   error that narrows the remaining defect.

## 2026-09-27 15:15 validation: completion accepted, authoritative effects absent

The corrected ID ordering was validated over nine activation requests. The
server returned request IDs 1 through 9, and the client selector hook reported
`success=1 selector=54058C0E:E7DC09C4` for every completion. There were no
`SendScriptError` packets. This confirms the selector, typed arguments,
`effResultOk` value, and ability/request correlation are all accepted.

The two observed ability specifications resolve from the April GOM buckets as:

- `0xE0009B0DF29A7BA2`: `abl.jedi_knight.introspection`;
- `0xE000A433E5152AA7`: `abl.jedi_knight.force_might`.

Force Might is a particularly useful discriminator because its GOM record is a
friendly buff ability and references eight effect specifications, several of
which are positive effects with 3,600,000 ms duration. The animation and local
global cooldown occur, but no buff icon or persistent state appears.

That behavior matches the HeroScript contract. `OnQueuedAbilityResult` only
calls `AttemptQueuedAbility`, which starts client casting time, client
anticipation/appearance, and the local global cooldown. It does not construct
the authoritative gameplay effect. `AbilityActivate` also records an
unverified activation keyed by effect spec and request ID; a subsequent server
effect event is expected to verify and realize it.

The nearby `CMsg61116AD5` packets are periodic character-sync messages. Their
payload shape is stable while only a time-like suffix changes, and they occur
independently of ability completion. Swallowing them is not the cause of the
missing buff.

The next protocol primitive is therefore a dynamic `AreaEffEventMessage`
(`0xDBF41C90`) correlated to the requested ability/effect and activation
request. The repository currently has only captured startup `.aeff` blobs and
a structural C++ declaration; it has no dynamic effect-event serializer.
`effEventClassMethods`, `effEventOracleClassMethods`, and
`effOracleClassMethods` are the next relevant client-script exports for mapping
the receive-side verification and required fields before constructing a test
event.

## 2026-09-27 JP effect-event contract and first dynamic experiment

The three JP exports close the receive-side contract. `EffEventMessage` copies
the decoded class view into a real `effEvent`, marks it non-synthesized, calls
`effEventConstruct`, and queues it through `effEventOracle_AddEvent`. For a
local caster and positive request ID, that path clears the pending activation;
`effEventOracle_AddEvent` then calls:

```
caster.VerifyAbilityActivation(effEventEffectSpec,
                               effEventActivateRequestId)
```

The effect specification, not the ability specification, is therefore the
authoritative completion key.

The legacy GOM metadata and `msg_area_eff_event_message.h` map the top-level
wire object as follows:

```
target-details vector
effEventCaster                         UInt64
effEventTransactionId                  UInt64
effEventSubEffectNumber                UInt8
effEventTriggerName                    UInt8
effEventResult                         UInt8
optional mask                          UInt8
  0x01 effTimeStamp                    UInt64
  0x02 effEventActivateRequestId       UInt16
  0x04 effEventCalledByTransactionId   UInt64
  0x08 effEventEffectSpec              UInt64
  0x20 effEventExpiration              UInt64
  0x10 effEventTargetPosition           3 x Float32
```

Captured startup event 1 is an 86-byte, one-target event with an AddEffect
action (`0x57`) whose string value is empty, plus top-level mask `0x28`
(effect spec plus expiration). The
first dynamic experiment inserts the two-byte request ID, changes the mask to
`0x2A`, patches caster/target/effect spec and distinct event IDs, and sends an
`effTrigger_OnApply`/`effResultOk` event. It is guarded by
`SWTOR_ABILITY_EFFECT_EXPERIMENT=1`.

The initial mappings are deliberately limited to runtime-observed abilities:

- Introspection `0xE0009B0DF29A7BA2` -> effect
  `0xE0008CAE3E2BB386` (`/1/0`);
- Force Might `0xE000A433E5152AA7` -> effect
  `0xE000A78DCFFE7716` (`/3/4`, positive, 3,600,000 ms).

The Tython trace launcher enables the experiment using the captured AddEffect
action shape.
The next run should press Force Might once. A visible buff proves that the
captured checked-frame value describes the action-free shape independently of
the optional request field. A decode error instead isolates the remaining work
to deriving that frame word; the request/effect semantics are no longer
ambiguous.

## 2026-09-27 15:46 action-free result and action-bearing follow-up

The client accepted repeated 88-byte action-free events without a decode or
script error, but neither ability produced a visible effect. This rules out a
gross top-level layout failure; an action-free event can verify the request but
cannot reproduce the server-authored effect actions.

The April ability data also corrects the Force Might completion key. Its
`ablEffectIDs` slot zero is `0xE000A38DCFFE7CC2` (`/3/0`), while
`0xE000A78DCFFE7716` (`/3/4`) is the downstream one-hour positive buff.
`GetAbilityEffectSpecByNumber(0)` requires the former for request verification.

Captured event 2 is the matching action-bearing template. Byte 8 is action
`0x2C` (AbilityActivate), bytes 9..12 are the UInt32 value length `0x13`, and
bytes 13..31 are the 19-byte decimal character-ID value. The next experiment
therefore sends:

1. a `/3/0` root event with the activation request and
   `effAction_AbilityActivate`;
2. a dependent `/3/4` event with `effAction_AddEffect`, linked through
   `effEventCalledByTransactionId`.

Introspection uses the same root/action form with its already-correct slot-zero
effect, but has no synthetic persistent child event.

## 2026-09-27 16:02 crash and packet-layout correction

The first Force Might action-bearing run crashed in the client's OString reader.
Native stack resolution places the throw in the bounded input-buffer read used
while decoding `effEventActionDetailsValue`; it was a wire-length failure, not
an action-execution or effect-script failure.

The builder had incorrectly treated raw bytes 8..11 (`2C 13 00 00`) as a
CheckedFrame word and then wrote the action enum at byte 12. Byte 12 is actually
the high byte of the UInt32 string length, producing `13 00 00 2C` =
`0x2C000013`. The client consequently requested about 704 MiB from a packet
containing only 19 value bytes and threw `omega::OString`. The corrected builder
writes the action at byte 8, preserves the length at bytes 9..12, and removes
the nonexistent checked-frame environment override.

The dependent buff now uses captured event 1 as its template. That capture is
already `effAction_AddEffect` (`0x57`) and its action-value length is zero. The
root continues to use captured event 2's AbilityActivate action and 19-byte
character value; only the root carries `effEventActivateRequestId`, while the
buff carries `effEventCalledByTransactionId` linking it to the root.

## 2026-09-27 16:14 accepted events do not create persistent state

The corrected packets no longer crash and produce no `SendScriptError`, but
Force Might and Introspection still do not create visible/persistent effects.
The same run identified two additional activation IDs from the request stream:

- `0xE00079A6400301F5` = `abl.jedi_knight.shiicho_form`, root effect
  `0xE000C3452BFEEA1C`, positive child `0xE000C2452BFEE9AF`;
- `0xE00081CEF00BAF68` = `abl.player.sprint`, root effect
  `0xE00015A245BFAC89`; its `/3/1` driver calls `/3/2` and `/3/3`, with
  `/3/3` (`0xE00018A245BFA7A0`) being the persistent 35-percent movement buff.

These casts received `OnQueuedAbilityResult(effResultOk)` but were correctly
logged `effect-not-sent:no-map`; the result RPC only clears/updates activation
state and cannot apply a buff.

More importantly, `effEventConstruct` assigns every incoming event an
expiration of `$NOW + 2 seconds`, and `effEventOracle_AddEvent` places it only
in the transient event oracle. The message verifies an activation request and
drives combat/appearance actions. It does not create an `effEffect` instance or
insert it into `effContainerPositive`.

The captured CRT2 proves the missing authoritative path. Positive effects are
structure-40 replicated nodes parented to positive container
`0x1AC6F6DC0E`; the container's structure-13 `conContents` map owns their slot
membership. Therefore persistent ability support requires one replication
transaction which (1) creates a new structure-40 effect node from the desired
effect prototype and (2) replaces/updates the positive container map to include
that node. `AreaEffEventMessage` remains useful for request verification and
visual notification, but cannot substitute for this state replication.

block, not two strings. In `mirror` mode `ExtractNameBlob` reads the first
four bytes of the request as a length — `0x00000029` = 41 — and copies 41
bytes from a 45-byte body, so the "name" is the packed RPC id plus the
trailing counter rather than a readable name.

`SWTOR_RPC_REPLY_MODE=swallow` is the active setting, so the only two modes
that emit a real server opcode (`SMsgResults`) have never run against
`sub=29`. Every observed ability attempt was swallowed or echoed with the
wrong type.

### 2026-09-27: authoritative positive-effect replication experiment

Accepted `effEvent` messages are not persistent state: `effEventConstruct`
assigns a two-second expiration and the event oracle stores only the transient
event. CRT2 supplies the missing authoritative shape. Its smaller structure-40
`effEffect` record transmits only three fields: `effSlotType` (field 0),
`effTargetDefaultId` (field 1), and `effCasterId` (field 8). The field-state
tail `5A-AA-40` decodes to exactly those indexes.

`AreaAbilityEffectReplication` now reproduces that create shape and, in the
same transaction, replaces `effContainerPositive.conContents` with the
captured slot 1 plus experimental slot 2. Recasts replace slot 2 and remove the
previous experimental node. It is gated by
`SWTOR_ABILITY_EFFECT_REPLICATION=1`; the Tython trace launcher enables it for
Force Might `/3/4`, Shii-Cho `/3/1`, and Sprint `/3/3`. The first generated
payload was checked offline: 100 bytes total, a reconciled 28-byte container
update and byte-for-byte capture-shaped 62-byte effect create. Client behavior
still requires a live run to validate.

### 2026-09-27 16:30: effect nodes accepted; actions remain authoritative

The first live replication run accepted ten consecutive create/replace/remove
transactions without a client exception or `SendScriptError`. Force Might,
Sprint, and Shii-Cho each appeared in the buff tray. This proves the structure
40 create, structure 13 map replacement, generated node IDs, and removal-list
framing are client-compatible.

The result also establishes the next boundary. `PostContainerAdd` in
`effContainerComponentClassMethods` only caches the effect by spec, ability
spec, and tags. It does not execute the effect definition's action list. Sprint
therefore displays its `/3/3` buff but does not execute
`effAction_ModifyMovementSpeed(135)`. Force Might's `ModifyStat` actions and
Shii-Cho's stat/meta-stat actions are likewise server-authoritative outcomes
that must be calculated and replicated independently.

Both Sprint and Shii-Cho have a nonzero `ablModalGroup`. Their quickbar toggle
state is driven by structure-26 field 175, `ablUserModalActiveSpecs`:
`ablUserComponent.Replication_Update` diffs that list and emits
`OnAbilityToggledModalOn/Off`, which updates the quickbar slots. Buff-container
membership alone cannot drive that UI.

The next packet revision consequently:

- retains separate positive-container slots for Force Might (2), Sprint (3),
  and Shii-Cho (4), instead of replacing one shared experimental slot;
- replicates the complete modal-active ability list in the same transaction;
- continues to replace and remove only an older instance of the same ability.

Offline checks reconcile the first modal transaction at 179 bytes and a
two-modal replacement transaction at 202 bytes, with three object records and
the expected one-node removal tail. Actual movement/stat modification remains
deliberately unimplemented until its authoritative replicated output is
identified; displaying an effect and applying its gameplay actions are now
known to be separate operations.

### 2026-09-27 16:50: timed effect-instance fields

The multi-icon run showed no countdown on Force Might even though its ability
definition has a 3,600,000 ms duration. This is expected from the first
replication shape: the tray is displaying the correct persistent `/3/4`
effect, but that instance carried no `effStartTime` or `effEndTime`.

The timed structure-40 Safe Login record establishes the encoding. It adds
fields 3 and 4, uses an inner value size of 33, outer size 38, and field-state
tail `59-6A-40`. Its packed end and start values differ by exactly 59,000.
Interpreting them as FILETIME milliseconds gives
`2012-04-13T09:57:13.219Z`; the contemporaneous `AreaUpdateTimeSource` second
value is Unix milliseconds for `2012-04-13T09:57:12.943Z`. Their epoch offset
is exactly 11,644,473,600,000 ms, with the remaining 276 ms accounted for by
packet order.

Force Might instances now transmit a real start time and end time one hour
later in that captured shape. Indefinite Sprint and Shii-Cho instances retain
the smaller untimed shape. `AreaUpdateTimeSource` now supplies current Unix
milliseconds instead of the stale 2012 fixture so the client time source and
new FILETIME-based effect timestamps share the same instant. Offline encoding
produced the expected `26-28-21` framing, fields 0/1/3/4/8, `59-6A-40` tail,
and an exact 3,600,000 ms timestamp difference. Live countdown behavior still
needs client validation.

### 2026-09-27 16:56: duration accepted; modal quickbar state unresolved

The client displayed Force Might's one-hour countdown exactly as encoded,
confirming that the live effect is the `/3/4` instance and that the current
Unix/FILETIME clock pairing is accepted.

Sprint and Shii-Cho continued to display their buff icons, but their quickbar
buttons did not visually enter the active modal state. The server emitted one
structure-26 field-175 replacement after Sprint and a two-ID replacement after
Shii-Cho. Both contain the activation-request ability IDs, use the measured
54-byte state stream with field 175 selected, and caused neither a client
exception nor `SendScriptError`. The remaining distinction is therefore
whether `ablUserModalActiveSpecs` actually changes in client memory or changes
without causing the expected GUI refresh.

The x86 hook now includes a read-only, ID-filtered
`ablUserModalActiveSpecs` observation in `HeroClass::getField`, and the trace
launcher enables it. A run with one Sprint and one Shii-Cho activation will
show whether the list was applied and whether the quickbar subsequently reads
it; no client value is modified by this probe.

The 17:09 run produced no `HeroClass::getField` observation for this field,
despite confirming that the hook was installed. The compiled HeroScript path
therefore accesses the modal list by resolved field offset and bypasses the
generic getter. The launcher disables this inconclusive probe again. The next
discriminator is the client's own second-press behavior: an applied modal list
causes `AbilityDeactivate` and `OnRequestAbilityDeactivate`; an unapplied list
causes a second `OnRequestAbilityActivate`. The existing outbound RPC trace
records that distinction without any new client mutation.

The 17:15 run sent eight presses and all eight used activation selector
`1279C371:001703D5`; none used `OnRequestAbilityDeactivate`. This proves the
modal list itself was not applied, rather than being applied without a GUI
refresh.

The fault is in the list value. `ablUserModalActiveSpecs` is a Hero List. In
style 8, `DeserializeList` interprets an odd count marker as having explicit
per-element indexes and reads one packed index before each value. The
experiment sent `(count * 2) | 1` but omitted those indexes, so the client
consumed the beginning of the ability ID as an index and never stored that ID.

CRT4 provides a measured structure-26 List value: its two-entry
`cbtActiveAttitudesList` begins `05 03 ... 05 ...` — odd doubled count, then
explicit one-based odd index tokens 3 and 5 before the two values. The modal
update now reproduces that captured form: one ID is `03 03 <ID>` and two IDs
are `05 03 <ID> 05 <ID>`. The positive-container map retains its separate
map-entry encoding.

### 2026-09-27 17:23: modal state accepted; deactivation request identified

With the indexed List encoding, the client visibly marked both Sprint and
Shii-Cho active. More importantly, each second press stopped using
`RequestAbilityActivate` and emitted a different RPC:

```text
C7 71 C3 79 12 F2 96 17 9D 01 <packed ability ID>
```

The selector is `1279C371:9D1796F2`, matching
`OnRequestAbilityDeactivate`. The remaining payload is exactly one style-5
typed argument: `HeroTypes.Id` followed by the ability spec ID. Sprint sent
`E00081CEF00BAF68`; Shii-Cho sent `E00079A6400301F5`. There is no request ID,
so this path does not have the activation request's queued-result completion.

The server now parses that form strictly and, for a known active replicated
ability, sends one authoritative replication transaction which replaces the
positive-effect container with the retained nodes, replaces
`ablUserModalActiveSpecs` with the remaining modal abilities, and removes the
deactivated effect node. An empty modal list is encoded in the same indexed
replacement form with count marker `01`. This builds successfully as x86;
live removal and zero-entry replacement behavior are the next test.

### 2026-09-27 17:32: deactivation transactions accepted without errors

The directed sequence Sprint on, Shii-Cho on, Sprint off, Shii-Cho off reached
all four intended server states:

- stream `001B502E` created Sprint node `1`, modal count 1;
- stream `001B502F` created Shii-Cho node `2`, modal count 2;
- stream `001B5030` removed Sprint node `1`, retained Shii-Cho and modal count 1;
- stream `001B5031` removed Shii-Cho node `2`, retained no experimental nodes
  and sent modal count 0.

The two removal payloads were 133 and 116 bytes respectively. The client
continued running afterward and produced neither `SendScriptError` nor a C++
exception after either removal, so both the retained-one and zero-entry
transaction shapes are at least parser-safe. One handled first-chance
`ConversionException` occurred during world entry, well before the ability
test. Logs cannot establish whether the quickbar highlights and buff icons
visually disappeared; that observation remains a user-visible check rather
than a wire-level one.

The visual result was negative: neither the buff-tray entries nor quickbar
highlights disappeared. This corrects the interpretation above. Parser-safe
does not mean semantically applied, and the removal-list tail only destroyed
the effect object; it did not remove references held by collection fields.

The cause is the low bit on style-8 sequence counts. The activation packets use
the captured odd form, which is a sparse merge. Sending a shorter odd sequence
therefore leaves omitted map/list entries intact. The reference serializers in
`Tools/tor_tools/Hero` emit an even `count * 2` marker for full values; Lists
then write explicit zero-based indexes. Deactivation now sends full even-form
replacements for both `effContainerPositive.conContents` and
`ablUserModalActiveSpecs`, followed by the effect-node removal. For the final
modal removal these values become an even zero-entry list (`00`) and the
container's retained slot-1 map. This revision builds successfully and awaits
the same four-step live test.

### 2026-09-27: full-value deactivation validated

The repeated Sprint on, Shii-Cho on, Sprint off, Shii-Cho off test passed
visually. Removing Sprint removed its buff-tray icon and cleared its quickbar
toggle while leaving Shii-Cho active; removing Shii-Cho then removed its icon
and cleared its toggle as well. This validates both the retained-one container
replacement and the final zero-entry modal-list replacement.

The modal ability lifecycle is therefore closed at the client-state level:
queued activation completion, persistent effect creation, multiple concurrent
icons, modal-on UI, selective effect removal, and modal-off UI all work. The
remaining Sprint, Shii-Cho, and Force Might work is gameplay-authoritative
modifier replication; their visible effect instances do not themselves execute
movement-speed or stat actions on this client.

### 2026-09-27: Sprint action data and shared meta-stat replication

The April asset graph was loaded directly from
`Assets2012April/swtor_main_systemgenerated_gom_1.tor`. Sprint's persistent
effect `abl.player.sprint/3/3` contains the following executable rule:

- subeffect 0: `effCondition_IsNotInCombat`, actor 3;
- subeffect 1: `effAction_ModifyMovementSpeed`,
  `effParam_AmountPercent = 135`;
- subeffect 2: `effAction_RemoveEffect` on its removal trigger.

The root description is therefore not being used as an implementation hint;
the action name, parameter, and condition all come from the real effect graph.

Structure-26 field 100, `modMetaStatComputed_Shared`, was then decoded from
both captured CRT16 and CRT17. Its exact value schema is
`Map<Integer, Map<modStatEnum, Float>>`. Both bodies reconcile completely:
588/588 bytes for CRT16 and 600/600 bytes for CRT17. The outer keys resolve to
actual ability/effect specs (Slash, proficiency effects, revive effects, and
their children), proving this is a per-spec computed-stat cache rather than an
active-character modifier collection.

The HeroScript accessor confirms the same contract independently:
`effEffect.GetEffectStat*` obtains `Me.GetSpec()` and calls
`character.GetMetaStat(effectSpec, statEnum)`. Thus the cache key required by
Sprint is specifically the persistent `/3/3` effect spec, not the root ability
or the runtime effect-node ID.

The authoritative April `modStatEnum` definition also corrects an important
stale-tool assumption: `STAT_aiMoveSpeedModifier` is enum ordinal `0x24`.
`Tools/tor_tools/GomLib/Models/Stat.cs` labels ordinal 25 as movement speed,
but that helper omits several earlier unused enum members and cannot be used as
the replication ordinal table.

Sprint activation now sparse-merges this entry before the effect object in the
same replication transaction:

```text
abl.player.sprint/3/3 -> { 0x24: 135.0 }
```

The update uses structure 26, field 100, style 8, and odd doubled map counts at
both nesting levels. The generated record has a 16-byte value body, 54-byte
field-state stream, outer size `0x48`, and state byte 25 equal to `0x40`.
Offline generation produced four correctly framed object records for Sprint
(stat cache, effect container, effect create, modal list), and the x86 server
build succeeds. The cache entry deliberately remains after deactivation: the
positive-effect container determines whether the action is active, while the
shared map supplies the effect spec's computed parameter whenever needed.

Live validation should compare movement with Sprint off and on while out of
combat, then confirm that a second press restores the original speed. Combat
suppression remains a separate condition-state test after the basic modifier
path is confirmed.

### 2026-09-27: Sprint shared-stat cache accepted, but not executed

The live run activated and deactivated Sprint twice. Both activation
transactions logged `metaSpecs=1`, both modal transitions completed, and the
client produced neither `SendScriptError` nor a C++ exception. The player did
not move faster. Therefore field 100 is valid, parser-safe input, but adding an
effect instance to `effContainerPositive` does not locally execute
`effAction_ModifyMovementSpeed` on this client.

This narrows the missing server output to the action's active stat mutation.
The replicated player schema has three plausible layers:

- field 52 `modStatComputed` (`Map<modStatEnum, Float>`);
- field 136 `modStat_Fixed`
  (`Map<modStatEnum, Map<ID, Float>>`);
- field 137 `modStat_PercentOfCurrent`
  (`Map<modStatEnum, Map<ID, Float>>`).

The next implementation must follow the April `modStatComponentClassMethods`
calculation/removal contract rather than guessing which layer owns the 135%
source entry. `modMetaStatComponentClassMethods` will also establish whether a
field-100 merge invalidates or immediately recomputes any client-side cache.

### 2026-09-28: client stat contract and Sprint computed output

The added `modStatComponentClassMethods` resolves the replication behavior:

- a field-136/137 change only calls `OnModifiersChanged`;
- a field-52 `modStatComputed` change independently calls
  `OnComputedStatChanged`;
- the client does not recalculate field 52 from either modifier collection;
- `GetAccumulatedModifiers` treats field 137 as a fraction of the clamped
  `(base + fixed)` value.

Consequently the server must replicate both the active modifier source and its
already-calculated output. Field 100 is still required because
`modMetaStatComponent.GetMetaStat(effectSpec, stat)` reads the effect action's
135 parameter there, but it is input metadata rather than live character
state.

A targeted scan of the captured CRT2 player record found exact, internally
consistent stat maps:

- `modStatComputed`: 37 entries at body offset `0x18B`;
- `modStatBase`: 25 entries at body offset `0x248`;
- `modStat_Fixed`: 16 stat keys / 19 sources at body offset `0x35E`.

The relevant unmodified computed values are:

```text
STAT_aiRunSpeed      (0x27) = 0.60
STAT_aiWalkSpeed     (0x28) = 0.15
STAT_aiRunBackSpeed  (0x3A) = 0.36
```

Sprint's 135% therefore produces `0.81`, `0.2025`, and `0.486`, with a `0.35`
field-137 source contribution for each stat. The modifier source is the runtime
effect node, matching CRT2's captured fixed modifier sourced by its runtime
Safe Login effect node rather than by the effect prototype.

Activation now sends a structure-26 update containing fields 52 and 137 before
the effect/container records. Deactivation restores the three captured values
in field 52 and sparse-merges even empty nested maps for those field-137 stat
keys, removing the Sprint source without replacing unrelated stat keys. The
generated activation payload contains five framed records and is 380 bytes;
the generated deactivation payload contains three records plus node removal
and is 200 bytes. Both were inspected offline and the x86 server builds.

### 2026-09-28: Sprint computed-stat mutation validated live

The live out-of-combat comparison passed. Activating Sprint visibly increased
character movement speed, and toggling Sprint off restored normal movement
speed. The pre-existing buff-tray icon and modal quickbar state also continued
to activate and deactivate correctly.

This validates the complete persistent stat-effect path for Sprint: effect
metadata, runtime effect-node source, percent-of-current modifier replication,
server-computed stat replication, and inverse removal. The next implementation
step should replace Sprint's hard-coded restored values with source-aware stat
aggregation before adding overlapping stat effects. Shii-Cho is the preferred
second ability because it reuses the proven indefinite/modal lifecycle while
exercising a different set of gameplay stats. Force Might should follow once
timed expiry and overlapping modifier recomputation are authoritative.

### 2026-09-28: source-aware stat aggregation and Shii-Cho

The effect state now retains each runtime node's base values, fixed modifiers,
and percent-of-current modifiers. Activation recomputes affected output from
all retained sources. Removal recomputes after excluding the removed source and
replaces only the affected nested source maps, retaining any other active
sources on the same stat. This removes Sprint's hard-coded inverse as the
authority for deactivation and makes activation/removal order safe for future
overlapping buffs.

The April asset graph for `abl.jedi_knight.shiicho_form/3/1` establishes the
unconditional base-rank actions. It adds `0.03` fixed to elemental, internal,
kinetic, and energy damage reduction (stats `0x15` through `0x18`) and to
damage-done percentage (`0x4F`). Conditional talent-rank branches increase the
four reduction values, but those talent abilities are not present in the
current character fixture and are intentionally deferred.

Shii-Cho activation now transmits the five fixed runtime-node sources in
structure-26 field 136 together with their five server-computed field-52
values. Deactivation restores the zero baselines and sends full empty nested
maps for those five fixed-source collections. Offline generation produced a
valid four-record activation transaction and a 214-byte three-record removal
transaction. The x86 server builds successfully; live validation is pending.

Live validation confirmed that the character UI's damage-reduction value rises
while Shii-Cho is active and returns on removal. This proves field-136 fixed
sources and their source-aware inverse, independently of Sprint's field-137
percentage path.

### 2026-09-28: Force Might stats and right-click removal

Force Might's persistent `/3/4` effect applies `+5% of current` to six stats:
ranged (`0x19`), melee (`0x1A`), Force (`0x81`), and Tech (`0x82`) bonus
damage, plus Tech (`0xDA`) and Force (`0xDB`) healing power. These now use the
same source-aware percentage pipeline as Sprint and retain the real one-hour
effect duration.

The client implements buff cancellation through
`effOracle.RequestEffectRemove(ownerId, effectNodeId)`, which calls the server's
`OnRequestEffectRemove`. The server now recognizes any two-ID request in the
untrusted-method stream only when both IDs match a live effect node created for
that client. It then invokes the same authoritative stat, container, modal, and
node removal path used by toggle abilities. Matching live IDs instead of a
hard-coded function SID keeps this compatible with the April script build and
prevents unrelated two-ID RPCs from being consumed. Live validation is
pending.

Live validation passed for all three persistent effects. Right-clicking Force
Might, Sprint, or Shii-Cho removed the selected buff icon, reverted its
authoritative stat changes, and cleared modal quickbar state where applicable.
This confirms `OnRequestEffectRemove` routing is generic by runtime effect node
and that fixed and percentage modifier cleanup both work through the shared
manual-cancellation path.

### 2026-09-28: conditional Sprint suppression on combat state

The client contract identifies `staFighting` as structure-26 field 6;
`staCharacter_IsInCombat()` returns this value directly and its replication
update invokes the client's combat-state rectification path. A new stat-only
transaction updates this field together with computed and modifier maps,
without touching the persistent effect container or modal-active ability list.

Sprint's runtime effect state can now be suppressed independently of its buff
instance. On combat entry its three percentage sources are replaced with empty
nested maps and run/walk/back speed return to baseline, while the Sprint icon
and active quickbar state remain. On combat exit the same runtime effect-node
sources and computed speeds are restored.

This emulator does not yet have authoritative NPC threat/death ownership. For
live validation, an opt-in bridge treats an ability request whose target is not
the player as combat entry, resets a ten-second inactivity timer on subsequent
hostile activations, and emits combat exit when that timer elapses. The bridge
is isolated from Sprint's condition logic so a future combat manager can call
the same state transition without retaining the inactivity heuristic. Offline
generation produced a 103-byte one-record combat-entry refresh with field-state
bytes for `staFighting`, `modStatComputed`, and
`modStat_PercentOfCurrent`. The x86 build succeeds; live validation is pending.

