"""Survey every captured tython CRT for *contracts* (per-object replication
updates), separating them from schema tables.

A CRT opens with a schema table; only after that does the contract stream begin.
A node whose bytes appear inside the schema table is NOT evidence of a contract.
This distinguishes "referenced by a schema" from "actually updated by replication",
which is the distinction the taxi needs.
"""
import re
import struct
from pathlib import Path

CRT = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')

NPC_NODES = {
    0x1AC6F6DC6D: 'Weller  (struct 62) - the only working NPC',
    0x1AC68957EB: 'vendor / medcenter droid (struct 64) - NOT working',
    0x1AC689748C: 'struct-42 NPC - NOT working',
    0x1AC689385F: 'struct-42 NPC - NOT working',
}


def packed(buf, i):
    b = buf[i]
    if b < 0xC0:
        return b, i + 1
    ln = b - 0xC7
    v = 0
    for k in range(ln):
        v = (v << 8) | buf[i + 1 + k]
    return v, i + 1 + ln


def tokens(node):
    out = bytearray()
    v = node
    while True:
        out.insert(0, v & 0xFF)
        v >>= 8
        if not v:
            break
    return bytes([0xC7 + len(out)]) + bytes(out), node.to_bytes(8, 'little')


print(f"{'CRT':>5}  {'bytes':>7}  {'schema':>7}  {'contracts':>9}  NPC hits")
print('-' * 72)
rows = []
for p in sorted(CRT.glob('tython_blockout-*.acrt'),
                key=lambda x: int(re.search(r'-1\.(\d+)\.acrt', x.name).group(1))):
    buf = p.read_bytes()
    schema_count = struct.unpack('<I', buf[4:8])[0]
    nc = '?'
    if schema_count == 0 and len(buf) > 9:
        flags = buf[8]
        i = 9
        if flags & 0x01:
            try:
                cnt, i = packed(buf, i)
                nc = cnt
            except Exception:
                nc = 'err'
    hits = []
    for node, label in NPC_NODES.items():
        for tok in tokens(node):
            if tok in buf:
                hits.append(f'{node & 0xFFF:03X}')
                break
    n = int(re.search(r'-1\.(\d+)\.acrt', p.name).group(1))
    print(f'{n:>5}  {len(buf):>7}  {schema_count:>7}  {str(nc):>9}  {",".join(hits)}')
    rows.append((n, schema_count, nc))

live = [r for r in rows if r[2] not in (0, '?', 'err')]
print(f"\nCRTs that actually carry contracts: {len(live)} of {len(rows)}"
      f"  -> numbers {[r[0] for r in live]}")
print("Total contracts sent by the captured stream:",
      sum(r[2] for r in rows if isinstance(r[2], int)))