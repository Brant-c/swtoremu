# Read-only gnarls native identity mapping — 2026-09-30

## Controlled timing

The operator remained stationary in the Masters' Retreat through the snapshot
at 00:41:45 Toronto. The only intentional movement began at 00:42:58 and crossed
the server's X=-63 detector at 00:43:03. That later movement and phase-info
destroy are excluded from this mapping result.

The initial scanner waited on the wrong textual marker and captured no memory.
The corrected invocation changed only that predicate from literal text to the
exact hyphenated ASCII bytes present in the AREA payload log. Its evidence files
were complete before a separate manifest self-hashing error. The manifest was
regenerated offline excluding itself. All versions and error logs are preserved
beside this capture.

## Snapshot identity

- Captured: `2026-09-30T00:41:45.2359734-04:00`.
- Process: PID 2860, module base `0x006E0000`.
- Area root: `0xF41D39A0`.
- Primary selection: `0xD2D94000`, state 3.
- Secondary selection: `0xD2D95000`, state 3.
- Process access: `0x410` query/read only.
- Search identities: little-endian node `94 DC F6 C6 1A 00 00 00`, packed node
  `CC 1A C6 F6 DC 94`, and ASCII `gnarls_new`.

## Matches

The scan found seven exact matches:

- Packed node record at `0x04B922BF`.
- ASCII strings at `0x04B8F933`, `0x04B8FA0C`, `0x04B9230A`, `0x0A5395AC`
  and `0x0A539685`.
- Little-endian node ID at `0x1076E318`.

The little-endian match begins at offset `+0x18` from an inferred object base
`0x1076E300`. The first dword at that base is runtime vtable `0x01405ECC`.
Resolving its ASLR-adjusted PE32 RVA through Microsoft RTTI gives type name
`.?AVHeroNode@@`. This identifies a generic native GOM node allocation. It does
not identify a room-stream object.

Neither selected 4096-byte object snapshot contains an exact identity or a
pointer to an exact match. An additional offline scan found no pointer to the
inferred HeroNode base either. `selected-links.csv` and
`selected-inferred-base-links.csv` preserve these negative results.

The corresponding awareness record is a `dynPlaceable` containing the dropship
asset `mag_repdropship_ship` and `gnarls_new`. The room string is a placeable
assignment, so node `0x1AC6F6DC94` must not be treated as the room itself.

## Conclusion

The client has replicated objects assigned to `gnarls_new`, but neither
selected native object directly contains or references this placeable HeroNode
within the tested bounds. This weakens missing basic asset streaming as the
doorway blocker and removes node `0x1AC6F6DC94` as a room-object candidate.

The next evidence target is the engine trigger registry: determine whether the
known `INSTANCE_GATEWAY` at `(-63.6168,-6.7343,-126.8847)` and its associated
`INSTANCE_REGION` volumes exist as native `TriggerInstance` objects after
startup. That question directly tests the established phase-script prerequisite
without introducing a packet hypothesis.
