# Taxi NPC next run: resolve merged-list acceptance, not content

Date: 2026-10-02. Confidence of the *framing and payload*: **Behavior-verified**
(this session, offline). Confidence of the *hypothesis under test*:
**Hypothesis**. One protocol variable.

## What this session changed about the picture

The value-walk blocker is gone (see
`2026-10-02-05-taxi-wire-surface-and-precreate-spec.md` #RESOLVED), which made two
things measurable that were previously not admissible:

1. **Our payload is exact.** `TaxiNpc.bin` reconciles 388/388 with the resolved
   grammar. `taxTerminalSpec` (struct-66 idx 32) sits at body+59 and
   `brkResourceName` (idx 69) at body+354, both authored-exact. So framing,
   field order and field widths are NOT the fault.
2. **Content is not the whole fault either.** Run 9a's clone control delivered a
   byte-for-byte copy of the captured rendering vendor record with only the node
   changed, and it still produced no droid. That removes "taxi content" as the
   sole cause, which is consistent with the taxi's own 2-field surface already
   being authored-exact.

A name-aligned three-way diff (`Compare-NpcRecords.py` /
`npc-record-comparison.txt`) of Weller (the one NPC the client resolves), the
captured vendor (model, no nameplate) and our taxi found no field that
distinguishes a rendering NPC from our record in a way we have not already
tested. The one genuinely un-probed anomaly left in the record is
`spnSpawnedSpec`, below.

## The measurement that is actually missing

`MergedAwarenessAcceptance` (Protocol-Evidence.csv) is still **Hypothesis**: when
our record was appended to the captured set-1 object list, it was never
established whether the captured NPCs survived. That single observation
discriminates two very different worlds:

  * captured NPCs survive -> the list was ACCEPTED and our record is ignored
    in-list -> the problem is our record's lifecycle, not delivery context.
  * captured NPCs vanish -> an appended record causes wholesale rejection
    (matching the reverted earlier merge) -> nothing about content can ever
    work from this delivery shape, and the merge must stay reverted.

Every later content experiment is uninterpretable until this is known, because
both worlds predict "no droid".

## Hypothesis under test

**Appending one record to the captured set-1 object list leaves the rest of the
payload intact** (i.e. the earlier revert was premature, or the cause was the
merge's shape rather than the concept).

Single protocol variable: the object list of `AreaAwarenessEntered` — 77 captured
objects, or 78 with one record appended. Nothing else changes.

**The path is already wired and needs no rebuild.** `AreaStartupBundle.cs:139`
calls `TythonTaxi.MergeNodes()`; when it returns non-null, `AreaMergedAwareness`
is sent *in place of* `AreaAwarenessEntered(set 1)` (line 158), otherwise
`AreaAwarenessEntered(set 1)` is sent untouched (line 164). Construction is
wrapped in try/catch and falls back to the untouched captured set on any
exception (lines 148-157), so this cannot take down area startup.

Enable with one switch on the launcher at the repository root:

    Run-SWTORClassic-Taxi.cmd -CloneControl -TaxiRung 0

`-TaxiRung 0` (default) merges the shipped taxi payload; `-TaxiRung 1` merges
`taxi.record1`, which differs only in `_characterSpecification`.

Omitting `-CloneControl` is the committed baseline: the same taxi record sent as
its own separate packet (`AreaTaxiAwareness`), with set 1 delivered afterwards.

**Precise mechanics** (`AreaMergedAwareness.BuildPayload`):

  * The merged list appends a **five-object** taxi payload, so the one-byte count
    goes **77 -> 82**, not 77 -> 78 (line 152; `RungObjects = {5, 5}`). The
    class's outer docblock still says "77 -> 78" and is stale.
  * Every captured byte is preserved; only the single count byte differs, and
    the code asserts that before sending (lines 157-165).
  * All five identities are substituted through 14 guarded offsets that throw on
    any mismatch (lines 136-148).
  * Construction is wrapped in try/catch; on failure it sends the untouched
    captured set 1 instead (AreaStartupBundle lines 148-157).

No rebuild and no identity repin: nothing in `SharpServer` changed this session,
and the pinned identity manifest does not cover the new diagnostics.

## Deciding observations (record which occur, do not infer)

Read the server log FIRST. Two lines decide the run:

  * `AreaMergedAwareness: MERGED taxi rung=N sha256=... bytes=... captured=...
    count=77->82 npc=0x...; captured payload preserved verbatim.`
    -> the merge WAS emitted. That is the precondition; everything else is
    observation.
  * `AreaStartupBundle: merged taxi construction failed (...); falling back to
    the captured awareness set 1 unchanged.`
    -> the merge did NOT happen. This is a negative for the merge, not for
    content, and the room will otherwise look normal.

POSITIVE-A: the captured medcenter droid, Weller and the authored speeders are
all present and behave as they do today (nameplate on Weller, models on the
speeders). => list accepted.

NEGATIVE-A: any captured NPC is missing, or Weller loses his nameplate.
=> wholesale rejection; keep the merge reverted and stop pursuing content.

POSITIVE-B: the taxi terminal renders a droid. => set-1 delivery, framing and
placement are all proven end to end for the real payload.

NEGATIVE-B: no droid, but POSITIVE-A held. => set 1 is accepted and our record is
created-but-not-rendered; go to room lifecycle / `Replication_Create`.

## Logs to capture

`SharpServer/bin/Debug/NexusToR.log` (fresh node id + object count), the
`TythonTaxi` startup marker, and `Diagnostics/Audit-RequestedAssets.py` output
for both areas: if the client requests the taxi model's asset, the record was
created and rendered-capable; if it requests nothing, creation never happened.
That asset-request delta is the single most informative artifact and it is
free.

## Explicitly NOT part of this run

No field edits, no `spnSpawnedSpec` change, no awareness/CRT re-sends, no
phase-instance gating. `spnSpawnedSpec` (ours `0xE0008B8CC0FAEA1D`, the NPC's own
template; vendor `1`; Weller `2`) is the next candidate AFTER this run resolves,
because it is a field both reference NPCs populate with a small handle and we
populate with a self-reference — but it changes record length, so it must be its
own run.

## Regression gate

`Diagnostics/Test-TaxiValueWalk.ps1` re-walks every generated fixture and fails
unless each record consumes exactly its `inner_size`. Run it before and after any
fixture edit from now on.
