# 2026-09-18 session — client now renders character select + reaches Tython area load

## What changed in SharpServer (built 18:39, verified clean)

1. **Echo/ack replies for the periodic area & world polls** (first change of the
   session, and the one that visibly unblocked the client):
   - `AreaModulesList` → new `AreaModulesListAck` (area routing `0x65B3 -> <AreaServiceID>`).
   - `CMsg7CB9A193` → new `CMsg7CB9A193Ack` (echoes component + body).
   - `CMsgC26464A9` → new `CMsgC26464A9Ack` (echoes component + body).
   - `CMsg61116AD5` (CMSG_CHARACTER_SYNC) → new `CMsg61116AD5Ack`. The client
     sends this once, right after the area-service attach, carrying the applied
     placement (rotation `-90.0002`, position `-64.8741 / -6.906221 / -127.671`
     — exactly the `AreaTeleportCharacter` values) plus the last replication
     stream ID it received (`0x001B502D`, i.e. CRT17). It was the one
     entry-handshake message still left unanswered.
2. **Area startup moved behind the `AreaModulesList` report.** The bundle that
   `ObjectReply` used to emit on area attach now lives in
   `NET/Packets/Server/AreaStartupBundle.cs` (same packets, same order,
   awareness 2 still between CRT10 and CRT11) and is emitted by the *first*
   `AreaModulesList`, guarded by the new `TORGameClient.AreaStartupPacketsSent`
   flag. Rationale below.

## Result of the echo replies (17:15 run)

Before this session the client stalled at the character list and the window
stayed black. With the echoes in place the client:

- rendered the full character-selection screen (3-D model, character list,
  CREATE CHARACTER / PLAY / QUIT), and
- on character select, attached the area service, was teleported, and reported
  `Active area load complete` for tython_blockout in
  `nexusclient/nexusclient/swtor/logs/Client_*.log`.

The client then sits in the loading screen and does not reach in-world.

## Why the AreaModulesList trigger (authoritative source found)

`Server/WorldServer` + `Packets/MessageHeaders` are a C++ reference
implementation of this protocol. Two facts came out of it:

- `Session::HandleClientModules` (ModulesList, `0x2195CC8A`) replies with the
  world startup senders (GauntletVersion, ScriptErrors, TrackingServerInit,
  GameSystemId) — i.e. **world startup is gated on the client's module report**,
  not emitted on attach.
- `msg_area_modules_list.h` has the same `MessageID/StreamID/Payload` shape as
  `msg_modules_list.h`, so `AreaModulesList` (`0x74D16DED`,
  `CMSG_AREA_MODULE_LIST`) is the area-side equivalent report.

In the 16:55 run the area bundle was sent at 16:59:06 (attach) while the
client's first `AreaModulesList` report only arrived at 16:59:11 — the bundle
was therefore delivered before the client finished its own area setup. The
teleport was applied (proven by the character-sync payload), but the area never
came up. Emitting the bundle on the report mirrors the working world flow.

Other reference facts recorded here for later use:
- `CMSG_GAME_STATE = 0xD0D38F43` (our enum calls it `SetTrackingInfo`): body is
  `u64, u64, string`; the reference only logs `Client is in "<state>"`.
- `CMSG_CHARACTER_SYNC = 0x61116AD5`, `CMSG_CHARACTER_SOMETHING = 0xC26464A9`.
- `F96DCDB0`, `C26464A9`, `8EB28DE9`, `HackNotifyData` are handled as **no-ops**
  by the reference WorldServer ("not handling it doesn't change anything"), so
  our echoes are non-canonical but harmless.
- Character-select reference flow: `SMSG_CHARACTER_SELECTED` (empty) →
  `SMSG_TRAVEL_PENDING` (mapName, mapId, 16 bytes
  `{4A 23 FD 46, 00 00 00 40, 01 00 00 00, 00 00 00 00}`,
  `\world\areas\<id>\area.dat`) → `SMSG_TRAVEL_STATUS(1)` →
  `SMSG_SEND_TO_AREA` ("AreaServer-<map>-<id>-1-:areaserver").
  Our SharpServer matches this structurally.
- Unimplemented reference senders that may matter later:
  `SMSG_CHARACTER_SET_RENDEZVOUS_POINT (0x2B4792AE)`,
  `SMSG_CHARACTER_CHANGE_STATE (0xADEAFCA3)`,
  `SMSG_SEND_TO_CHARACTER_SELECT (0x77425A47)`,
  `SMSG_AREA_DISCONNECT (0x30CCCB47)`,
  `SMSG_AWARENESS_EXITED (0xFEE87C7C)`,
  `SMSG_AREA_HACK_DATA_REQUEST (0xBBC9DC07)`.

## CRT fixture structure (decoded from the headers)

`AreaClientReplicationTransaction = MessageID, StreamID, uint32 Unknown, GomUpdate`,
so each `.acrt` body = 4-byte ID + GomUpdate. The IDs are sequential and
monotonic in the low byte:

| CRT | 1 | 2 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|----|----|
| ID low byte | 12 | 13 | 15 | 17 | 19 | 1B | 1D | 1F | 21 | 23 | 24 | 25 | 27 | 29 | 2B | 2D |

(`XX 50 1b 00`, e.g. CRT12 = `24 50 1b 00`, CRT17 = `2d 50 1b 00`.)

CRT12 (26 bytes) parses byte-exact against `base_gom_update.h`:
`[Unknown][ContractUpdates=0][switch 01][count 01][NodeID packed 6B][switch 09][ver 05][fmt 08][len 06][data]`.

**CRT3 (`1.3.acrt.disabled`, 55 bytes) is inconsistent with every sibling:** its
first four bytes are `37 ab 0d 00` (0x000DAB37) where the sequence implies
`14 50 1b 00`. Its 25-byte inner tail matches the captured crash buffer exactly
and ends immediately after the shared 9-byte class blob
`cf 40 00 01 0e 21 8a 83 9c`, while every sibling CRT continues with
`09 05 08 c9 02 .. 1a c9 02 .. 11 cf e0 00 ...` — i.e. the fixture looks
truncated/fabricated from a fragment, not a genuine CRT3. Two consequences:
(a) the earlier `SerializationException` was caused by this fixture, and
(b) suppressing CRT3 entirely (current behaviour) is the right call until a real
capture exists — do not re-enable the 55-byte file.

## Next steps

1. Test the AreaModulesList-gated bundle (this build).
2. If the client still stalls in the loading screen, capture which replication
   stream the client reports next in `CMsg61116AD5` — a value different from
   `0x001B502D` indicates it is waiting for a later/missing stream.
3. Capture a genuine area session to obtain the real CRT3 and any CRTs beyond
   the 16 we have (the ID sequence suggests the real set is longer).
4. Consider `SMSG_CHARACTER_SET_RENDEZVOUS_POINT` / `SMSG_CHARACTER_CHANGE_STATE`
   as candidates for the final "enter world" signal.
