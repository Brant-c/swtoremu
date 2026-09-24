# 2026-09-20 session — enter-world signals implemented (rendezvous + change state)

## What changed in SharpServer (built clean, x86)

1. **Two new server→client packets, bodies decoded from the client dispatch**
   (both subclass `TORAreaServerPacket`, so they carry the area routing
   `0x65B3 -> <AreaServiceID>` like every other area packet):
   - `NET/Packets/Server/CharacterSetRendezvousPoint.cs`
     (`SMSG_CHARACTER_SET_RENDEZVOUS_POINT = 0x2B4792AE`).
     Client handler at `0x64F4BC` reads **(u64, u32, vec3, vec3, u8)** = 37-byte
     body, then an end-of-message check — the same shape as
     `AreaTeleportCharacter` (u64 + u32 + 6 floats + u8), so the teleport's
     placement values are reused: char id, type=1, pos
     `(-64.8741, -6.906221, -127.671)`, rot `(0, -90.0002, 0)`, flag=1.
   - `NET/Packets/Server/CharacterChangeState.cs`
     (`SMSG_CHARACTER_CHANGE_STATE = 0xADEAFCA3`).
     Client handler at `0x6501DD` reads **(u64, string)**; the string reader is
     the same one TravelPending's mapName/mapId use (already working).
2. **`AreaEnterSignals`** (`NET/Packets/Server/AreaEnterSignals.cs`) sends both
   packets once per session, controlled at send time by env vars (server
   restart picks up new values; process env is snapshotted at start):
   - `SWTOR_AREA_ENTER_MODE` = both (default) | rendezvous | state | none
   - `SWTOR_AREA_ENTER_TRIGGER` = sync (default) | bundle | both
     - *sync*: on the client's first `CMsg61116AD5` character sync, i.e. after
       the client confirmed it applied the teleport and every CRT stream.
     - *bundle*: at the end of `AreaStartupBundle.Send`.
   - `SWTOR_AREA_ENTER_STATE` (ChangeState string, default ""),
     `SWTOR_RENDEZVOUS_TYPE` / `SWTOR_RENDEZVOUS_FLAG` (payload overrides).
3. `Run-SWTORClassic-Trace-Tython.cmd` exports `SWTOR_AREA_ENTER_MODE=both`,
   `SWTOR_AREA_ENTER_TRIGGER=sync` by default.
4. New wire verifier `Diagnostics/Test-AreaEnterSignals.ps1` (x86 PowerShell):
   checks both bodies byte-exactly, area routing, and env parsing. All PASS.
   Existing `Test-AreaWireRoundTrip.ps1` still PASS (54 fixtures) and CRT3
   sha unchanged (`f03a79a9…`).

## Correction of the previous session's "RPC round-trip" finding

`CMsgF96DCDB0` / `CMsg4A765897` are **client→server RPC requests**, not
responses to the server's `AreaRequestRPC` calls:

- Their bodies are `[length:4 LE][RPC blob]` — the identical wire shape the
  server uses for `AreaRequestRPC` (`0D 00 00 00 | C7 4F 77 41 …` = 13-byte
  blob). The handoff's "rpc id 09/15/0B/0F" are byte lengths (9/15/21/11),
  not ids.
- No server `AreaRequestRPC` payload ever begins with `09 00 00 00`; the
  client replies' 5-byte prefixes (`C7 71 C3 79 12`, `CF 14 63 F5 32`,
  `CF 6F 6F 2E 93`) are their own packed blob starts, not echoes.
- Disasm proof: client sender functions at `0xA7FEB0` push `0xF96DCDB0` and
  serialize ONE argument with `0x97CB30` — the same blob-writer used by the
  other client poll senders (`ModulesList 0xA7FC42`, `AreaModulesList
  0xA802A2`, `CMsg7CB9A193 0xA80342`, `CMsg61116AD5 0xA800C2`, `CCACB51D`,
  `C26464A9`).

Consequence: Echo/Swallow/Ack equivalence for these periodic script RPCs
(telemetry/heartbeats) was expected; polling replies are a confirmed dead end.

## Client receive-dispatch coverage (checked the full switch, 0x64C000–0x657000)

Handled inbound (server→client): `AreaRequestRPC 0x0ADFF9BF` (handler
`0x64EDF5`: reads one RPC object via `0x97D2A0`, end-check `0x97D020`,
dispatches to the script layer), `CRT 0x0D446E80`, `AreaHackPack 0x0E71623B`,
`AwarenessRange 0x1CA72F2D`, `SMsg23B61238 0x23B61238`, `Talk 0x6BA87A93`,
`TimeSource 0x8F0A39AA`, `Teleport 0x944511BF`, `AwarenessEntered 0xA1D9E226`,
`SetCharacter 0xCFBFFBCB`, `EffEvent 0xDBF41C90`, `HasMail 0x4AA61E6B`,
`SystemRequestRPC 0x2D0B9303`, `GameSystemNotifyID 0x4BD75535`,
`GauntletVersion 0x25ACBEF4`, `WorldRequestRPC 0x25E86D5C`,
`ScriptErrors 0x35BEBAA5`, and all six previously-unimplemented senders
(`0x2B4792AE`, `0xADEAFCA3`, `0x77425A47`, `0x30CCCB47`, `0xFEE87C7C`,
`0xBBC9DC07`).

NOT handled inbound (client→server only, confirms the poll set):
`AreaModulesList 0x74D16DED`, `F96DCDB0`, `4A765897`, `C26464A9`,
`7CB9A193`, `CCACB51D`, `61116AD5`.

## Reader-primitive map (client disasm) — reuse for future packet decoding

| RVA | Reads |
|---|---|
| `0x97C2C0` / `0x97C510` | u64 (throws if <8 bytes remain) |
| `0x97C4C0` | u32 |
| `0x97C530` | u16 |
| `0x97C580` | u8 |
| `0x97C5D0` | float |
| `0xA7FD40` | vec3 (3× float at +0/+4/+8) |
| `0x97D270` | string (obj vtable `0x0111DCD4`) |
| `0x97D2A0` | RPC blob ([len][bytes]) |
| `0x97D020` | end-of-message check |
| `0x97CB30` | blob writer (client→server senders) |

C# `WriteString(s, hasTerminator=true)` emits `Int32(len+1) + bytes + 0x00`
(empty string = `01 00 00 00 00`, 5 bytes) — confirmed by the working
TravelPending parse.

## Bridge travel trace (from last-compatibility-run.log)

Character-select scene completes (selection=1) → Tython travel starts
(selection=0, queued `AreaServer-tython_blockout-4611686019869492753-1-:areaserver`)
→ local area.dat load completes (`0x34F482`, 16:49:05) → `0x350240`,
`0x350461` → `0x34F2B0` (state=3) → `0x241740` "connecting to the destination
area service" (16:49:06) → area attach + startup bundle → client idles in
resource-worker `state=5 queued=0`, polling forever. The two new signals are
sent at the first character sync after that point.

## Next run — what to look for

1. Server log: `AreaEnterSignals: rendezvous sent (sync) …` and
   `change-state sent (sync) …` lines right after `CMsg61116AD5` handling,
   plus `AREA-PAYLOAD type=CharacterSetRendezvousPoint/CharacterChangeState`
   plaintext dumps.
2. Client log / bridge transcript: any new line after
   "Active area load complete" (e.g. world-entry script output, a second
   `TellCharacterSummaries`, or a travel-transition line with a new area
   state) = reaction. A clean disconnect = the client rejected a body; retry
   with `SWTOR_AREA_ENTER_MODE=rendezvous` only, then tweak
   `SWTOR_RENDEZVOUS_TYPE`/`FLAG`.
3. If neither message changes anything, the remaining candidates are the
   SMsg23B61238 "On Enter" RPC batch targets (its payload contains the
   literal `On Enter`) and the client's own unanswered RPC blobs
   (`C7 71 C3 79 12 …`), which now look like script calls into server-side
   GOM objects that this server has not implemented.
