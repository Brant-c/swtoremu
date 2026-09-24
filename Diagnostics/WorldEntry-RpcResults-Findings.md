# 2026-09-20 (second session) — SMSG_RESULTS implemented (the missing RPC reply)

## The decisive discovery

`SMSG_RESULTS (0xD5280283)` has a **client inbound handler** that we have never
used. Found by byte-scanning the client `.text` for `83 02 28 D5`
(`cmp eax,0D5280283h`) and disassembling the true address with capstone
(`Diagnostics/Find-Bytes.py` + `Disasm-Range.py`):

```
RVA 0x25214E: cmp eax, 0xd5280283
RVA 0x252153: je  0x2521A4           ; handler
RVA 0x2521A4: [ebp-0x28] = string object (vtable 0x0111DCD4)
RVA 0x2521B3: [ebp-0x20] = string object
RVA 0x2521C1: call 0x97D270           ; READ STRING 1
RVA 0x2521CF: call 0x97D270           ; READ STRING 2
RVA 0x2521DC: call 0x97D020           ; end-of-message check
RVA 0x25220B: call 0xa82400           ; build a results object
RVA 0x252217: dispatch(results, string1, string2)
```

So `SMSG_RESULTS = (string, string)` — the reply to an RPC.

And the client's `CMsgF96DCDB0` / `CMsg4A765897` bodies are `[Int32 len][len
bytes]` (the reference server's `HandleUnkF96DCDB0` in
`Server/WorldServer/Src/Logic/Handlers/General.cpp:352` reads exactly
`count` + `count` bytes and discards them). The client re-fires the same request
every ~30 s forever; we used to swallow/echo/ack it. **An RPC request that never
produces a result is the only explanation left that is consistent with every
observed log**: stable poll loop, no crash, no state change, loading screen
never drops.

## What was added

1. `PacketTypes.SMsgResults = 0xD5280283`.
2. `NET/Packets/Server/SMsgResults.cs` — two payload forms:
   - text: `WriteString(name) + WriteString(value)` (`Int32(len+1)+bytes+0x00`)
   - raw: `Int32(len)+bytes` per field (the encoding the client itself uses for
     the RPC name inside its request body) — this is what `mirror` mode uses.
   Explicit service routing: area `0x65B3 -> AreaServiceID` or game systems
   `0x65AC -> GameSystemsServiceID`.
3. `NET/Packets/Server/RpcReply.cs` — env-controlled dispatcher:
   - `SWTOR_RPC_REPLY_MODE` = **mirror (default)** | results | echo | swallow | ack
     - *mirror*: string 1 = the client's own request name blob (so the client can
       match its pending call), string 2 = `SWTOR_RPC_RESULT_B`.
     - *results*: string 1 = `SWTOR_RPC_RESULT_A`, string 2 = `SWTOR_RPC_RESULT_B`.
   - `SWTOR_RPC_RESULT_A` (default "true"), `SWTOR_RPC_RESULT_B` (default "true").
4. `CMsgF96DCDB0` and `CMsg4A765897` now answer with SMSG_RESULTS in
   mirror/results mode; echo/ack/swallow remain available for regression.
5. `CMsgC586BD22` re-send gate `SWTOR_RE_SEND_INIT=1` (in-world init + attach
   signals on re-attach) — the previous run proved this switch was never
   actually exported by the cmd; that is fixed.
6. `Run-SWTORClassic-Trace-Tython.cmd` now sets and echoes:
   `SWTOR_RE_SEND_INIT=1`, `SWTOR_RPC_REPLY_MODE=mirror`,
   `SWTOR_RPC_RESULT_A=true`, `SWTOR_RPC_RESULT_B=true`.
7. `Diagnostics/Test-SMsgResults.ps1` — wire verifier. Verified bytes for
   ("true","true") on area routing:
   `83 02 28 D5 | 08 00 B3 65 | 05 00 00 00 74 72 75 65 00 | 05 00 00 00 74 72 75 65 00`
   (26 bytes) plus the game-systems routing and empty-string variants.

Regressions re-run and passing against the fresh build:
`Test-AreaEnterSignals.ps1` (3 PASS), `Test-AreaWireRoundTrip.ps1` (54 fixture
packets), CRT3 sha unchanged.

## State of the previous run (16:06-16:10) — what it proved

- The re-attach path ran with `SWTOR_RE_SEND_INIT` unset (my cmd edit had only
  replaced an echo line), so no re-send happened.
- The **AreaStartupBundle still sent the complete state**: CRT1–CRT17
  *including CRT3 = stream 0x001B5014, 63 bytes*, AreaAwarenessEntered (13496
  and 1255 bytes), AreaHackPack, AreaSendAwarenessRange, AreaUpdateTimeSource,
  AreaTalk, AreaSetCharacter, AreaTeleportCharacter, SetMailboxInteraction, and
  the two enter-world signals.
- The client consumed all of it, then went back to polling only
  `CMsgF96DCDB0` every 30 s (16:06:53, 16:07:20, 16:07:50, ..., 16:10:50) with
  `mode=Swallow` from the stale env — i.e. **requests with no results**.
- Conclusion: the bundle + signals are not the gate; the unanswered RPC is.

## Next run

`Run-SWTORClassic-Trace-Tython.cmd` (after killing the servers so the env is
fresh). Expected in `NexusToR.log`:

```
RpcReply: CMsgF96DCDB0: SMSG_RESULTS (mirror) sent to 0x65B3->0x0008 nameLen=9 value="true".
AREA-PAYLOAD type=SMsgResults bytes=... hex=83-02-28-D5-...
```

and the same for `CMsg4A765897` on `0x65AC->0x0009`. Then watch the client log
and the bridge transcript for: a new line after `Active area load complete`,
a different area state in `World travel transition`, `TellCharacterSummaries`,
or a clean disconnect (which would mean the client rejected the reply shape).

If the mirror shape is rejected or ignored, iterate **without rebuilding**:
`SWTOR_RPC_REPLY_MODE=results`, then
`SWTOR_RPC_RESULT_A`/`SWTOR_RPC_RESULT_B` variants (e.g. `SWTOR_RPC_RESULT_A`
empty, or the request name as a visible string like `"OnEnter"`).
