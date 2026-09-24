r'''Cross-reference GOM node ids used by the area startup RPC batches against
the node ids created by the CRT replication fixtures.

A CRT GomUpdate creates nodes; the SMsg23B61238 "On Enter" batch and the
AreaRequestRPC blobs reference nodes. If a referenced node was never created
by any CRT (e.g. the disabled CRT3, stream 0x001B5014), the client's entry
scripts silently fail to resolve and world entry stalls.

  python Diagnostics/Check-GomNodeRefs.py
'''
import re
from pathlib import Path

BIN = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer')


def read_crt(n):
    p = BIN / 'CRT' / ('tython_blockout-4611686019869492753-1.%d.acrt' % n)
    if not p.exists():
        return None
    b = p.read_bytes()
    stream_id = int.from_bytes(b[0:4], 'little')
    return stream_id, b


def packed_u64_values(blob):
    '''All CF-prefixed packed-8 u64s (the common node-id encoding).'''
    vals = []
    i = 0
    while True:
        i = blob.find(b'\xcf', i)
        if i < 0 or i + 9 > len(blob):
            break
        vals.append(int.from_bytes(blob[i + 1:i + 9], 'big'))
        i += 1
    return vals


def u32_candidates(blob):
    return [int.from_bytes(blob[i:i + 4], 'little') for i in range(0, len(blob) - 3)]


# --- CRT fixtures ---
crt_nodes = {}
all_crt_values = set()
present, missing = [], []
for n in list(range(1, 18)):
    fx = read_crt(n)
    if fx is None:
        missing.append(n)
        continue
    sid, body = fx
    present.append((n, sid, len(body)))
    for v in packed_u64_values(body):
        all_crt_values.add(v)
    # also 4-byte LE node-ish values (0x4000xxxx patterns)
    for v in u32_candidates(body):
        if 0x40000000 <= v <= 0x4FFFFFFF:
            all_crt_values.add(v)

print('CRT fixtures present:')
for n, sid, ln in present:
    mark = '' if n != 3 else '   <-- DISABLED in the bundle'
    print('  CRT%-3d stream=0x%08X bytes=%d%s' % (n, sid, ln, mark))
print('missing fixtures:', missing)
print()

# --- SMsg23B61238 payload (captured, from AreaStartupBundle.cs) ---
smsg = bytes.fromhex(
    'CF4312BCBA6B8F69E001'
    'CF4000010E218A839C01'
    'CF4000010E218A839C01'
    'CF4000010E218A839C01'
    'CFE0009EBFFAA2E204'
    '06084F6E20456E746572'
    '020107010000')
smsg_nodes = packed_u64_values(smsg)
print('SMsg23B61238 node references (%d):' % len(smsg_nodes))
for v in smsg_nodes:
    known = v in all_crt_values
    print('  0x%016X  %s' % (v, 'created by a CRT fixture' if known else '*** NOT IN ANY CRT ***'))
print()

# --- AreaRequestRPC blobs from AreaStartupBundle.cs ---
rpcs = [
    'CF2B7E42022E1003' + '0D0600',
    'CF75DCE5C30311A4C8',
    'C74F7741BDE7FF9539' + '02050205',
    'C775A11AAF776506' + '240301',
    'C70C19E0BE7ADB' + '8173',
    'CF65F1369130110385' + '0802020000070200000802040000080206000008020700 00',
    'C707E54B657A208683',
    'C707E54B654836A3C6' + '0801030000',
    'CF057743E1C6B9C0' + '9A0200',
]
print('AreaRequestRPC / SystemRequestRPC first packed values:')
for r in rpcs:
    r = r.replace(' ', '')
    blob = bytes.fromhex(r)
    first = None
    if blob[0] == 0xCF:
        first = int.from_bytes(blob[1:9], 'big')
        kind = 'u64 (CF packed-8)'
    elif blob[0] == 0xC7:
        first = blob[1]
        kind = 'u8 (C7 packed-1)'
    known = first in all_crt_values if isinstance(first, int) else False
    print('  %-16s 0x%016X  %s  %s' % (
        kind, first if isinstance(first, int) else 0,
        'in CRTs' if known else 'not a literal CRT value (may be a function hash)',
        ''))
