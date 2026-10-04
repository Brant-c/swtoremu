# Taxi: drop the two authored-absent fields from the wire surface

Date: 2026-10-02. Confidence of the change itself: **Behavior-verified**
offline (the regenerated record still walks to exactly its `inner_size`, and the
byte diff is exactly the two removed fields). Confidence of the hypothesis:
**Hypothesis**. One protocol variable.

## Variable

`chrGender` (struct-66 field 8, `chrNPCGenderComplete=5`) and
`chrAppearanceNppOverride` (field 59, `npcAppearanceOverride=3`) are no longer
replicated.

Both are AUTHORED on `npc.location.tython.taxi.jediretreat_pad1`, but neither is
in that node's replicated surface — which is exactly `taxTerminalSpec` and
`brkResourceName` — and neither appears in any reference NPC record. They were
added by an earlier generator as content guesses. `chrAppearanceNppOverride` is
an *appearance* override, which is the kind of field that would produce the
`not a valid animation agent` / `Mag node doesn't have a valid asset spec` pair.

This makes the record present the **same field set as the captured vendor**, and
`chrAppearanceNppOverride` is the only remaining field ours carries that the
vendor's does not (`chrGender` was the other).

## Why this run and not another content tweak

- Payload framing is settled: the value-walk grammar reconciles and
  `TaxiNpc.bin` walks to exactly `inner_size`.
- Delivery context was tested on 2026-10-02 and changed nothing (merged into
  set 1, `count=77->82`, same six errors, same absence of a droid).
- The clone control (run 9a) already produced a record with the vendor's own
  bytes and still no droid, so "taxi content" alone is not the whole cause.
- Of everything left, this is the one measured difference between a record the
  client processes silently and one that throws six appearance errors.

## Exact change (all offline, no ambiguity)

    SharpServer/AreaServer/TaxiNpc.bin
      before 677 bytes  sha256 78CE8D7A66552C5631DE89489CC753CB2DDF3060F8C4572A8F28BF72DC95023D
      after  675 bytes  sha256 7F98AA2F0CD596D26AC2FC0D45E088D54B57783D62E1F12BD870B9C621405F39
      inner_size 388 -> 386, present fields 31/95 -> 29/95
      identical prefix 69 bytes; the only body difference is the deletion of the
      single byte 0x05 at body+24 (chrGender) and the single byte 0x03 that
      followed chrAppearanceNppOverride. inner_size's own packed field changes
      from c9 01 84 to c9 01 82.

Coupled changes that MUST travel with it, because they are hardcoded guards:

    AreaTaxiAwareness.cs   Offsets  6,109,115,...646 -> 6,108,114,...644
                           FixtureBytes 677 -> 675
    AreaMergedAwareness.cs Offsets  same shift
                           RungBytes { 677, 677 } -> { 675, 677 }
                           (rung 1 is left at its real 677 bytes; its generator is
                            absent from this tree. Rung 1 still works, and a size
                            mismatch throws and falls back to the untouched set.)

Server rebuilt (x86 Debug, `MSBUILD_EXIT=0`), `identity.csv` repinned for
TaxiNpc.bin, Generate-Taxi.py, fixture.json, both .cs files and the rebuilt exe.

Regression gate `Diagnostics/Test-TaxiValueWalk.ps1`: **PASS**, every fixture
record reconciles exactly.

## Run it as the BASELINE delivery

    Run-SWTORClassic-Taxi.cmd

No `-CloneControl`. Delivery context was already shown not to matter, and the
separate-packet path is the one every historical no-op run used, so this is
directly comparable to run 8a/8b and the six-error baseline.

## Deciding observations

Read the LIVE server log (`SharpServer/bin/Debug/NexusToR.log`), never a
`prelaunch-*` copy — those hold the PREVIOUS run.

POSITIVE-A: the six appearance errors (`not a MAG node`, `valid animation
agent`, `Char spec missing`) **drop out** of the log. => the invented appearance
field was poisoning resolution. Look for a model at the pad, then test
right-click -> taxi map.

NEGATIVE-A: the six errors are **unchanged**. => the invented fields were not the
cause; restore `Generate-Taxi.py` from git and pivot to `spnSpawnedSpec`
(ours = the NPC's own template; vendor `1`; Weller `2`), which changes record
length and so needs its own build anyway.

Control-B (must hold in both arms): Weller keeps his nameplate and the
medcenter droid and the speeders are unchanged. If they are NOT, the fixture
edit is implicated in a way the value walk cannot see — report it.

Do not interpret a negative as "content is exonerated": the clone control
already rules out content as the SOLE cause, so a negative here points at
appearance resolution / `spnSpawnedSpec`, not at the taxi prototype.

## Not part of this run

No `spnSpawnedSpec` change, no anchor change, no merge, no phasing change, no
awareness/CRT re-send, no phase-instance gating.
## RESULT — NEGATIVE-A (run 2026-10-04 14:59:41)

Outcome: **the six appearance errors are unchanged, so the two authored-absent
fields were not the cause.** No droid, exactly as before.

Evidence from the LIVE server log (`SharpServer/bin/Debug/NexusToR.log`,
1932 lines, mtime 2026-10-04 15:00:34):

    [14:59:41] AreaTaxiAwareness: fixture sha256=336316F50704B681D838645B3B13EC8E
                79DAEF006340E5829027502741D2B77A bytes=675
                placement=(-53.5,-7.7,-125.5) npc=0x0000001AC7000001 containers=...
    [14:59:41] TythonTaxi: EXPERIMENT taxi NPC=0x0000001AC7000001;
                template=npc.location.tython.taxi.jediretreat_pad1

  * `bytes=675` proves the EDITED fixture shipped (the previous one was 677), so
    this is a real negative and not a stale-payload artefact. The logged hash is
    of the payload AFTER the fourteen identity substitutions, which is why it
    differs from the file's own `7F98AA2F...`.
  * `AreaTaxiAwareness` logged a hash at all, which means `BuildPayload`
    completed: every guarded offset at the new positions (6,108,...,644) matched
    its expected placeholder. The offset edit is therefore validated by the
    server itself, not only by the offline byte diff.
  * No `AreaMergedAwareness: MERGED` line: the baseline separate-packet path ran,
    as instructed.
  * Signature counts are identical to the pre-edit run: `not a MAG node` x6,
    `Mag node` x10, `valid animation agent` x6, `Char spec missing` x2,
    `Unknown spec` x2.

### The more important conclusion this negative delivers

The six errors are a SYMPTOM, not the cause, and that is already provable:
the run-9a clone control delivered the captured rendering vendor record
byte-for-byte and produced ZERO of these errors — and still no droid. Chasing
the error text is therefore low-value; a record that errors nothing and a record
that errors six times both render nothing.

What the clone result plus this negative jointly establish: the client is not
deciding to draw our NPC from anything in our record. It draws the ORIGINAL
vendor droid at the ORIGINAL node, because that one is present in the area's own
spawn data. A record we append, however faithful, is created as an object without
ever being assigned an appearance.