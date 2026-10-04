# Architecture

Assessed 2026-10-04 against cached upstream `79eb5e9`, HEAD `7785bc8` and the
dirty working tree. Source inspection and offline checks are distinct from
native client acceptance. Path provenance does not establish correctness.

## Original architecture

Upstream contains two implementations, not one modern consolidated server:

- `Server/`: C++ Framework/network/DB/event machinery, ProxyServer,
  WorldServer/Logic sessions and handlers, TimeServer, Script and PluginNet.
  `Server/WorldServer/Src/Swtor.cpp` and `Logic/World.cpp` show the native world
  path; the old Visual Studio/CMake builds require historical dependencies
  such as Boost, crypto++, zlib and ODBC. They are preserved, not validated
  as the current playable runtime.
- `SharpServer/`: C# login, shard/world/area dispatch and time service, plus
  a separate HTTPS shard-list executable. Vendored MongoDB/crypto/zlib and
  packet classes are inherited. `TOR/Character.cs` already leaves DB loading
  as a TODO. `WorldSendToArea` already fixes the Tython destination.
  `AreaServer/{CRT,Awareness,EffectEvents,HackPacks}.cs` and the matching
  `bin/Debug/AreaServer` fixtures also existed upstream. Snapshot use is an
  inherited technique, although the currently playable replay sequence is local.

`Packets/`, `Parser/`, `Client/` and `Hacks/` retain original protocol, capture
and client tooling. Duplicate-looking projects are not automatically obsolete.
For example both Hero copies are upstream; `Tools/tor_tools` explicitly depends
on its own Hero project. Their PackedStream files differ, so neither was deleted.

## Current executable path

`SharpServer/Program.cs` starts login (7979), shard (20060) and time (20066)
handlers in one process. It does not initialize Database or start PlatformServer.
`ShardListServer/Program.cs` separately reads `Shards.xml`, generates a localhost
self-signed certificate, and listens on 443 and 8888. These listeners bind broadly
in source; their successful build does not establish deployment readiness.

The local path is: shard-list/login and RSA exchange → connection/service
dispatch → captured character list → selected character ID → world module
readiness → area attachment/readiness → AreaStartupBundle → movement/RPC
handlers. TORGameClient holds service IDs and startup flags. Packet families
share compression/cipher transport; the local TORAreaServerPacket centralizes
area routing. `NET/Protocol/PacketCursor.cs` and associated message decoders
separate bounded parsing for selected messages, not every original packet.

AreaStartupBundle now supplies a fixed startup from fixtures, remaps selected
player identity, changes phase ordering and player fields, teleports to a fixed
spawn, and emits awareness/effects. CMsgF96DCDB0 dispatches selected local
ability, Weller and taxi handlers; generic unresolved RPC traffic can be swallowed.
PlayerMovementState and RetreatGatewayState approximate one retreat boundary.
They are not an authoritative world simulation, room manager or phase allocator.

## Why the fork diverged

| Difference | Upstream → current | Interpretation |
|---|---|---|
| Login / toolchain | One RSA block, historical framework/build settings → block loop, .NET 4.8 and Detours changes | Intentional local compatibility progress; retain |
| Selected player | `CharID + 1` with upstream comment questioning it → exact ID plus remap | Preserve correction; persistence still absent |
| Modules / startup | Empty module-list handlers → deferred world sequence and area replay | Local progress that reaches the client; readiness semantics still patched |
| Area serializers | Individual fixed component assumptions → shared area routing and corrected framing | Preserve; routing/blob/wire offline checks pass |
| Client assets / repository | Original paths/tooling → TorArchive, repository responses and compatibility bridge | Added to make the April client consume prepared assets; isolation and version identity remain necessary |
| Player/phase state | Captured fixtures → forced mobility/loaded, phase reorder, loading-confirmation fallback | PATCH/BYPASS; rendered world is not a complete lifecycle |
| Movement / story / taxi | Limited handlers → tether, retreat detector, selected ability/story replies, synthesized taxi attempts | Mixed local controls and experiments; no general feature completeness |
| Logging | Shared mutable List → locked Queue in existing Log class | Intentional concurrency fix; preserve, avoid adding another logger |

Dirty files and Cline checkpoint refs establish later work but not who authored
every line. The three normal fork commits combine many unrelated changes.
Root one-shot probes are session artifacts by function/history; a file is not
discarded merely because it may have been AI-assisted.

## Boundaries

Runtime stays in SharpServer/Client; packet/content tools stay in Tools;
research fixtures, exact results and protocol confidence stay in Diagnostics.
`scripts/` only builds, starts existing server components and snapshots logs.
`Archive/` is retained reference material. Future read-only AI/Jedipedia/native
client research tooling must live separately and must not become a runtime
dependency. This cleanup implements no such research layer.
