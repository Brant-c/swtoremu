# Experiment 2026-09-30-04 — Read-only gnarls native identity mapping

## Question

During stable Tython startup, where do the April client representations of awareness node 0x1AC6F6DC94 and gnarls_new reside, and do the objects selected at area+0x2A0 or area+0x400 contain or directly reference either identity?

## Existing evidence

Experiment 03 established that the existing startup `AreaAwarenessEntered`
payload contains `gnarls_new` in dynPlaceable node `0x1AC6F6DC94`. It also
established stable client-selected pointers `0xD2C14500` and `0xD2C15500` in
that process, both state/aux `3/6`, with no identity or state change across the
doorway destroy. The addresses are process-specific and cannot be reused.

It is established that `gnarls_new` is present in startup wire data. It remains
a hypothesis that either selected native object represents that room, refers to
its awareness object, or owns the blocking doorway collision.

## Single variable

Add one external, one-time read-only identity scan after stable Tython startup.
It will search readable committed client memory for the exact 64-bit node ID,
its six-byte packed representation and ASCII `gnarls_new`, then inspect bounded
memory surrounding the current `area+0x2A0` and `area+0x400` objects for those
values or direct pointers to the matches. It must use query/read process rights
only. No crossing, process write, hook change, packet or environment change.

## Exact input

- Pinned scanner/control identity:
  `../DoorwayControl-20260930/gnarls-native-map/identity.csv`, 53 files,
  manifest SHA256
  `DF12846CC0FBD405A5A14C788D03B16DE503C4700A5EBE7A7F819ADC1F209AB2`.
- Scanner SHA256:
  `12873D3256E44775DC4D850AA13CA9E2E31CF2974F824BAAE62FF1A71B8DD29B`.
- Capture-producing marker repair SHA256:
  `F9030C8A5606EFF4E3893CF3C537A641002922669605F8AC7599C1EA70F473B7`.
- Final scanner, including the manifest repair, SHA256:
  `5DCAA09B3CE2FEF8EB4BA380879A1C65A4B19E711BA69D2F71EDC6FD2D336754`.
- The original launch identity is preserved as `identity-at-launch.csv`; the
  repaired current 54-file identity has SHA256
  `08CAA5B6B0B9CADBB3C9994E51B277E81752006E01A675D9686D95CB033823EC`.
- Environment switches: unchanged frozen experiment-01 baseline; actual values
  preserved at launch. No ability input.
- Existing S2C startup `AreaAwarenessEntered`; no new packet is sent.
- Captured fixture:
  `SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.2.aaw`,
  SHA256 `8B888EDC0823F5A3E8E3FD19DBB43AA121A6C26964193101E32B25B3F33DFB73`.
- Search identities: node `0x0000001AC6F6DC94`, packed bytes
  `CC 1A C6 F6 DC 94`, and ASCII bytes for `gnarls_new`.

## Predictions

Positive observation:

- A bounded selected-object region contains the exact node identity, the room
  string, or a direct pointer to a process-memory match. Record addresses,
  representation and offsets so the relationship is reproducible under ASLR.

Negative observation:

- The scan finds the identities elsewhere but neither selected object contains
  or directly references them. This falsifies only the direct-relationship
  hypothesis, not an indirect graph relationship.

Invalid/inconclusive conditions:

- Startup fixture/hash differs, `gnarls_new` is absent from the actual emitted
  awareness payload, area or selected pointers are null, memory-region metadata
  is not preserved, reads are unbounded, or the observer requests write access.

## Evidence to preserve

- Exact startup server and hook logs plus effective switches.
- Scan script, identity manifest, process/module addresses, virtual-memory
  regions and all match addresses/offsets.
- Offline awareness inventory tying `gnarls_new` to node `0x1AC6F6DC94`.
- No screenshot is required unless startup behavior differs.

## Result

Live run occurred 2026-09-30. The operator entered Tython and remained
stationary in the Masters' Retreat through the 00:41:45 capture. The automatic
initial C5 position report at 00:39:36 is not operator movement. The operator's
only movement and doorway attempt began at 00:42:58, more than a minute after
the snapshot, and is excluded from this experiment.

The pinned-at-launch scanner waited incorrectly for literal `gnarls_new` in the
server text log; AREA payloads log the bytes as hyphenated hex. That invocation
performed no memory capture. Its source, empty logs and identity manifest are
preserved. The only repair changed the marker predicate to exact bytes
`67-6E-61-72-6C-73-5F-6E-65-77`; no client, hook, packet or environment
behavior changed. The corrected scan completed. Its final manifest pipeline
then tried to hash `manifest.csv` while writing it and exited with an error
after all substantive evidence files were already closed. The manifest was
regenerated offline excluding itself; the final script includes that repair.

At 00:41:45 the read-only scan captured PID 2860, module base `0x006E0000`,
area `0xF41D39A0`, primary `0xD2D94000` and secondary `0xD2D95000`; both
selected objects were state 3. It found seven exact identity matches: one
packed node record, five ASCII `gnarls_new` strings, and one little-endian
64-bit node ID at `0x1076E318`.

The little-endian match has an object-shaped prefix beginning 24 bytes earlier:
candidate vtable `0x01405ECC`, object base `0x1076E300`, node ID at `+0x18`.
Offline PE32 RTTI resolution maps that vtable to `.?AVHeroNode@@`. Thus the
matched allocation is a generic native HeroNode for the replicated GOM node,
not evidence of a native room object.

Neither selected 4096-byte object region contains the node ID, packed ID or
room string, or points directly to any exact match. A second offline check also
found no pointer to inferred HeroNode base `0x1076E300`. The direct relationship
hypothesis is falsified within the bounded regions; indirect ownership remains
unresolved.

The captured record is class `dynPlaceable` and also names the Republic
dropship asset `mag_repdropship_ship`. `gnarls_new` is therefore a room
assignment inside a placeable record, not the identity of a room node. It still
establishes that at least one object assigned to `gnarls_new` was sent at
startup.

Evidence is under
`../DoorwayControl-20260930/gnarls-native-map/capture-corrected/`.

## Conclusion

- Outcome: direct selected-object relationship falsified; generic HeroNode and
  placeable-room assignment identified; indirect ownership unresolved
- Confidence change: none; no protocol lifecycle interpretation promoted
- Registry rows updated: none
- Runtime code retained: unchanged frozen control; observer is external and
  read-only
- Next single question: are the captured `INSTANCE_GATEWAY` and
  `INSTANCE_REGION` engine triggers materialized in the client trigger registry
  after startup, independently of GOM awareness replay?

