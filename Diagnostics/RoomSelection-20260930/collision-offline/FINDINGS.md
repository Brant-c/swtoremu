# Collision path after successful room selection

Primary confidence: Client-derived. No runtime changes or client launch.
Experiment08 established gnarls_new selection/activation with wall remaining.

## Script path and important limits

_JPEXTRACT/phsPhasedInstanceClassMethods.txt:6-34:
OnReplicationNodeCreate separately scans type4 gateway sources for visuals and
attachment, then type3 matching TriggerParam identifiers for the cached
phsPhasedInstanceToTrigger collection. Gloms TriggerInstance if needed.
The source does not establish live collection membership in our client.

_JPEXTRACT/phsOracleClassMethods.txt:318-361:
UpdateGatewayForInstance resolves phased instance, RequiresGatewayUpdate,
eligibility and output values; initializes collision Boolean false before
GetInstanceGatewayState. _SetGatewayState can force it false for instanceID0
or character allow-instances. It updates FX separately, then writes Collidable
only on cached region triggers if phsCollisionStatePerInstance differs.
A skipped write does not prove the existing native collision bit is clear.
Destroy callback enters this update only if its parent/membership/player
conditions pass; no nested gateway update was observed in three valid runs.
That absence does not exclude updates from other callers.

Crucial correction to old checkpoint447: derived class overrides collision
output for additional states. Green FX alone is not collision permission.

| Derived class state | FX | Collision output, caller initialized false |
| --- | --- | --- |
| phsCanExit | green | false |
| phsHasPhaseLock | green | true |
| phsCanJoin | blue | false |
| phsCanOwn | green | false |
| phsCanOwnOrJoin | green | true |
| phsCanJoinMultiple | blue | true |

Other states delegate to base, which sets true for denied/combat states.
See phsClassPhasedInstanceClassMethods.txt:157-187 and base:177 onwards.
Banner or green visual does not independently prove phsCanExit. Older claims
that the phase barrier is excluded on that basis were too strong. No live
eligibility/cached collision value has yet been established.

## Exact native path

Pinned April executable SHA256:
2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494.
Trace-CollisionOffline.py verifies357 printed instruction prefixes and PE RTTI.
No process reading/scanning. Existing listing prefix check is not fresh decoding.

- Native property dispatcher starts7FD8C0. At7FD9FB it compares name with
  UTF16 Collidable at1147BAC, converts value via6C8080, and at7FDA27 passes
  property keyB4963DC1 plus Boolean to vtable+ B4.
- PE vtable116116C has slot+ B4=7FDE70. Its complete-object locator11B7010
  and type descriptor133723C name it .?AVTriggerNode@@. Constructor7FB206
  installs this same table. These are exact static identities.
- TriggerNode Boolean setter7FDE70: ECX=this, stack property key and Boolean,
  returns Boolean inAL, ret8. KeyB4963DC1 branch sets object+E0 bit0x1000,
  compares old/new, and performs no physics call if unchanged.
- Bit turns on: custom-register routine6D4FB0 (object inEAX) requires object+98
  room and object+F0 collider, bit1000, room+120 area and area+4B0 manager.
  Marks collider+2C bit40 and callsD1E7B0 with collider pointer.
- Bit turns off:6D4F60 (ECX=this) checks existing room/collider/manager and
  collider+2C bit40, clears it, callsD13480 with collider pointer.
- Getter at7FC764 reads the same object+E0 bit12 for Collidable.

Therefore there is a precise native collision-state/physics-association path
separate from room selection. Custom EAX routine6D4FB0 must NOT be treated as
an ordinary thiscall hook. No physical barrier identity or live bit proven.

## Next concrete target, before another run

Establish bounded identity reads for TriggerNode name/TriggerParam and position
from the native property interface or its verified layout; relate it to the
knight INSTANCE_REGION asset volumes. Then one opt-in log target can observe
only Collidable keyB4963DC1 at7FDE70, original return/old-new bit/room/collider
association, without scanning, changing state or intercepting unrelated flags.
Absence of setter calls cannot by itself prove no blocking trigger exists;
constructor/default state and cached-write suppression remain alternatives.
Do not fabricate triggers, toggle arbitrary collision bits, send guessed CRT18,
or claim a missing opcode from these findings. No further client request yet.
