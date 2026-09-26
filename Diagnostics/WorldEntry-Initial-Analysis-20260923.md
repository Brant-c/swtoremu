# World-entry initial analysis — 2026-09-23

## 2026-09-24 completed-run boundary

The targeted travel-manager trace removes the area-travel machinery itself from
the remaining suspect set.  After `On Enter` was parsed and its callback ran,
and after `CharacterChangeState("AreaServer")` returned success (`1`), two
independent snapshots showed:

- both area-manager slots (`+0x24` and `+0x28`) null;
- both slot states zero;
- selection/travel mode zero;
- the destination queue empty; and
- the destination string cleared.

The resource worker was also idle (`state=5`, `queued=0`).  The client continued
normal ping/module/world-report traffic and exited cleanly when closed.  This is
not an area-load deadlock, a queued resource wait, or an unconsumed destination.
The remaining gate is downstream of successful travel and character-state
dispatch: gameplay readiness, local-character semantics, or loading-UI/script
state.

One previously under-recorded signal remains: the client sends a 48-byte
`CMSG 0x8EB28DE9` world report every ten seconds after activation.  The original
reference server treats it as a no-op, so no response was added.  The emulator
now passively logs its full bytes and 32-bit words to determine whether it is a
constant heartbeat or contains a readiness transition.  This instrumentation
does not alter protocol behavior.

### Correction: the correlated `0x00923C20` hook is not a Hero VM method

Static disassembly resolves `0x00923C20` as a replicated-field string copier
with one source argument.  Its return address `0x0093173B` is the instruction
after a call that writes an unnamed map-note object's `mpnTaxiConnectionsList`
field at object offset `+0x12C`.  Values previously printed as eight formal VM
arguments are merely adjacent caller-stack context.  They must not be used as
evidence that a `chrPlayerCharacter` Hero method is active or returning zero.

The genuine class-1 bridge correlation also lands in a small reference/copy
routine (`0x009B2A20`), not a named Hero procedure.  Hero-script activation
therefore remains possible, but the current native hooks do not prove it.  The
next script investigation must anchor on an actual script/event symbol or the
loading-screen `cleanUp` transition, rather than interpreting generic copy
routines as script dispatch.

### Loading-screen state definition

`Diagnostics/Inspect-GomClass.py` now decodes a named class and its direct
field types from the 2012 `client.gom`. For `guiGFxLoadingScreen` it establishes
the following client-local state without relying on a live run:

| Field | Type |
| --- | --- |
| `guiGfxLoadingProgressBarOn` | Boolean |
| `guiGfxLoadingStringTableTimer` | Timer |
| `guiGfxLoadingFadeTimer` | Timer |
| `guiGfxLoadingAssetLoadingTimer` | Timer |
| `guiGfxLoadingAssetTimeoutAt` | Time |
| `guiGfxLoadingAssetLoadingTimerZeroCounter` | Int64 |
| `guiGfxLoadingFadedOut` | Int64 |
| `guiGfxLoadingNewFadeOut` | Boolean |
| `guiGfxLoadingRepositorAssetCount` | Int64 |
| `guiLoadingStageProgress` | Map<String, Float> |
| `guiAssetsLoadedTimer` | Timer |

The associated v5 script's 19-entry symbol table contains `cleanUp`,
`enableLoadingBar`, `updateLoadingBar`, `Loading Repository Assets`, and
`Loading String Table Assets`. No other recovered script contains the loading
screen class name, those stage labels, or `cleanUp`. Together, this narrows the
client-side exit path to one script and two progress phases. It does **not** yet
prove either phase is the blocker: the last run's resource worker reached
`queued=0`, all observed GUI/resource callbacks succeeded, and the native area
manager logged `Active area load complete`.

The compiled portion of this version-5 script is not a regular ELF image. The
repository's original `SCPTExtractor` explicitly documents that it only
decrypts/reconstructs v5 payloads and that their result is not regular v4 SCPT.
Consequently, treating bytes immediately after the string table as an ELF or
as a single length-prefixed blob would be another unsupported interpretation.
The next live diagnostic should observe the 11 runtime fields (or the loading
screen `cleanUp` dispatch) directly; no server packet should be changed merely
because the loading overlay remains visible.

An opt-in, read-only observer now detours the client's central GOM definition
lookup (`0x004A95B0`) and filters before logging to the loading-screen class and
its eleven direct fields. `Run-SWTORClassic-Trace-Tython.cmd` enables it with
`SWTOR_TRACE_LOADING_SCREEN=1`. Each match records the symbolic field name,
returned descriptor words, descriptor memory, and client-relative call stack.
It does not write GOM state or invoke `cleanUp`. The post-run trace analyzer
summarizes these matches separately, allowing the next run to establish which
native code accesses the loading state before any object-layout assumptions are
made.

The first live attempt produced no matching central-GOM lookups even though the
observer installed successfully. Offline decoding then established why: the v5
payload contains big-endian packed (`CF`) GOM references and compiled native
x86 with cached field IDs. `Diagnostics/Inspect-V5ScriptGomRefs.py` resolves
those references and identifies the sole function marker as string-table entry
5, `cleanUp`. Its generated timer accessor compares the requested 64-bit field
ID directly against `guiGfxLoadingFadeTimer`,
`guiGfxLoadingAssetLoadingTimer`, and `guiGfxLoadingStringTableTimer`.

The compatibility launcher now locates that generated accessor by a unique
25-byte code signature after active-area completion and installs an
observation-only breakpoint at its function entry. The signature has exactly
one match in the recovered loading-screen payload, resolves from offset
`0x41FF` to function entry `0x416B`, and is independent of patched call
relocations. Each invocation reports the exact timer field ID and receiver; it
does not change the timer or function result.

## Current boundary

The project is no longer blocked on reaching or transferring the area service.
The client:

- completes character selection;
- attaches to Tython's area service;
- accepts the startup packet bundle and CRT stream through `0x001B502D`;
- reports `Active area load complete`; and
- remains alive in its loading/polling state until it is closed.

That places the remaining fault after transport, service routing, asset loading,
and bulk replication. The most likely missing piece is a semantic transition:
the client has data for the area, but has not accepted the local character as an
active, playable world entity.

## What the repository tools establish

`Parser/SWTORParser` is valuable for packet framing and for locating handlers,
but some area-handler routines are incomplete or stale. In particular, detailed
client replication decoding is currently bypassed by an unconditional early
return. It should not be used as the sole protocol specification.

`Parser/SWTORParser/Hero/PackedStream.cs` is the strongest local reference for
Hero packed-value v5 encoding. Applying it to the captured data separates two
important RPC forms:

- `C7` followed by a little-endian 32-bit call identifier;
- `CF` followed by a packed 64-bit target/object reference.

The repeated client request decodes as call ID `0x1279C371`, with changing
four-byte argument values. It is a structured binary call, not a textual RPC
name.

`Tools/SCPTExtractor` successfully recovers SCPT string tables and embedded ELF
content. The decoded script corpus is therefore useful for vocabulary and
event-name discovery, but the extractor does not currently map a 32-bit RPC ID
to a procedure name. `tor_tools/GomLib` is useful for GOM types and instances;
its SWTOR hash implementation concerns archive/resource paths and is not yet
shown to be the RPC-ID algorithm.

The reproducible inventory is in `Diagnostics/Decode-WorldEntryPayloads.ps1`.

## Important correction to the current RPC hypothesis

Client disassembly confirms that inbound `SMSG_RESULTS (0xD5280283)` reads two
strings and invokes a registered callback with a constructed results object and
those strings. It does **not** expose any packet-layer link between those strings
and the binary call ID from the client's `C7` request.

The current `RpcReply` implementation extracts the entire binary request blob
and sends it as the first `SMSG_RESULTS` string. That can wake script behavior,
as observed, but calling that blob an RPC name or correlation key is not
supported by the decoded wire format. The synthetic `("blob", "true")` reply
should therefore be treated as an experiment, not the finished protocol.

## Remaining work, in priority order

1. **Resolve the semantic meaning of client call `0x1279C371`.** Extend the
   existing SCPT/ELF tooling or inspect the client call-construction path to find
   the procedure registration/table that maps the ID to a name or handler.
2. **Identify the `SMSG_RESULTS` callback contract.** Trace registration of the
   callback interface used by the handler at client address `0x00652120`; find
   what the two strings represent and whether this message is related to the
   repeated binary RPC at all.
3. **Compare against a successful world-entry capture.** A same-build retail or
   known-good exchange from area attach through loading-screen dismissal would
   settle packet order, RPC replies, character-state strings, and final
   replication deltas much faster than further blind variants.
4. **Audit player-object semantics in the CRTs.** Verify that the selected
   character node is created, designated local/controlled, placed in the correct
   instance, and referenced consistently by awareness, teleport, rendezvous,
   and character-state packets. Do not rewrite the frequently occurring
   `...839C` value merely because the selected character ends in `...839B`; its
   repeated positions look like a shared prototype/class reference.
5. **Only then change production packets.** Prefer decoded fields and explicit
   state over additional captured opaque blobs. Keep the current bundle as a
   regression fixture while replacing one understood component at a time.

## Recommended next implementation slice

Build a small command-line extension around the existing SCPT extraction logic
that emits, per script, its name, string table, ELF symbol/relocation inventory,
and every occurrence of the little-endian bytes `71 C3 79 12`. In parallel,
instrument the client hook at the outbound RPC constructor so it logs the
resolved procedure/object metadata before serialization. This is narrower and
more informative than trying more `SMSG_RESULTS` string combinations.

## Follow-up implementation and result

`Diagnostics/Scan-ScriptRpcIds.ps1` now implements the static scan directly on
the original v5 SCPT containers. It applies SCPTExtractor's decrypt rule,
validates payload lengths, searches both byte orders, and prints nearby ASCII
strings for any hit. A portable Python equivalent is also present as
`Diagnostics/Scan-ScriptRpcIds.py`.

The scanner checked all 846 recovered scripts for the observed call IDs
`0x1279C371`, `0x654BE507`, `0xAF1AA175`, `0xBD41774F`, and `0xBEE0190C`.
There were no exact 32-bit references in either byte order. This makes a static
literal table in the SCPT payloads unlikely; the IDs are probably calculated or
assigned during runtime registration.

An opt-in diagnostic hook was consequently added at the client's outbound
`CMsgF96DCDB0` wrapper (`0x00A7FEB0`, RVA `0x0067FEB0`). Enable it with
`SWTOR_TRACE_RPC_CALLS=1`. Before attaching it validates the expected function
prologue. For every call it logs the sender and blob addresses, return address,
payload length, marker, decoded `C7` call ID, and up to 64 payload bytes. It
passes the original object and blob through unchanged.

The Release/Win32 hook builds successfully and the isolated x86 Detours
attach/trampoline/detach smoke test passes. The next live run should use the
opt-in switch and compare the logged caller address across the 30-second poll
and initial world-entry request. That caller is the next static path to trace
back toward the runtime procedure registration.

### Completed-run refinement

The 2026-09-23 live run showed that every outbound payload passed through the
same generic sender address and began with `C7 71 C3 79 12`, while the following
four bytes varied by request. The repeated loading request was:

`C7 71 C3 79 12 F2 40 F5 F5`

It repeated at 30-second intervals despite a mirrored `SMSG_RESULTS` reply.
This makes `0x1279C371` more likely to be a shared target/object identifier and
`0xF5F540F2` the operation identifier. The other observed candidate operations
(`0xEF39EF2C`, `0xCE20ED6B`, `0xB6FDF089`, `0xA08E665B`, and `0x17D527CC`)
also have no literal occurrence in the 846 SCPT payloads.

The hook now records the client image base and a 12-frame stack with image RVAs,
and labels the two fields as `target` and `operation`. This avoids treating an
ASLR-dependent absolute return address as a static client address. The updated
hook builds successfully and passes the isolated x86 Detours smoke test. The
existing trace launcher will install this build automatically on its next run.

### 2026-09-24 two-cycle loading-script result

The latest two-cycle Tython run again completed the area resource path, the
OnEnter batch, and the character-state transition. The resource worker reached
state 5 with an empty queue, while operation `0xF5F540F2` continued at its
30-second cadence.

The read-only loading-screen observers produced two important negative results:
there were no `guiGFxLoadingScreen` definition lookups, and the unique native
timer-accessor signature recovered from April script
`4C15D3BA7555CC29.scpt` was not resident when active-area loading completed.
An offline inventory also confirms that this is the only one of the 846
recovered scripts containing both `guiGFxLoadingScreen` and `cleanUp`.

This does not establish that a timer is stuck. It establishes that the expected
April loading-screen implementation was not observable in the live process in
its recovered form. The next investigation should therefore verify script
registration and activation/resource mapping before changing another server
reply or loading timer.

The `SDEF` packed-stream format has now been decoded. The April list contains
1,734 records representing 867 unique script definitions, each with variants 0
and 1. All 867 definition IDs resolve to SCPT containers in the recovered April
cache. In particular, `4C15D3BA7555CC29.scpt` is registered as
`0xD000468824F9B4C8`, key `0xEFDF56CB`, in records 416 and 417. The same script
ID is directly referenced by the `guiGFxLoadingScreen` class record in
`client.gom`, so neither registration nor class-to-script association is
missing.

The stripped client directory contains GFX archives but not
`swtor_main_systemgenerated_gom_1.tor`. That matching April archive contains
the SCPT bodies. The compatibility bridge supplies the definition list but does
not supply anonymous/hash-addressed script bodies, explaining how registration
can succeed while the generated loading code is absent. The trace launcher now
installs this exact April archive before startup; the next live run tests native
script-body resolution without changing server packets.

The three-cycle run with that archive installed did not activate
`guiGFxLoadingScreen`: its definition lookup count and recovered accessor count
both remained zero, while `0xF5F540F2` repeated three times. This rejects the
archive's absence as the direct world-entry blocker.

The correlated string-copy stack contains `0xD000199A7D03034B`, which resolves
by SCPT checksum to `C9CA0FEDFE12C16C.scpt`; `client.gom` associates that script
with `chrPlayerCharacter`. Static disassembly subsequently showed that these
values are caller-stack context around a generic string-copy adapter, not a
proven method identity. Similarly, its reachable `not_found` string is not yet
proven to be the poll result. They remain correlation evidence only.

### 2026-09-24 correction: external frames were the diagnostic DLL

The executable addresses outside the client image were resolved against the
built `MemoryMan.dll`. They are the diagnostic hook's own frames, not generated
Hero code. The stable client path is instead a chain of generic native
adapters: event dispatch at RVA `0x001D12A0`, the class-1 bridge returning at
RVA `0x007D4929`, and the area-RPC sender adapter returning at RVA
`0x00242A49`. The original C++ server also deliberately consumes
`CMsgF96DCDB0` without replying, and the repository's echo/result experiments
did not advance world entry. The repeated operation remains a readiness-loop
symptom, not a proven missing response.

The next observer records the direct caller of the central event dispatcher
before those adapters run, together with a deeper stack. That caller is the
first evidence capable of distinguishing the timer/subsystem producing
`0xF5F540F2`; no server reply or loading-screen state should be changed until
it is identified.

The first run with that observer found the direct caller at a private runtime
address (`0xEC4B1CC3` in that process). Unlike the earlier external frames,
this address is outside `MemoryMan.dll`, and the captured bytes are a small
generated thunk whose relative call resolves exactly to the native event
dispatcher. The deeper stack below it passes through the client VM/script
scheduler (including RVAs `0x001BE181`, `0x001C173B`, `0x001BF096`, and
`0x001BEEA7`) and ultimately the main update loop. This establishes that a
runtime-generated script callback produces the readiness operation. It does
not yet identify which script or method registered that thunk.

An attempted in-process dump around that generated caller caused repeatable
access violations during character-selection setup (near-null instruction
addresses `0x2F`, `0x34`, `0x2E`, and `0x33`). Removing the producer-dump block
restored the last known working hook and the client again reached the Tython
readiness loop. Do not reintroduce memory walking on this hot generated-event
path.

The clean follow-up proves that `0xF5F540F2` is emitted synchronously while the
VM is inside the invocation correlated with dispatch key
`0xD000199A7D03034B`; the active native caller is RVA `0x001C173B`. The GOM
resolver maps that key to the `chrPlayerCharacter` **class record**, not a Hero
method. Recovered
SCPT scanning finds no literal F5 operation or `0x1279C371` target in the
scripts, so those values are constructed by the native event/RPC layer. An old
full dump places F5 beside the other events in the same generated batch; later
F5 instances repeat alone every 30 seconds. This supports treating it as a
periodic script-side status notification, not a request requiring a direct
server reply.

`Capture-ReadinessDump.ps1` now watches the existing hook log and takes one
external full-memory snapshot at the second F5 event. The first F5 belongs to
the initial world-entry batch and has no active VM invocation; the second is
the periodic call 30 seconds later where the trace shows the correlated
definition active at RVA `0x001C173B`. The Tython trace launcher starts this
watcher after rotating the log. This avoids changing the client hook while
preserving the relevant runtime script object and generated callback for
offline analysis.

### 2026-09-24 correction: startup RPC ordering drift

Comparison with the untouched `swtoremu2` `ObjectReply` sequence found one
unintentional ordering change introduced when startup moved into
`AreaStartupBundle`: the `CF 65 F1 36 ...` area RPC had moved from immediately
after CRT1 + the first `CF 75 ...` RPC to after CRT2, effect event 1, and the
system RPC. This contradicted the September 18 note promising the same packet
order. The call is restored to its original position. The normalized sequence
now matches the untouched source (apart from the intentionally removed duplicate
`AreaSetCharacter`), and `Test-WorldEntryOffline.ps1` guards the prefix order.
