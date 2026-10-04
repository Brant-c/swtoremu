# Handover — 2026-09-29 — Locating the "notify area of new player" message opcode

Read-only disassembly work this session. **No client DLL changes, no server code
changes.** (One leftover server edit from a prior session is noted at the end.)

## Goal

Open the invisible wall at X = -62.92 in the Tython Masters' Retreat so the player
can walk out into `gnarls_new`.

## Established before this session (do not re-derive)

- Room geometry + collision is loaded **client-side** (`bwa::AreaManager` builds
  `CollisionRoom`/`CollisionScene`). It is a native engine operation, not a stream
  we can build. (Handover-20260928 §§14–22.)
- The client sits in the loading state **"Waiting for server to notify area of new
  player"**; collision staging never fires. That notify is the blocker.
- The door-crossing phase-exit destroy CRT **is delivered and applied**
  (`CrtApplyHook`, §24) but does not open the wall.
- `SetCharacter` re-order was tried and did **not** open the wall.
- CRT18 room stream and awareness re-send are **dead ends** (`.aaw`/`.acrt` are
  non-idempotent creation batches → "Character already exists", §§21–22).
- `_Room_Activate` is server-only, not a client RPC (§15).

## Biggest correction this session: how opcodes are actually known

**Opcodes are a known table, not something we compute.**

`Server/Framework/Src/Network/Packet.h` defines every message as
`SMSG_<NAME> = 0x<opcode>`, ported from the SWTOR server protocol. The client's
dispatcher independently confirms them: it is a `cmp eax,<opcode>` chain whose
values match the table one-for-one (e.g. `SMSG_CLIENT_REPLICATION_TRANSACTION =
0x0D446E80` ↔ `cmp eax,0D446E80h` at `0x0064EDC3`).

**=> To get an opcode, look it up by name. Do NOT try to hash/derive it.**

Dead ends ruled out this session (kept so nobody repeats them): the GOM "classic"
hash, the GOM "bitmath" hash (including lowercase + `0xdeadbeef` seeds), CRC32,
FNV-1a, and DJB2, tested against real name↔opcode pairs — none reproduce the
opcodes. Note: classic(seed `0xDEADBEEF`) and bitmath(seed `0,0`) are the *same*
function (identical outputs), so they are one dead end, not two.

Real pairs used (client-logged string ↔ opcode):

| logged string (client VA) | opcode | Packet.h name |
|---|---|---|
| `AssetCreated` (0x1140864) | `0x699FAC0E` | SMSG_ASSET_CREATED |
| `ClientReplicationTransaction` (0x114088C) | `0x0D446E80` | SMSG_CLIENT_REPLICATION_TRANSACTION |
| `HackPackFromArea` (0x113EFF0) | `0x0E71623B` | SMSG_AREA_HACK_PACK |
| `HackDataRequestFromArea` (0x113EFD8) | `0xBBC9DC07` | SMSG_AREA_HACK_DATA_REQUEST |
| `LogDebug` (0x114090C) | `0x10FF67AB` | SMSG_LOG_DEBUG |
| `InstanceCreated` (0x1140848) | *(none)* | *(not in Packet.h)* |

VA→file helper: `file = 0xD3F9D0 + (VA - 0x11407D0)`.

## The full "area message" dispatch tree (0x0064ED70) — mapped

Binary search over the opcode (`arg2 = [ebp+0Ch]`). Opcode → handler:

| opcode | name | handler |
|---|---|---|
| 0x0ADFF9BF | AreaRequestRPC | 0x0064EDF5 (fallthrough) |
| 0x035C75FE | SetBehavior | 0x0064EEBF |
| 0x992D20 | ? | 0x0064EFBB |
| 0x0D446E80 | CRT | 0x0064F0B4 |
| 0x10FF67AB | LogDebug | 0x0064F1F4 (fallthrough) |
| 0x0E71623B | AreaHackPack | 0x0064F2ED |
| 0x1CA72F2D | AwarenessRange | 0x0064F3C0 |
| 0x2B4792AE | SetRendezvousPoint | 0x0064F4B6 (fallthrough) |
| 0x23B61238 | RequestMultipleRPC | 0x0064F5BB |
| 0x2F37A18B | CLI | 0x0064F6B1 |
| 0x699FAC0E | (Packet.h: AssetCreated) | 0x0064F7CC (fallthrough) |
| 0x30CCCB47 | AreaDisconnect | 0x0064F8A1 |
| 0x6AFFFFB1 | EditBinaryCommand | 0x0064F95F |
| 0x8F0A39AA | UpdateTimeSource | 0x0064FA9F (fallthrough) |
| 0x8EBB0A67 | LogWarning | 0x0064FB71 |
| 0x6BA87A93 | Talk | 0x0064FC57 |
| 0x944511BF | CharacterTeleport | 0x0064FD98 |
| 0xAB69A205 | IDBatch | 0x0064FEB9 (fallthrough) |
| 0xA1D9E226 | AwarenessEntered | 0x0064FFD2 |
| 0x9553F230 | RenameAccountLegacyNameStatus | 0x006500DD |
| 0xADEAFCA3 | CharacterChangeState | 0x006501DD |
| 0xD105177D | LogError | 0x0065030D (fallthrough) |
| 0xCFBFFBCB | SetCharacter | 0x00650405 |
| 0xBBC9DC07 | AreaHackDataRequest | 0x006504C7 |
| 0xD3DA98F0 | EditCommand | 0x0065059A |
| 0xDBF41C90 | EffEventMessage | subtree 0x0065066A (`cmp eax,0DBF41C90h` @ 0x0065066A — **not mapped further**) |

Default / unknown-opcode path = `0x00650687` (deserializes then calls `009C1540`,
NOT `009C1250`).

## The 28-entry "system message" table in .rdata

File `0xE824A0` → **VA `0x00C832A0`**; 28 entries × 16 bytes:
`{ u32 type = 9, u32 class = 0x01323FE4, u32 fieldOffset, u32 handler }`.

Each `handler` is a **separate cold block that ends in `ret`** (not the
`jmp 006509AB` epilogue used by the tree handlers); it logs a name string and calls
the shared `009C1250`. Its `fieldOffset` is the stack slot the dispatcher puts the
message's string field in.

Selected entries:

| fieldOffset | handler | logged name |
|---|---|---|
| -0x1A4 | 0x0064F047 | `InstanceCreated` |
| -0x190 | 0x0064F845 | `AssetCreated` |
| -0x1AC | 0x0064F166 | `ClientReplicationTransaction` |
| -0x14C | 0x0064F28E | `LogDebug` |
| -0x1B4 | 0x0064F361 | `HackPackFromArea` |

Remaining handlers in the table: 0x0064FD1B, 0x0064EE69, 0x0064F63F, 0x0064FF61,
0x0064F903, 0x0065046B, 0x0064EF53, 0x0064FB1E, 0x0064FE42, 0x0064F55F,
0x0065026A, 0x0065060B, 0x0064F745, 0x0064FA03, 0x00650075, 0x00650764,
0x0064F439, 0x0065053B, 0x0065093F, 0x0065016C, 0x006503A6, 0x0064FBF8,
0x0065086F.

**Open problem:** the dispatcher that reads this table was NOT located. The table
address (VA `0x00C832A0`, RVA `0x8832A0`) has **no** direct or relocatable
reference in `.text` (searched `C832`, `C83200`, `C83280`, `8832A0`, and the raw
pointer value). The handlers are referenced *only* from this table. Next step is to
find the function that indexes it (likely via a runtime pointer/registry).

## Client loading state machine (the thing that is stuck)

Strings (VA `0x1153A00` region), in order:

    Waiting for server instance to start              (0x1153A6C)
    Waiting for server to notify area of new player   (0x1153A94)  <-- STUCK
    Waiting for area connection                       (0x1153BDC)
    Waiting for replicated character                  (0x1153BF8)
    Client area load / Streaming in assets / Loading HUD /
    Loading area dat file / Loading area assets / Area transition

The string is referenced at `0x00715DE1`, `0x0074F2CA`, `0x0074FD9F`.
Loading-UI update function is at `0x0074F2B0`; it reads the state value at
`[obj+0x8C]` and compares it to `3` (`0x0074F2E7`).

## Unverified claim — do not build on it blindly

Repo-wide grep: **`InstanceCreated` and `AssetCreated` appear in zero of our
notes**, and `"Waiting for server to notify area of new player"` appears only in
the *client binary*, never in a doc. The "the notify is
InstanceCreated/AssetCreated" claim comes only from the session summary. Treat it
as a hypothesis, not a finding.

## Recommended next steps (in order)

1. **Pin the opcode definitively.** Trace how `[obj+0x8C]` advances past the
   "notify" state (start at `0x0074F2B0` and its callers, plus `0x00715DE1`), or
   locate the dispatcher that indexes the `0x00C832A0` table. Either gives an
   exact opcode with no guessing.
2. **Cheap experiment.** `SMSG_ASSET_CREATED = 0x699FAC0E` is a *known* opcode,
   the client logs the string `AssetCreated`, and it is absent from the startup
   bundle. Requires a new C# packet under `SharpServer/NET/Packets/Server/`.
   **Settle this ambiguity first:** in the client, opcode `0x699FAC0E` binds to
   handler `0x0064F7CC` (two reads via `0x0097C510` ⇒ two u64s), whereas the block
   that logs the *string* `AssetCreated` is `0x0064F845` (string field + body via
   `0x006400F0`). Confirm which is the real wire shape.
3. `SMSG_SEND_TO_AREA = 0x13509F15` already exists in Packet.h and
   `SharpServer/NET/Packets/Server/WorldSendToArea.cs` exists — check whether the
   "notify" is really this already-known message rather than a new one.

## Files created this session (all under Diagnostics/, none are build inputs)

- `test-msghash.py` — GOM bitmath hash vs candidate names.
- `test-msghash2.py` — GOM classic hash, case/seed variants.
- `test-realpairs.py` — both hashes vs the real name↔opcode pairs (no match).
- `HashMessages2.cs` / `.exe`, `HashMessages3.cs` — earlier hash probes.

## Carry-over caution (from Handover-20260928 §19)

Do **not** add a client hook without deriving the full signature from
`swtor-disasm.txt` first — the `AreaMessageDispatch` hook crashed the client twice
(`__stdcall`/`__thiscall` mismatch + truncated args). The safe
`ParseInboundFrame_Hook` opcode filter remains in `Client/Hook/Src/ToR.cpp`.

## Leftover state to tidy

`SharpServer/NET/Packets/Server/AreaStartupBundle.cs` still carries the prior
session's `[EXPERIMENT]` `SetCharacter`-first re-order (it did not help; safe to
revert).
