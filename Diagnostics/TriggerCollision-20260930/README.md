# Retreat trigger collision log — experiment09 prepared, not yet run

Purpose: test collision flags/physics association on native trigger objects for
`tyt_jedi_knight_masters_retreat` after successful room selection. Diagnostic
only; no fix, collision write, guessed packet or extra game-function call.

## Derived identity and state

Primary confidence: Client-derived. See
../RoomSelection-20260930/collision-offline/FINDINGS.md and verified excerpts.
600 printed instruction prefixes now match pinned April PE, plus TriggerNode
RTTI and virtual slots. Field identity is independent of old memory scans.

- TriggerNode virtual94 =7FE1F0, ECX=this, stack(property key,wchar pointer),
  Boolean AL return, ret8. TriggerParam keyD84FB395 branch assigns string at
  object+138; dereferences its first pointer for native string hashing at
 7FE27F. Hash stored+148/+14C. Safe bounded reads use this observed pointer.
- Name property stores the same string representation at+110 (7FD918).
- Collidable Boolean setter7FDE70, ECX=this, stack(key,byte value), AL/ret8.
  KeyB4963DC1 updates+E0 bit1000, then changes physics association on transition.
- Entity+98 room, +F0 collider, collider+2C bit40 tracks association path.
  Read failure is FFFFFFFF, null is0. Neither flag alone proves all collision.
- Native vector setter6D5D60 uses local transform at+24, cached position floats
  at+2C/+30/+34; low-byte flagbit2 gates cache validity. Matrix translation can
  supply it lazily. Logger emits raw bits and transform flags, makes no world
  position claim, performs no getter call. Match authored coordinates only
  when cache/context justify it; no guessed offsets or geometry edits.

Four authored targets exported in authored-retreat-trigger-targets.csv with
asset SHA256 in authored-input.json: one gateway and three INSTANCE_REGIONs.
All authored ExistsOn=Server, Collidable=false. These settings are NOT proof
of presence/absence or native collision value in this reconstructed client.

## Single diagnostic change and bounds

SWTOR_TRACE_TRIGGER_COLLISION=1. Same29 settings as experiment08 otherwise.
Existing room logging retained for correlation. No server/packet changes.
Two new exact48-byte native prefix gates. No absolute addresses within these
prefixes; known RVAs work at relocated module bases. Either mismatch disables
both with UNSUPPORTED. INSTALLED only after Detours transaction commit.

Logs target TriggerParam assignment return and Collidable before/return, each
max256events. First8 other TriggerParam writes provide positive-control logs.
Original calls forwarded once even after cap; AL return and LastError retained.
Known target pointers remembered in fixed64slot event-derived table, atomic
publication. Existing room-selection events take at most32 bounded snapshots
of that table before/after selection; revalidate TriggerNode vtable and exact
parameter each time. No process/heap/address-space search or polling.
Snapshots catch unchanged collision state even if no setter call occurs.
Table/snapshot/event cap markers make later absence claims inconclusive.
Snapshot/before result0 is a placeholder, not a native method return.

## Verification

Release Win32 build passed. Hook SHA256:
185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED.
Test-TriggerTrace:519 original calls, x86 AL/arguments forwarding, target filter,
caps/positivecontrol/LastError/faultreads,96prefixmutations; known-target
snapshot and reused/unrelated-parameter exclusion. Local stubs, not live proof.
Verify-Prefixes: old3 and new2 exact48byte PE prefixes pass. Launch VerifyOnly
passes all pinned inputs; no client/server launched. Config-comparison.json:
all29 oldsettings identical, only new collision flag. Server unchanged.
Small current-log preservation tested; full copies<=8MB each, otherwise last
2000lines explicitly marked. No copying old diagnosticlogs or memorydumps.

## Next run gates

Launch D:\SWTORClassic\swtoremu\Run-SWTORClassic-TriggerCollision.cmd.
Load Tython, standstill, no abilities. Before crossing confirm fresh launch,
installed DLLhash, CRT3off, both hook INSTALLED markers, target identity logs,
name/parameter/position interpretation, valid known-target snapshots, no caps.
Confirm sameclientPID/area/roomnames; no mixing secondaryprocess pointers.
If no target identity appears, preserve positive controls/failure and do not
request repetitive doorway attempts. Absence of setters alone is insufficient.
Then one crossing; stopwall/outside, clientopen. Capture fresh acceptedC5,
exact46byte destroy and target collision snapshots around exterior selection.
Preserve small current server/hook/launcher logs before close/restart.

Positive: a same-object identified region remains bit1000/collider40 set across
crossing, with valid local coordinates matching authored region. This supports
persistent region collision, not automatic proof it is the contacted collider.
Alternative: all identified regions have bits cleared and associations absent;
that weakens those regions as wall source. Missing/stale identity, invalid cache,
caps, recycled mismatching objects or absent snapshots are inconclusive.

## Preservation

ToR.before.cpp, MemoryMan.before.dll, RoomSelectionTrace.before.h and
baseline-identity.csv preserve prior room experiment inputs. Prior room header
backup byte identity checked against its old hash. Restore these3 with all
processes closed to revert to experiment08; check baselineidentity afterward.
Old lifecycle/room launch identity pins intentionally unchanged, reject newDLL.
New identity includes both collision headers, room header and launch/preserve
script. Base verbose launcher and reference tree unchanged. No runtimefix yet.
