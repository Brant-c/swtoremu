"""Prove the MERGED awareness payload is well-formed: 82 records, exact walk to end.

The run produced all six script errors again, identically, which tells us
_characterSpecification is not the blocker. Before reaching for another field, verify
the one thing that has never been checked offline: that what AreaMergedAwareness
actually EMITS is a valid object list.

Reconstructs the merge exactly as the C# does -- captured set 1 with the count byte
set to 77+5, the five taxi records appended, and all fourteen identity slots
substituted -- then re-parses the whole thing.
"""
import hashlib
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'd7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()

SET1 = ROOT / ('SharpServer/bin/Debug/AreaServer/Awareness/'
               'tython_blockout-4611686019869492753-1.1.aaw')
RUNG = ROOT / 'SharpServer/AreaServer/TaxiRecord1.bin'

SLOTS = [0, 1, 2, 3, 4, 1, 0, 0, 2, 0, 3, 0, 4, 0]
OFFSETS = [6, 109, 115, 121, 127, 486, 502, 531, 538, 554, 584, 600, 630, 646]
RUNTIME = [0x1AC7000001 + i for i in range(5)]


def pack(value):
    n = max(1, (value.bit_length() + 7) // 8)
    out = value.to_bytes(n, 'big')
    if n == 1 and out[0] < 0xC0:
        return out
    return bytes([0xC7 + n]) + out


captured = SET1.read_bytes()
rung = bytearray(RUNG.read_bytes())

# Substitute the fourteen identity slots exactly as AreaMergedAwareness does.
for off, slot in zip(OFFSETS, SLOTS):
    tok = pack(0x1AC7001000 + slot)
    assert rung[off:off + len(tok)] == tok, 'placeholder mismatch at %d' % off
    rep = pack(RUNTIME[slot])
    assert len(rep) == len(tok), 'width mismatch at %d' % off
    rung[off:off + len(rep)] = rep

records = bytes(rung[6:])
assert captured[4] == 0x01 and captured[5] == 77, 'unexpected captured header'
merged = bytearray(captured[:5]) + pack(82) + captured[6:] + records

# 1. Prefix integrity: only the one count byte may differ.
assert merged[:5] == captured[:5], 'HEADER PREFIX ALTERED'
assert merged[6:len(captured)] == captured[6:], 'CAPTURED PAYLOAD ALTERED'
print('prefix integrity: OK (all %d captured bytes preserved verbatim)' % len(captured))

# 2. Full re-parse of the merged list.
rd, _, count = d.read_gom_update(bytes(merged), 0, 'merged')
recs = [d.read_object_record(merged, rd) for _ in range(count)]
exact = rd.pos == len(merged)
print('merged: %d bytes, count=%d (expected 82), walks to end=%s'
      % (len(merged), count, exact))
assert count == 82, 'merged record count is %d, expected 82' % count
assert exact, 'merged payload has trailing slack or a short read'

# 3. The captured 77 must be unmoved; the five taxi objects must be the tail.
for i in range(77):
    src = d.read_object_record(captured, d.Reader(captured, 6)) if False else None
base_rd, _, base_n = d.read_gom_update(captured, 0, 'set1')
base = [d.read_object_record(captured, base_rd) for _ in range(base_n)]
for i, (b, m) in enumerate(zip(base, recs)):
    assert b['node'] == m['node'] and b['structure_id'] == m['structure_id'], \
        'captured record %d moved or changed' % i
print('captured records 0..76 unmoved')
tail = recs[77:]
print('appended records: %s' % [(r['node'], r['structure_id']) for r in tail])
assert tail[0]['node'] == RUNTIME[0], 'taxi NPC node missing from the merged list'
assert tail[0]['structure_id'] == 66, 'taxi NPC must be struct 66'
assert tail[0]['template_id'] == 0xE0008B8CC0FAEA1D, 'taxi template lost in merge'
print('taxi NPC 0x%016X struct=66 template=0x%016X present as record 77'
      % (tail[0]['node'], tail[0]['template_id']))
print('\nMERGE IS WELL-FORMED. sha256 %s'
      % hashlib.sha256(bytes(merged)).hexdigest()[:32])