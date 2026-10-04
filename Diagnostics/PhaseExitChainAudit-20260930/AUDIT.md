# Phase exit chain audit — 2026-09-30

The selected character leaves the retreat phase in experiment14, but exterior
traversal still fails. The reviewed client phase-exit chain contains no additional
room-transfer or movement-release call after the observed callback. This narrows
the investigation; it does not establish complete physical transition readiness.
No runtime, launcher, packet, or collision behavior changed during this audit.

## Evidence boundary

Client-derived semantics below come from extracted April scripts and the loaded
Jedipedia reader, identified as 1.2.0. Live observations come exclusively from
`../PhaseFormat-20260930/live-20260930-222139/RESULTS.md` and its saved tails.
The pinned native format finding remains in `../PhaseFormat-20260930/FINDING.md`.
Script semantics do not establish a missing network opcode or production server
ordering. Unknown exported bodies and dynamic Hydra hooks remain explicit gaps.

## Chain and coverage

| Step | Script behavior | Latest run / limitation |
|---|---|---|
| Local character field notification | `phsEntity.Replication_Update` matches `phsPhase`, compares with local player, calls `PHASE.OnPhasedInstanceUpdated` | Both comparisons and callback observed at 22:21:51 |
| Resolve membership | Oracle resolves phase-info parent and new instance name, compares with cached old name | New instance name zero observed; startup resolved retreat name `FF5F184AAA9ECE77` |
| Character instance change | `phsParticipant.OnInstanceChanged` sets GUI instance name and refreshes nearby client spawners | Call returned; individual spawner activation outcomes were not measured |
| Old instance exit | Retreat class override `OnPlayerExitedInstance` fires the attacking-enemies tutorial event | Exit call and completion checkpoints observed; no transfer call in this override |
| Exit UI and gateway | Clears join override, updates exiting GUI, refreshes old instance gateway | Exit branch completed and user saw phase UI leave; nested gateway decision and trigger list contents not recorded |
| Entity notification tail | Companion/crafting handling, invalid-target clearing, group invite UI | Reviewed full reader method; no room activation, instance transfer, or movement release in this tail |
| Native exterior selection | Separate native room selection/activation | `gnarls_new` selected/activated at 22:21:50; this does not prove controller residency, complete content, or contact readiness |

The transaction applies phase-info removal before the deferred entity notification.
Nevertheless the oracle resolves the cached old instance and follows its exit
branch. Existing live evidence therefore does not support claiming that removal
prevented this exit callback. Production ordering is still not independently
captured.

## Gateway branch: the remaining phase-related gap

`UpdateGatewayForInstance` resolves the instance, checks `RequiresGatewayUpdate`,
then calls `DeterminePhaseEligibility` and `GetInstanceGatewayState`, obtaining
FX states and a blocking Boolean. `_SetGatewayState` updates gateway FX separately
from physical blocking. It forces blocking false for area instance ID zero or the
character allow-instances override. It writes each registered trigger's
`Collidable` property only when the cached `phsCollisionStatePerInstance` differs
from the requested Boolean. Its physical list is `phsPhasedInstanceToTrigger`.

Consequences:

- An exit callback and disappearing story banner do not prove the gateway's
  final Boolean or physical list is correct.
- No Collidable setter at exit can be normal when the cache already equals the
  requested value; it is not proof the gateway update was omitted.
- `phsCanExit` selects an unblocked gateway state in the reviewed class mapping.
  After membership clears, eligibility is recalculated through ownership, quest,
  group, lock and combat rules. The final state in this run is not known.
- Trigger registration binds type-3 matching phase parameters to the physical
  list. Type-4 matching gateways also create a client gateway clone for entry
  detection/FX. The clone enables Enter and disables Leave; do not assume its
  leave event implements the server's phase exit.

The authored inventory contains one INSTANCE_GATEWAY and three INSTANCE_REGION
objects for `tyt_jedi_knight_masters_retreat`, all authored Collidable=false and
ExistsOn=Server. See
`../TriggerCollision-20260930/authored-retreat-trigger-targets.csv`.
Five runtime objects tracked by the existing diagnostic exclude the native
Collidable bit `0x1000` at the saved room-selection snapshots. This weakens those
specific objects as a persistent collidable gateway explanation, but neither
establishes their membership in the script lookup nor identifies the actual
contacted object. Snapshot `result=0` is a placeholder, not a getter result.

## Separate branches reviewed

`SPAWNER.UpdateClientOnlySpawnersInProximity` refreshes nearby anchors, loads their
specifications if needed, computes phase/quest/override activation and creates or
destroys client NPCs. The reviewed activation/deactivation methods contain no
direct room-stream or gateway Collidable update. Individual NPC outcomes are
unmeasured; this is not a proof that every physical object is unrelated.

`phsWorldPhasedInstance` defines another type of phased content with its own
eligibility and gateway rules. It is not evidence that ordinary exterior space
requires assigning the character a new world phase.

`sysBaseClient._Room_Transition` in both the local extraction and the reader is
an effectively empty script body (`var unused = a4.length`). Native engine room
work is separate; this script cannot supply a missing transition packet schema.
Full area travel performs unload/load, oracle initialization, fades and movement
handling. Nothing in the reviewed local retreat exit chain proves that a full
area transfer is required for this doorway. The retreat prototype's exit-area
fields are zero. `RequestInstanceTransfer` must not be substituted solely because
its name resembles the desired action.

The retreat prototype references
`hyd.generic.class_phases.jedi_knight.phase_jk_class`. Its complete dynamic Hydra
server/runtime actions were not available as a semantic local export in this
audit. Client exit callbacks alone cannot certify that entire production server
flow. This remains an audit limit, not evidence for a particular missing message.

## Emulator comparison and next steps

The temporary server crossing detector clears the selected player's `phsPhase`
and removes the phase-info child. Experiment14 verifies that phase/UI effect.
It does not implement a general trigger runtime or prove native physical room
transition semantics. CRT18 remains suppressed; no evidence justifies enabling
it or adding guessed transfer/RPC messages.

Next work, in priority order:

1. Audit existing native collision/controller code and saved boundary evidence
   to identify the query/filter that stops movement and how it chooses room
   residency. Reuse existing `RoomSelection-20260930/collision-offline` and
   `MovementC7-20260930/jedipedia-comparison` findings before adding diagnostics.
2. Cross-reference the blocking object's identity against the registered phase
   triggers and room content. If it is a phase trigger, investigate the gateway
   decision, cached state and list membership. If it is a room/content object,
   investigate its room activation/filter lifecycle.
3. Recover the referenced Hydra actions if they can be located in the available
   content, especially any explicit doorway/room action; do not infer them from
   the prototype name.

No new client run is needed to repeat membership clearance. A subsequent run
should answer a specific unresolved physical or gateway question with bounded
logs, only after the relevant native path and expected observation are defined.

## Reader script identities inspected

- `phsEntityClassMethods`: 14988219368268985980
- `spnOracleClassMethods`: 14988197701636805405
- `phsWorldPhasedInstanceClassMethods`: 14988107479794948855
- `sysBaseClientClassMethods`: 14988129110554817399

Additional local semantic sources: `_JPEXTRACT/phsoracleclassmethods.txt`,
`phsParticipantClassMethods.txt`, `phsPhasedInstanceClassMethods.txt`,
`phsClassPhasedInstanceClassMethods.txt`, `phsPhaseInfoClassMethods.txt`,
`_BaseClientClassMethods.txt`, `sysTravelClassMethods.txt`,
`chrCharacterClassMethods.txt`, and `phs.tyt_jedi_knight_masters_retreat.txt`.
