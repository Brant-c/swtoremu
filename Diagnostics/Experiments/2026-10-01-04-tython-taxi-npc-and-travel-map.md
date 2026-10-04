# Experiment 2026-10-01-04 - Tython taxi NPC and travel map

## Question
Does the April client render and interact with a fresh schema66 taxi NPC, and does player taxi interaction open a Retreat/Gnarls map?

## Existing evidence
See ../TaxiDevelopment-20261001/AUDIT.md and registry TythonTaxiAwarenessExperiment, AprilTaxiRequestArguments, TaxiPlayerInteractionExperiment. Captured startup has no taxi NPC; existing schema66 supplies its field layout. April scripts connect NPC use to player interaction fields and taxi GUI. Client-derived route data connects Retreat/Gnarls. Generated NPC/map acceptance remains Hypothesis.

## Single runtime variable
Enable SWTOR_TYTHON_TAXI=1, the new session taxi interaction feature. Phase/tether/Weller baseline remains identical. No hook changes or general NPC respawning; flight is not enabled.

## Exact input
- Current build/source/archive/hook/launcher hashes: ../TaxiDevelopment-20261001/identity.csv (nonempty).
- NPC awareness fixture: ../../SharpServer/AreaServer/TaxiNpc.bin, SHA256 37af28109b84d9ad8ebc1753836d9b0db9936390b74735d39387b1dbfa9eddb2, 669 bytes before 8-byte routing header. Earlier values: d1ffa71c... 612 bytes (run 1) and 74a435b6... 669 bytes (run 2).
- Exact area8/19 offline packets: ../TaxiDevelopment-20261001/awareness-8.bin, known-8.bin, clear-8.bin, open-8.bin, and corresponding -19.bin files, pinned in identity.csv.
- Outbound A1D9E226 after captured startup objects, followed by session-known destination update0D446E80.
- Accepted exact one-ID use request triggers None1 then Taxi3 interaction updates0D446E80. Different bounded NPC selectors are logged only.
- Baseline flags: tether refresh, phase reentry, gateway timing, phase clear, Weller conversation/end all1; CRT3=0; retry disabled; trace RPC/full CRT0.

## Predictions
Positive: new droid renders with nameplate and can be clicked; TythonTaxi startup marker has fresh NPC ID. Use request followed by map-interaction marker opens native taxi map; selecting Gnarls yields a complete inbound F96DCDB0 route body with source/destination/Boolean. No travel is expected.
Negative: absent/untargetable NPC, decode failures, or received map-interaction update with no map. A new selector to this NPC identifies the use-request gap but does not establish a valid response.
Inconclusive: wrong launcher/config, prior active process, fixture hash mismatch, missing startup delivery, no client click or unrelated startup failure.

## Evidence to preserve
Server NexusToR.log, existing hook/client logs, operator NPC/map observation. Close after one destination selection; launcher preserves prior logs automatically. No additional observer requested.

## Result
Run 1 (logs in ../TaxiDevelopment-20261001/prelaunch-20261001-130957-581/): NEGATIVE for rendering. Taxis tutorial fired and a minimap marker appeared, but no droid; no click, map or travel. Delivery was confirmed (NexusToR.log 13:06:56, taxi NPC=0x0000001AC7000001) and the client kept polling, so delivery was not the fault.

Diagnosis after run 1: the captured rendering vendor 0x1AC68957EB presents 30 of 96 struct64 fields while the synthesized taxi record presented 18 of 95 and omitted every appearance/identity field (chrTemplateVisualIndex, _characterSpecification, chrClass, cbtFaction, cbtCreatureType, brkResourceName, chrCreatureTypeList, ablContainer, chrLevel). Framing was verified identical to the captured record, so header/envelope/allocation were not at fault.

Run 2 change (one variable): transplanted the vendor's last 57 body bytes verbatim into schema66 slots 62,63,66,68,69,76,77,79,85. Fixture 612 -> 669 bytes; offsets and fixture length updated; identity manifest regenerated.

Run 2 result: NEGATIVE. Still no droid. Operator also reported the client felt slightly laggier (not investigated; 57 bytes cannot plausibly cause that, so treat it as unconfirmed and unrelated).

Diagnosis after run 2: placement was the real defect. Jedipedia node extraction for `npc.location.tython.taxi.jediretreat_pad1` confirmed the template and terminal were already correct, and the area instance dump supplied the authored anchor. The instance coordinate columns are X = col1/10, Z = col2/10, Y = col3/10, pinned by med_poi01_masters_retreat matching the captured vendor to 0.19. The taxi pad spawner row (-535,-1255,-77) is (-53.5,-7.7,-125.5); we had been placing the NPC at (-59.7872,-6.8998,-125.8348), a vendor offset 6.3 units west in X and 0.8 units above the pad level. The minimap marker comes from the mapnote, so it never implied the NPC was there.

Run 3 change (one variable from run 2): placement only, moved to the authored anchor. Fixture stays 669 bytes so the offset table is unchanged; fixture SHA256 is now 37af28109b84d9ad8ebc1753836d9b0db9936390b74735d39387b1dbfa9eddb2. Verify-Taxi.py now pins the anchor so it cannot silently regress.

Run 5 attempt (delivery mechanism) was REVERTED, not adopted. Merging the five taxi records into awareness set 1 - the shared startup stream carrying the captured vendor and the authored speeders - broke previously working content: if the client rejects the appended object list it loses the entire set-1 object set, not just the taxi. That is an unacceptable blast radius for an opt-in experiment and it violated the rule that experimental behavior stays out of the default startup path. The merge was additive-by-packet only in appearance; in blast radius it was destructive. Reverted: AreaAwarenessEntered, AreaStartupBundle, PhaseExit and TythonTaxi are back to their committed behavior, and the taxi ships as its own packet again, which costs nothing but the droid when the client declines it. The merge is retained as a rejected hypothesis with its reasoning, and Verify-AwarenessMerge.py (which proved the merged bytes were well-formed) was removed with it: a well-formed stream is not the same as an accepted one, and keeping the script implied the approach was still live.

Run 5 (authored placement) was negative as well.

Spawn-link probe, run 6: spnSpawnedComponentClassMethods resolves the spawn chain as GetSpawner() -> Me.spnParentAnchorId, then $SPAWNER.GetSpawnerSpecForNode(anchor). spnSpawnerSpec is a script-side cache, not a replicated chrCharacter field, so the anchor is the only replicated handle into that chain. Every captured set-1 NPC that renders carries a distinct spnParentAnchorId; this record carried none. (Correction: struct 62's index 27 is effContainerOther, not the anchor, so Weller is not evidence either way; the evidence is the three struct-42 NPCs plus the struct-64 vendor.) tmrContainer (33) was likewise absent while every rendering shape carried it. Both are now borrowed verbatim from the captured vendor, i.e. values the client already accepts, so the run tests whether the spawn link matters rather than inventing one. This is a probe, not the authored anchor: the taxi pad's own anchor is an opaque hash absent from the GOM name table and not exposed by the Jedipedia node reader, which publishes only hyd/mpn/npc categories.

Also established, and deliberately NOT treated as the fix: spnSpawnedAppearanceClassMethods drives appearance from spnSpawnedEntryAppearance inside a Replication_Create handler via abl.utility.apply_appearance. None of the six captured rendering NPCs carry spnSpawnedEntryAppearance, so creatures do not resolve their model through that path.

Offline build and taxi checks pass: Test-Taxi.ps1, Verify-Taxi.py (areas 8/19, now asserting fields 27/33 and the 684-byte length) and the new Verify-TaxiFixture.py, which runs against TaxiNpc.bin without the assembly. All 38 baseline bodies and 54 transport fixtures pass; routing, blob-framing, wire round trip and PacketWorkbench pass. The captured .aaw/.acrt fixtures remain byte-identical and dated 2026-09-10, and only taxi-specific pinned inputs changed, confirming the blast radius stayed inside the experiment. WorldEntryOffline retains the prior missing RequestWorldFadeIn observer source-check failure; no hook was changed.

Run 7 change (delivery ORDER only, additive): the taxi awareness packet now precedes awareness set 1 instead of trailing the bundle. Nothing else changed: same fixture, no captured payload modified, no merge. The ordering makes the failure mode asymmetric -- if the client treats each A1D9E226 as "replace the awareness list", set 1 supersedes our five objects and the result is "no droid", whereas sending after set 1 would have superseded the 77 captured objects, which is how the reverted merge broke the working NPCs. This is the first test of WHEN the packet lands; every prior negative came from record content, and the record is now field-equivalent to Weller.

Key finding that redirected the investigation: the operator reports the captured struct-64 record at (-59.79,-6.90,-128.33) renders a model but has no nameplate and is not interactable, and that position is med_poi01_masters_retreat_medic_droid.spn_c -- it is the medcenter droid, not a vendor. So it was never a working reference; Weller (0x1AC6F6DC6D, struct 62) is the only confirmed working NPC. Compared by field definition id, the taxi record shares 27 fields with Weller and lacks only staEnterIdle, effContainerEffectlessTags and cnvAlienConversationsRequiredLookup; parent (0x1AC688BE1E) and class (0x0) match all six captured NPCs.

## Conclusion
Pending operator run 7. If the droid appears, delivery order was the missing variable. If not, timing is ruled out and only two remain: template resolution, and whether the client will instantiate from any non-initial payload at all -- which the medcenter droid makes more plausible, since it is captured and in the initial payload yet still has no nameplate, unlike Weller. Two candidate explanations remain open and are not separable from the captures alone: whether an awareness record is sufficient to create a model, or whether the client only models objects its own spawner/appearance entry produced. No captured example exists of an object being added to a live area. behavior stays opt-in. Next work: confirmed use/route decoder, authored path extraction and vehicle/arrival lifecycle; no invented teleport destination.
## Run 9 results (2026-10-01 23:13 and 23:28) — clone control and single-list merge

### Run 9a (23:13) — clone control, sent as a separate packet

Variable: instead of the generated taxi, send a byte-for-byte copy of the captured
medcenter droid record (`TaxiClone.bin`, 478 B) with only the node identity changed,
delivered at the same position in the startup bundle as the taxi.

```
[23:13:58] AreaTaxiCloneAwareness: CONTROL clone of captured medcenter droid
           sha256=401EB3E0... bytes=478 npc=0x1AC7000001
script errors: 0        (taxi mode: 6)
```

**POSITIVE and decisive.** The three errors -- `Char spec missing: Unknown spec(0)`,
`Mag node doesn't have a valid asset spec`, `Node is not a MAG node or does not have a
valid animation agent` -- are produced by the *taxi's content*, not by our assembly,
framing or delivery. A record built by our generator, at our delivery position, was
accepted with zero failures. The taxi tutorial prompt also disappeared, corroborating
that the medcenter template was used instead.

Two independent problems are now established:

1. **Content** -- the taxi's `taxTerminalComponent` path fails. Clone proves it is
   content-specific.
2. **Ordering** -- the clone still did not appear, and the run log shows set 1 is sent
   AFTER our packet (idx 1022 ours, idx 1062 set 1), with the client never referencing
   our node afterwards. That is the replacement-semantics signature.

This explains why runs 8a/8b were uninterpretable and why three content experiments
produced byte-identical results.

*Design flaw, recorded honestly:* the clone kept the captured medcenter droid's exact
position, so even a successful render would have been stacked invisibly on the existing
droid. The zero-error result rescued the test's value, but visibility could not have
been confirmed visually.

### Run 9b (23:28) — clone merged into awareness set 1 as ONE object list

Variable: `AreaMergedAwareness` appends the clone record to captured awareness set 1
in memory and sends a single object list, so nothing is superseded.

```
[23:28:43] AreaMergedAwareness: MERGED single object list sha256=09333AF6...
           bytes=13960 captured=13488 count=77->78 npc=0x1AC7000001;
           captured payload preserved verbatim
script errors: 0
client references to our node: 0
```

Offline verification (`Verify-SingleListMerge.py`) established the properties whose
violation would break the working NPCs, before any code shipped:

- append-only; the captured 13488 bytes are preserved verbatim
- count byte 77 -> 78, one-byte packed encoding retained (width recovered by probing
  the decoder, not assumed)
- merged list re-parses to exactly 78 records, walking to its own end
- captured records 0..76 unmoved; the clone lands last

A likely culprit for the earlier reverted merge was checked and **cleared**: the
clone's parent `0x1AC688BE1E` is absent from set 1, but the *captured* medcenter droid
carries the same dangling parent and the client already accepts it.

### Conclusion

Zero script errors in both control runs, versus six in taxi mode, is
**Behavior-verified**: our synthesis, framing and delivery path are sound, and the
taxi failures are content-specific. That is the first positive result of the taxi
investigation.

The clone still did not render, so problem 2 is not yet closed either. Run 9b removes
the ordering variable entirely -- our record now travels inside the same packet as the
77 captured objects -- yet the node is still never referenced. Two readings remain,
and they are separated by whether the captured NPCs survived the merged list:

- **captured NPCs intact** -> the merged list was accepted; the clone record itself is
  being ignored even in-list, which would point at record-level acceptance rather than
  delivery or ordering.
- **captured NPCs gone** -> the appended record causes the client to reject the whole
  list, which matches the reverted merge and requires the client's rejection reason
  rather than further inference.

**OPEN: the operator has reported only that the taxi droid did not appear. Whether the
medcenter droid, Weller and the other working NPCs survived run 9b has not been
stated, and it is the discriminating observation.** Per the evidence policy this is
recorded as Behavior-verified for the zero-error content finding and **Hypothesis**
for the merge-acceptance question until the NPC-survival observation is supplied.
## Run 8 results (2026-10-01 21:48 and 22:03) — two behavior-verified negatives

Both runs produced **byte-identical** script-error traces, including line numbers,
which means neither changed value was reached by the failing code path.

### Run 8a (21:48) — taxi `_characterSpecification` self-reference

Variable: struct-64 field 78 / struct-66 field 77 `_characterSpecification`
`0x5541E56931B58335` (donor capture-time hash) -> `0xE0008B8CC0FAEA1D` (taxi
prototype's own spec). Also in this build: `spnParentAnchorId` (field 27) removed,
`brkResourceName` set to the taxi's own. Fixture 677 B,
sha256 `4c6fafb15292f748767998d2a50407b9048ee0c75a8a0d517b85bf834cf56b14`.

Result: `Char spec missing: Unknown spec(0)` unchanged. **Rejected.**

### Run 8b (22:03) — `staEnterIdle` set in the awareness record

Variable: `staEnterIdle` (struct-66 field 37) marked present. Evidence for the
choice: it is a Boolean (part kind 3) consuming ZERO value bytes, so presence *is*
the value; Weller (the only confirmed working NPC) has it present; and CRT12, the
only NPC replication contract in the whole capture, transmits exactly that field.
It was the only field the taxi lacked that Weller carries.

Fixture 677 B, sha256 `78ce8d7a66552c5631de89489cc753cb2ddf3060f8c4572a8f28bf72dc95023d`.
Record length and every patch offset unchanged; exactly one presence bit differs
(30 -> 31 fields transmitted).

Result: identical traces. **Rejected** — and since the traces are identical, the
field was never read on the path that fails.

### Fixture delivery was verified, not assumed

`Diagnostics/TaxiDevelopment-20261001/Verify-RunFixture.py` replays the runtime
node substitution performed by `AreaTaxiAwareness.BuildPayload()` and compares
against the hash in the run log. The logged `F7BF90DA...` can never equal the
file's `78CE8D7A...` because the log hashes the *substituted* payload. Replay
matches exactly, so both runs provably carried the intended fixture.

### New positive finding: class resolution is correct

The client error trace prints the class chain it assigned to taxi node
`0x1AC7000001`:

| class id | name |
|---|---|
| 4611686018435310013 | `chrNonPlayerCharacter` |
| 4611686018455170113 | `aiCharacterAgentOverrideComponent` |
| 4611686018456770059 | `spnSpawnedComponent` |
| 4611686019631751166 | `brkOwnerComponent` |
| 4611686035046870024 | **`taxTerminalComponent`** |

This is exactly `struct 66`'s `additional_classes`. Template
`0xE0008B8CC0FAEA1D` and structure selection are therefore correct, which removes
the whole "wrong template / wrong class / wrong structure" family and means a
wholesale captured-record clone is not required for class reasons.

### New finding: awareness ordering suppresses the taxi

Server log ordering for run 8b:

```
1004  taxi awareness logged
1005  AreaAwarenessEntered        <- our 5 objects
1006  AreaClientReplicationTransaction (CRT 13)
1008  AreaAwarenessEntered        <- awareness set 1, the 77 captured objects
```

Awareness set 1 arrives **after** the taxi. Under the replacement-semantics
hypothesis recorded for run 7, set 1 supersedes our five objects, so "no droid" is
the predicted outcome irrespective of record content. The script errors are
timestamped 22:03:43, i.e. the model-build failure occurs at object creation,
*before* set 1 lands — so the taxi fails twice over: the model never builds, and the
object may then be replaced.

### Caution: this run is not a clean captured baseline

`CRT.cs:24` honours `SWTOR_CRT_OVERRIDE_DIRECTORY`, which is set to
`Diagnostics/GeneratedPhaseCandidate`. During run 8 that replaced:

```
CRT 1: 57382 -> 57636 bytes  (sha256 adc5a0cb...)
CRT 4:  1833 ->  1785 bytes  (sha256 5eec8629...)
```

These are the phase-exit candidates, not captured bytes. The override is
intentional and env-gated, but a taxi failure cannot be attributed to the taxi
alone while it is active.

### Method-body availability

Script ids in the runtime traces were resolved via `_JPEXTRACT/Scriptdef.listdump.csv`:
`14988232461720378822` = `chrCharacterClassMethods` (errors at 334/396/438/855/919),
`14988218315743018005` = `chrAnimClassMethods` (21/26/83),
`14988160216094350333` = `staCharacterComponentClassMethods`,
`14988110172442017861` = `chrNonPlayerCharacterClassMethods`.

`_JPEXTRACT/chranimclassmethods.txt` and `chrCharacter.txt` are **decompiled
listings, not method bodies**, and their line numbering does not correspond to the
runtime trace: line 83 of `chranimclassmethods.txt` is `if Me._chrAnim_NewCpids()`,
not an error raise. The failing checks cannot currently be read directly.

### Remaining structural difference (untested)

The captured medcenter droid, which *does* render a model (it lacks only a nameplate
and targetability), is **struct 64**. Its `additional_classes` are identical to
struct 66 except for the fourth:

```
struct 64  ... brkOwnerComponent, vndVendorComponent    <- renders a model
struct 66  ... brkOwnerComponent, taxTerminalComponent   <- renders nothing
```

`Generate-Taxi.py:172` writes `additional_classes` explicitly, so this is our
choice, not the template's. Untested, and currently confounded by the awareness
ordering above.

### Conclusion

Two field-level hypotheses are rejected with byte-identical negatives. Field
guessing on this record has produced three consecutive no-ops (`brkResourceName`,
`_characterSpecification`, `staEnterIdle`) and should stop. The two live variables
are now structural — struct 64 + `vndVendorComponent` versus struct 66 +
`taxTerminalComponent` — and delivery ordering. They must be **decoupled** before
another client run, because the current ordering makes a correct record
indistinguishable from a wrong one.