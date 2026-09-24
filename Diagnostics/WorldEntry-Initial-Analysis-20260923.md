# World-entry initial analysis — 2026-09-23

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
