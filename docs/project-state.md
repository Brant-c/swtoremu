# Project state and dependencies

Assessed 2026-10-04. WORKING means the stated bounded capability only, not a
complete production subsystem. This cleanup performed no client run.

| Subsystem | Status | Evidence / limitation | Downstream dependency |
|---|---|---|---|
| C# build / offline packet tooling | WORKING | Current server and shard-list build; routing/blob/wire/workbench checks pass | All runtime work |
| Login / shard discovery / time | PARTIAL | Existing log evidence reaches world; RSA block fix and local shard-list preserved; real account auth not established | Character selection / world handshake |
| Character list / selection | PATCHED | Captured list, exact selected ID; inherited Character(ID) does not load DB state | Spawn, effects, story, persistence |
| World / area handshake | PATCHED | Local ModulesList readiness, client dispatch/loading compatibility bridge; normal confirmation incomplete | World readiness, transitions, all gameplay |
| Area replication framing | WORKING | 38 blob cases / 54 wire round trips and dynamic area handles; bytes only | All area state delivery |
| Player update semantics | UNKNOWN | CRT16 mobility split and CRT17 loaded/stat map work locally; full native schema26 read order unresolved | Loading, movement, effects, actors |
| World entry / spawn | PATCHED | Captured replay and fixed teleport; accepted rendered/movable world | NPCs, phase, interactions, abilities |
| Area / room lifecycle / streaming | UNKNOWN | Fixtures are creation data; no proven general room stream/reset/transition contract | Multi-area travel, dynamic awareness, NPC lifecycle |
| Shard / instance ownership | PARTIAL | Fixed Tython instance and captured phase IDs; no general allocator | Group/quest phases, persistence, room transitions |
| Phase resolution / membership | PATCHED | Accepted retreat exit/reentry and improved timing; axis-aligned corridor/hysteresis | Story eligibility, visibility, interactions |
| Movement authority | PATCHED | Client coordinates drive tether refresh; finite values and selected variants only | Trigger activation, combat range, travel |
| Dynamic entity lifecycle / spawning | PARTIAL | Captured actors and fixtures; no general authored spawn/lifetime manager demonstrated | NPCs, objects, combat, quests |
| NPC / object interaction | PARTIAL | Weller model/nameplate predates local conversation; medcenter visible but not targetable per operator | Conversation, services, quest/taxi interaction |
| Conversation / story | PARTIAL | Weller first conversation / normal end accepted in checkpoint; selected local replies | Quest progression / persistence |
| Abilities / effects | PARTIAL | Local experimental replies/effect replication; selected use is not complete ability semantics | Combat, buffs, phase/effect ownership |
| Combat | PARTIAL | Opt-in combat experiment exists; general targeting/damage/AI not established | Quests / encounters |
| Quest progression / save/load | NOT IMPLEMENTED | Character load TODO; no validated durable quest lifecycle | Reconnect correctness, eligibility |
| Taxi creation / travel | NOT IMPLEMENTED | Experimental creation has errors and no accepted terminal; travel pending | Depends on actor/interaction/area foundations |
| Legacy C++ runtime viability | UNKNOWN | Preserved upstream architectural evidence; historical dependencies not built here | Comparison / future architectural decisions |
| World-entry offline check | BROKEN | Fails a missing RequestWorldFadeIn observer assertion before and after cleanup | Verification quality; does not prove gameplay broken |

## Known patches and consequences

| Patch / source | Provenance | Foundation approximated | Consequence / unresolved risk |
|---|---|---|---|
| Snapshot CRT/awareness/effects | UPSTREAM technique, local startup wiring | Selected character/current-area state generation | Captured identities and stale state; replay can duplicate actors |
| Fixed Tython route and ID-only character | UPSTREAM | Persistence and destination selection | Every selection uses captured start rather than saved state |
| CapturedCharacterRemap byte scan | PATCH/BYPASS (fork) | Field-aware identity allocation | Other fixed IDs remain; byte pattern matching is not schema-aware |
| Generated CRT1/4 phase ordering | PATCH/BYPASS (local) | Phase creation/ownership ordering | Local captured control, not a general eligibility engine |
| Safe Login removal; forced mobility/loaded | PATCH/BYPASS (fork + dirty changes) | Effect/readiness lifecycle and player serialization | Downstream ability/movement state may mask an encoding/lifecycle defect |
| CompatibilityLauncher loading branch fallback | PATCH/BYPASS (fork/dirty) | Original phase-confirmation exchange | Local load success does not prove normal server completion |
| Tether refresh; retreat detector | LOCAL-VALIDATED bounded behavior, PATCH/BYPASS architecture | Authoritative movement/trigger/phase evaluation | No general group/quest/rotated-volume or area authority model |
| AreaReplicationDestroy positive-effect replacement | EXPERIMENTAL coupling | Phase exit mutates effects | Possible buff/client bookkeeping loss; hypothesis, no live reproduction |
| AreaStartupPacketsSent before Send completes | Later local startup defect | Transactional entry completion | Exceptions/merged-awareness failure can leave partial entry marked sent |
| Connection-scoped flags; movement routing guard | Later local implementation | Entry reset / packet authority | Second area and wrong-component movement lack demonstrated safe boundaries |
| Echo-only AreaEnterSignals call in Swallow baseline | Later local coupling | Final state/rendezvous signaling | Environment settings do not establish that the packet was sent |

Source review: `Diagnostics/Foundation-Audit-20261004.md`; bounded behavioral
evidence: RetreatReentry/prelaunch-20261001-002114-440/RESULTS.md and
RetreatGateway/prelaunch-20261001-003805-442/RESULTS.md. Claim confidence remains
in Protocol-Evidence.csv. No new wire-contract claim is promoted by this audit.

## Highest-leverage investigations

1. **Player encoding and loading readiness.** Reconstruct the April native
   schema26 reader for mobility, loaded and stat map, compare upstream packed
   implementation and actual transformed bytes. Determine whether splitting
   records masks a demonstrated defect; keep the accepted control.
2. **Selected-character/area entry ownership and completion.** Recover normal
   phase-confirmation exchange, define selected-player/area/instance ownership,
   transactional completion and reset boundaries. This blocks durable characters,
   multiple areas, dynamic actors and travel together.
3. **Phase/actor/effect lifecycle separation.** Determine whether phase exit
   needs the unrelated effect replacement; trace a captured medcenter as the
   actor/interaction control before synthesizing more actors or taxi streams.

These are investigations, not permission to implement another visible feature.
