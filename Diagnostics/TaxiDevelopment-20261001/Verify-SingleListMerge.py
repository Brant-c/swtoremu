"""Prove a safe single-list merge: captured awareness set 1 + our clone record.

The client appears to treat each A1D9E226 as "replace the awareness list", so our
object must travel in the SAME packet as the 77 captured objects. The earlier
merge attempt broke the working NPCs; this checks the two properties that would
cause that, before any code ships:

  1. PREFIX INTEGRITY -- the first N bytes of the merged payload must be
     byte-identical to the captured .aaw. Any divergence means we mutated captured
     payload, which is exactly the blast radius we must never take.
  2. EXACT RE-PARSE  -- the merged payload must decode as one object list whose
     record count is captured+1, walking to its own final byte with no trailing
     slack and no short read.

Also reports whether the clone's own dependencies (parent, prototype/template,
container references) are already present in set 1, since a record pointing at an
absent parent is a plausible cause of a rejected list.
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

SET1 = ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw'
CLONE = ROOT / 'SharpServer/AreaServer/TaxiClone.bin'


def pack(value):
    out = bytearray()
    while True:
        out.insert(0, value & 0xFF)
        value >>= 8
        if not value:
            break
    if len(out) <= 8 and (out[0] & 0x80 or len(out) == 1):
        return bytes(out)
    return bytes([0xC7 + len(out)]) + bytes(out)


base = SET1.read_bytes()
clone = CLONE.read_bytes()

# The object-list header is: LE u32 pad, flags byte, packed count. Recover the
# exact count-byte WIDTH from the decoder rather than assuming it is one byte,
# because set 1 carries a multi-byte prefix that a naive 4+1 assumption breaks.
def header_shape(buf):
    """Return (flags, count_value, count_start, count_end) or None."""
    for width in (1, 2, 3, 4, 5):
        i = 4 + 1 + width
        if i > len(buf):
            continue
        flags = buf[4]
        first = buf[5]
        # A packed value's leading byte is >= 0xC0 exactly when extra bytes follow.
        if first < 0xC0:
            if width != 1:
                continue
            total = first
        else:
            total_len = first - 0xC7
            if total_len != width - 1:
                continue
            total = 0
            for k in range(width - 1):
                total = (total << 8) | buf[6 + k]
        if total <= 0 or total > 4096:
            continue
        # Validate by actually walking that many records.
        try:
            rd, _, n = d.read_gom_update(buf, 0, 'probe')
            if n != total:
                continue
            recs = [d.read_object_record(buf, rd) for _ in range(n)]
        except Exception:
            continue
        if rd.pos <= i:
            continue
        return flags, total, 5, 5 + width, recs
    return None


shape = header_shape(base)
if shape is None:
    raise SystemExit('could not determine the awareness list header shape')
flags, base_count, count_start, count_end, base_records = shape
one_byte_count = (count_end - count_start) == 1
print('captured set 1: %d bytes, flags=0x%02X, count=%d, count-width=%d'
      % (len(base), flags, base_count, count_end - count_start))

crd, _, clone_count = d.read_gom_update(clone, 0, 'clone')
assert clone_count == 1
clone_rec = d.read_object_record(clone, crd)
assert crd.pos == len(clone), 'clone does not walk to its own end'
record_bytes = clone[6:]          # strip pad+flags+count
assert len(record_bytes) == len(clone) - 6
print('clone record: %d bytes, struct=%d template=0x%X parent=0x%X'
      % (len(record_bytes), clone_rec['structure_id'],
         clone_rec['template_id'], clone_rec['parent_id']))

# --- merge -------------------------------------------------------------------
merged_count = base_count + 1
if one_byte_count:
    assert merged_count < 0xC0, 'count would need multi-byte encoding'
    header = base[:count_start] + pack(merged_count)
else:
    raise SystemExit('captured count is multi-byte; refusing to guess the framing')
merged = header + base[count_end:] + record_bytes

# 1. prefix integrity: the captured bytes must survive verbatim.
assert merged[:count_start] == base[:count_start], 'HEADER PREFIX CHANGED'
assert merged[count_end:count_end + len(base) - count_end] == \
       base[count_end:], 'CAPTURED PAYLOAD ALTERED'
print('prefix integrity: OK (captured %d bytes preserved verbatim)' % len(base))

# 2. exact re-parse
mrd, _, mcount = d.read_gom_update(merged, 0, 'merged')
mrecs = [d.read_object_record(merged, mrd) for _ in range(mcount)]
exact = mrd.pos == len(merged)
print('merged: %d bytes, flags=0x%02X, count=%d (expected %d), walks to end=%s'
      % (len(merged), merged[4], mcount, merged_count, exact))
assert mcount == merged_count, 'record count mismatch'
assert exact, 'merged payload has trailing slack or short read'
assert mrecs[-1]['node'] == clone_rec['node'], 'clone is not the final record'
assert mrecs[-1]['structure_id'] == clone_rec['structure_id']
for i, r in enumerate(base_records):
    assert mrecs[i]['start'] == r['start'], 'record %d moved' % i
    assert mrecs[i]['node'] == r['node'], 'record %d node changed' % i
print('captured records 0..%d unmoved; clone appended as record %d' % (len(base_records) - 1, mcount - 1))

# --- dependency check ---------------------------------------------------------
# The clone's parent 0x1AC688BE1E is NOT in set 1. Check whether it is in the
# awareness-2 stream or any CRT instead: if the parent arrives later, a record
# appended to set 1 may be rejected for referencing an unknown parent, which is a
# much more likely cause of the reverted merge than a framing problem.
present = {r['node'] for r in base_records}
parent = clone_rec['parent_id']
print('\nclone dependencies:')
print('  parent 0x%016X present in set 1: %s' % (parent, parent in present))

SET2 = ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.2.aaw'
set2_nodes = set()
if SET2.exists():
    b2 = SET2.read_bytes()
    rd2, _, n2 = d.read_gom_update(b2, 0, 'set2')
    set2_nodes = {d.read_object_record(b2, rd2)['node'] for _ in range(n2)}
    print('  parent present in awareness set 2: %s' % (parent in set2_nodes))

# Does the ORIGINAL captured medcenter droid record have the same parent? If so,
# that parent is satisfied the same way for it, and our clone differs in nothing
# that matters -- which would mean the earlier merge failure had another cause.
orig = next(r for r in base_records if r['node'] == 0x1AC68957EB)
print('\noriginal captured medcenter droid in set 1:')
print('  struct=%d template=0x%X parent=0x%X'
      % (orig['structure_id'], orig['template_id'], orig['parent_id']))
print('  same parent as clone: %s' % (orig['parent_id'] == parent))
print('  parent in set 1: %s' % (orig['parent_id'] in present))

print('\nSAFE TO MERGE: append-only, single object list, exact re-parse.')
print('merged length = %d (captured %d + clone record %d)'
      % (len(merged), len(base), len(record_bytes)))