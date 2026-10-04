# Player movement audit — 2026-09-30

Primary confidence: Client-derived. No runtime/config changes, hooks, process
reads, or client launch. The invisible barrier is not yet identified.

## New script evidence from the loaded April Jedipedia reader

`chrBehaviorLocalPlayerClassMethods`, script14987998225829966387:

- Constructor enables character collision on a lightweight node.
- Pre-animation delegate runs input movement, camera handling and final movement
  calculation. Transmission reads the character transform and move vector;
  `BehaviorFinalAnimUpdate` subsequently evaluates sending that state.
- Transmission suppression conditions include combat animation lock, vehicle
  control, recorder playback and stage actors. Repeated movement packets do not
  independently prove an unobstructed proposed movement vector.

`chrBehaviorClassMethods`, script14988119136769865444:

- `chrBehavior_CanMove_PreCPPHSL` calls
  `chrBehavior_CheckCanMoveWithOptionalRotationPermission(false)`.
- Permission rejects visually dead, mobility-locked, vehicle-controlled,
  combat-animation-locked or ballistic characters. These are movement gates,
  not phase membership tests. They are not established active in this run.
- `BehaviorPreAnimUpdate` passes permission/animation conditions to
  `chrLocoAnim_PreAnimUpdate_CPP` and updates the behavior state.
- `BehaviorPostAnimUpdate` reads node position and stores
  `chrBehaviorPreCollisionPosition_w`. Debug rendering compares that stored
  vector against the current character transform and draws the difference.
  This is a useful pre/post-processing distinction, but the field name alone
  does not prove exact engine scheduling, identical coordinate spaces, or a
  specific collision contact.

Reader formatting caveat: the decompiled PreAnimUpdate call displays suspicious
`HIBYTE(float1)` and `BYTE10(float1)` expressions in Boolean argument positions.
Do not treat those expressions as intentional game logic. Native wrapper
`AFA420` independently loads five stack values and a final float, then calls
`AFA130` on the character behavior subobject. Full signature/order must be
checked against the assembly before logging or writing these values.

Dictionary confirms these name hashes, rather than relying on guessed names:

| Name | Hash | April native registration reference | Registered handler |
|---|---|---|---|
| chrLocoAnim_PreAnimUpdate_CPP | D97553EA | AFA53C | AFA420 |
| GetBehaveMoveVector_w | 9E01F9A0 | C1D3D2 | C1A2E0 |
| GetBehaveActionTransformer_w | 32D34133 | C2CC5C | C24EB0 |

The handler targets appear in registration code following the corresponding
name key. This establishes the native binding, not its live invocation outcome.

## Native player-behavior path

Pinned April PE SHA256
`2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494`.
`Locate-PlayerBehavior.py` verifies printed instruction prefixes directly against
this file and writes `player-behavior-native.txt`, `player-behavior-rtti.json`
and `movement-name-bindings.json`. It does not disassemble arbitrary process
memory. RTTI pointer arrays are bounded prefixes, not complete named interfaces.

RTTI identifies BehaviorPlayerCharacterBWA primary table115098C and secondary
table1150A28 (subobject offset8); constructor stores at720DC5/720DCB and
7211A3/7211A9. CharacterNode primary table1151154 is separately identified.
Secondary-table scanning explicitly stops before adjacent UTF16 text that can
look numerically like a code address.

Routine7228A0 uses the player's behavior and another node argument. Its branch
722E06 obtains a manager through global14928F0 +858, prepares transformed
positions and invokes manager slots+20 and+14 with numeric category2. The
slot+14 branch uses the known collision-result structure initializerD023F0.
On repeated positive checks at72303D/723075, branch7230A7 replaces the output
vector with the earlier saved vector. This is a concrete position-rejection
path, but it is NOT yet established as the ordinary walking collision path.

Its direct callers found in the existing listing are7347BC andC1AA3E. The
latter resolves two node references and passes the second as a target. This
target-relative placement/action context means a hook on7228A0 could miss the
doorway while walking normally. Do not install it as a wall observer merely
because it contains collision checks. Nor assume global14928F0+858 is the same
manager as the previously derived area+4B0; identity is unverified.

## What this changes

The previous CollideRaySegment tracing describes a general script ray query.
It remains unproven used by normal walking; a negative ray cannot certify a
clear player sweep. The new findings provide actual movement permission and
pre-collision state semantics, plus exact native bindings, so the next diagnostic
can distinguish denied movement from proposed motion being reduced by physics.
No missing network message follows from these findings.

Next offline target: follow CharacterNode's native update around the
BehaviorPostAnimUpdate call and its position application, identify the actual
walking collision routine and retained hit/room identity. Compare the native
move vector/position inputs and outputs there with the permissions derived
above. Only then prepare a bounded diagnostic around the doorway; do not repeat
phase/UI clearance or hook every ray query.

Existing experiment14 confirms the character can move before the doorway and
again retreat afterwards. A permanent general mobility lock is therefore a
weak explanation, although a transient permission change remains unmeasured.
The five tracked phase triggers being noncollidable at selection snapshots does
not identify all physical contacts. Room selection still does not prove the
character's physical room association.

Continuation: exact BehaviorPostAnimUpdate/BehaviorFinalAnimUpdate dictionary hashes have no raw occurrences in the pinned executable. Their absence does not exclude compiled-script calls or indirect native dispatch. CharacterNode interval727000..7283B0 was added to the byte-verified listing. Routine727CD0 applies saved vectors through6D5D60 then invokes behavior slot28; its purpose and normal walking coverage are not yet established. Do not call it the live collision apply point from adjacency alone. The verified PreAnimUpdate wrapper reachesAFA130 at behavior subobject+1A0 and consumes Boolean gates before updating locomotion state. Physical sweep/contact identity remains unresolved.

Follow-up: NATIVE-COLLISION-PATH.md now traces behavior update722250 -> controller737120 -> movement collision737520/7B7450 and floor support739AE0/738F80/CEF540. This supersedes the broad offline-search next target above; live doorway coverage and hit identity remain unmeasured. Byte verification now covers11892 instruction prefixes. No runtime change.
