"""Prove each ladder rung differs from rung 0 by exactly its intended change.

Rung 0 must be the CAPTURED medcenter droid record with only the node identity and
the X position offset applied. If anything else differs, the baseline is not the
known-good record the whole ladder rests on.

Then each rung N is diffed against rung 0 so the byte-level delta is exactly the one
field it claims to introduce -- no incidental drift.
"""
import importlib.util
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location(
    'd7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

OUT = ROOT / 'SharpServer/AreaServer'
SET1 = ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw'
DONOR_NODE = 0x1AC68957EB
manifest = json.loads((HERE / 'ladder.json').read_text())


def record_span(data, path_is_bin):
    if path_is_bin:
        rd = d.Reader(data, 6)
        n = 1
    else:
        rd, _, n = d.read_gom_update(data, 0, path.name)
    recs = [d.read_object_record(data, rd) for _ in range(n)]
    stop = recs[0]['start'] + _span(data, recs[0], path_is_bin)
    return recs[0], stop


def _span(data, rec, path_is_bin):
    if path_is_bin:
        return len(data) - 6 - rec['start']
    return None


def load_donor():
    data = SET1.read_bytes()
    rd, _, n = d.read_gom_update(data, 0, 'set1')
    recs = [d.read_object_record(data, rd) for _ in range(n)]
    i = next(k for k, r in enumerate(recs) if r['node'] == DONOR_NODE)
    stop = recs[i + 1]['start'] if i + 1 < len(recs) else len(data)
    return data[recs[i]['start']:stop], recs[i]


donor_raw, donor = load_donor()
r0 = (OUT / 'TaxiLadder0.bin').read_bytes()[6:]

# Field 0 (character_position) is the first value in the body.
pos_off = donor['body_start'] - donor['start']
node_len = 6
print('donor record %d bytes; rung0 record %d bytes' % (len(donor_raw), len(r0)))
assert len(donor_raw) == len(r0), 'rung0 record length drifted'

# The node token differs by design. Everything from the end of the node onward must
# match except the 12 position bytes.
diff = [k for k in range(node_len, len(donor_raw)) if donor_raw[k] != r0[k]]
lo, hi = pos_off, pos_off + 12
unexpected = [k for k in diff if not (lo <= k < hi)]
print('node  donor=0x%016X  rung0=0x%016X  (expected to differ)'
      % (DONOR_NODE, 0x1AC7001000))
print('position bytes %d..%d' % (lo, hi))
print('  donor %s' % [round(v, 2) for v in struct.unpack_from('<3f', donor_raw, pos_off)])
print('  rung0 %s' % [round(v, 2) for v in struct.unpack_from('<3f', r0, pos_off)])
print('differing bytes: %d total, %d outside the position field'
      % (len(diff), len(unexpected)))
if unexpected:
    print('  UNEXPECTED at', unexpected[:20])
    for k in unexpected[:6]:
        print('   %4d donor=%02x rung0=%02x' % (k, donor_raw[k], r0[k]))
    raise SystemExit('rung0 is NOT a clean splice of the captured record')
print('rung0 = captured record, byte-identical apart from node + position  OK')

print()
# Diff every rung against rung 0, not against its predecessor: the position offset
# is recomputed from the captured floats each time, so tiny representation drift
# would otherwise show up as scattered bytes on later rungs.
base = r0
for row in manifest[1:]:
    cur = (OUT / row['file']).read_bytes()[6:]
    d = [k for k in range(min(len(base), len(cur))) if base[k] != cur[k]]
    lo, hi = pos_off, pos_off + 12
    outside = [k for k in d if not (lo <= k < hi)]
    # A rung may introduce more than one token, so contiguity is only required when a
    # single field was introduced. Rung 3 (both) is expected to change two windows.
    windows = []
    for k in outside:
        if not windows or k > windows[-1][1] + 1:
            windows.append([k, k])
        else:
            windows[-1][1] = k
    expect = len(row['introduced'])
    ok = len(windows) == expect and all(b - a + 1 <= 9 for a, b in windows)
    print('rung %d  %-46s %d token window(s): %s%s'
          % (row['rung'], row['label'], len(windows),
             ', '.join('%d..%d' % (a, b) for a, b in windows),
             '  OK' if ok else '  UNEXPECTED'))
    if not ok:
        raise SystemExit('rung %d changed %d window(s), expected %d'
                         % (row['rung'], len(windows), expect))
print('\nEach rung is one client run. Rung 0 first: if it renders, transport, framing')
print('and placement are proven, and rungs 1-3 then name the offending token.')