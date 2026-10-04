# Schema-matched phase CRT diagnostic candidate

## 2026-09-30 control audit correction

The older "inert unless SWTOR_PHASE_INSTANCE_RETRY" statement below was false
for the pre-control source: `PhaseExit.OnMove` also called `SendRoomStream`,
whose `CRT.Has` lookup accepted this same override CRT18. `CRT.Get` would read
the override before checking the relative installed fixture directory. The
97-byte file still hashes to the documented value below and remains preserved.
It is a generated duplicate-instance probe, not a captured native room stream.
Its actual stream is `0x001B502E`, also used by the doorway destroy; the old
room-stream log advertised `0x001B502F` without rewriting the file's stream.
The control removes that doorway send. The independent retry path remains
opt-in and must be unset for this control. See experiment
`2026-09-30-01-doorway-crt18-suppression-control.md` and
`../DoorwayControl-20260930/README.md`. No native room semantics are promoted.

These files are reconstructed diagnostic fixtures, not captured packets or
production replacements. `SharpServer/bin/Debug/AreaServer/CRT` was not
modified.

## Current arrangement (2026-09-28, "deliver the phase-info child before CRT2")

The local player character is created by **CRT2**, and
`chrCharacter.Replication_Create` fires `OnPlayerCharacterNodeReady` ->
`phsoracle.OnPhasedInstanceUpdated` exactly once. That method returns early when
the player has no `phsPhaseInfo` child, so the child must already exist when
CRT2 is applied. CRT1 is sent before CRT2, so both phase nodes now ride in CRT1.
See `Diagnostics/Phase-Mechanics-20260928.md`.

- CRT1 keeps its header, its original 104 structures, its original phase-instance
  record at index 3, and the remainder of its captured transaction unchanged. It
  appends dependency-first compact structures 105 (`phsActivePhaseInfo`), 106
  (`phsUniqueActivePhaseInfo`) and 107 (`phsPlayerPhaseData`), and inserts the
  captured 48-byte `phsClassPhaseInfo` record at index 4, directly after the
  instance, bumping the object count 53 -> 54.
  Structures 3 (`phsClassPhasedInstance`) and 75 (`phsClassPhaseInfo`) were
  already present in CRT1's captured table, so no structure definition is
  fabricated for this step.
- CRT1's little-endian schema bound at offsets `0x04..0x07` is updated from
  44,001 to 44,207 bytes so the native sub-reader includes the appended
  structures. Omitting this framing update truncates the table at the original
  boundary.
- CRT3 preserves its header, object, 22 value bytes, and `00` state byte. Its
  sole change is offset `0x1E`: compact structure `1` becomes `107` (`0x6B`).
- CRT4 removes the exact 48-byte `phsClassPhaseInfo` child record and changes
  only its object count from 11 to 10.
- CRT11 is **not** overridden any more. `Generate-MatchedPhaseCrtCandidate.py`
  removes a stale CRT11 override from the output directory when it runs,
  because leaving one behind would silently keep a superseded arrangement in
  play.

## What this fixes and what it does not

- Fixes the phase banner and `pc.GetPhasedInstance()`: both now have a
  phase-info child present at the moment `OnPhasedInstanceUpdated` runs, so the
  enter branch executes and `DeterminePhaseEligibility` can reach `phsCanExit`.
- Does **not** fix the doorway on its own. No type-4 `INSTANCE_GATEWAY` trigger
  is replicated, so `_AttachGatewayTrigger` still cannot run. The replicated
  area-object stream contains only Hydra `hydTriggerEntity` triggers
  (`Diagnostics/PhaseExit-Checkpoint-20260928.md`).

## SHA-256

- CRT1: `ADC5A0CB3468D827821EED4D6B9773A83624548F34CFE8E38231BC3371A39B3C`
- CRT3: `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`
- CRT4: `5EEC86299E359D49CDB5572689CB0F446C6EAE7461667F211A86D17DCE7B7A86`
- CRT18 (phase-exit probe):
  `6752695E7BCCA4139D9488E56B35F95D4B37DC0750064B88166B52374CCB9A09`
  - 97 bytes: one `phsClassPhasedInstance` create for the master-retreat
    instance, on node `0x1AC688C981` with stream id `0x001B502E`. Both
    identifiers are *proven* unused across all 20 `.acrt` files by
    `Diagnostics/Generate-PhaseInstanceDuplicate.py`, which refuses to write
    unless both proofs pass — the earlier version asserted them and was wrong
    twice over.
  - Inert unless `SWTOR_PHASE_INSTANCE_RETRY` is set to a number of seconds; see
    the probe block in `Run-SWTORClassic-Trace-Tython.cmd`.

Regenerate with:

```powershell
python Diagnostics/Generate-MatchedPhaseCrtCandidate.py `
  --output-dir Diagnostics\GeneratedPhaseCandidate
```

The client accepted the correctly bounded CRT1/CRT3 pair in earlier controlled
live runs: no serialization error occurred and the world plus quest NPC
rendered. The known-good loading fallback remains enabled.

