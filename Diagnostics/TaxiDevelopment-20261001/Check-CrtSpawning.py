"""Do captured NPCs need a CRT contract to exist, or does awareness alone create them?

The user asks whether awareness/replication simply lacks the parameters needed to
spawn. The decisive test: for every NPC that demonstrably renders (vendor 0x1AC68957EB,
Weller 0x1AC6F6DC6D), search the captured CRT contract stream for a reference to its
node. If rendering NPCs appear ONLY in the awareness .aaw and never in any CRT, then
awareness alone is sufficient and the missing piece is record content. If they also
appear in CRTs, our taxi needs a matching contract too.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()


def packed(value):
    out = bytearray()
    while True:
        out.insert(0, value & 0xFF)
        value >>= 8
        if not value:
            break
    if len(out) <= 8 and (out[0] & 0x80 or len(out) == 1):
        return bytes(out)
    return bytes([0xC7 + len(out)]) + bytes(out)


AWARE = ROOT/'SharpServer/bin/Debug/AreaServer/Awareness'
CRT = ROOT/'SharpServer/bin/Debug/AreaServer/CRT'

KNOWN_RENDER = {
    0x1AC68957EB: 'vendor / medcenter droid (struct 64)',
    0x1AC6F6DC6D: 'Weller (struct 62, the only working NPC)',
    0x1AC689748C: 'struct-42 NPC',
    0x1AC689385F: 'struct-42 NPC',
}

print("=== is each rendering NPC present in the awareness object list? ===")
aware_nodes = {}
for f in sorted(AWARE.glob('*.aaw')):
    data = f.read_bytes()
    reader, _, count = d.read_gom_update(data, 0, f.name)
    for _ in range(count):
        rec = d.read_object_record(data, reader)
        aware_nodes[rec['node']] = (f.name, rec['structure_id'])
for node, label in KNOWN_RENDER.items():
    hit = aware_nodes.get(node)
    print(f"  0x{node:016X} {label:38} "
          f"{'aware in ' + hit[0] if hit else 'NOT IN ANY AWARENESS'}")

print("\n=== do those nodes also appear anywhere in the CRT contract stream? ===")
crt_blobs = {f.name: f.read_bytes() for f in sorted(CRT.glob('*.acrt'))}
for node, label in KNOWN_RENDER.items():
    found = []
    for token in (packed(node), node.to_bytes(8, 'little')):
        for name, blob in crt_blobs.items():
            if token in blob:
                found.append(name)
    print(f"  0x{node:016X} {label:38} "
          f"{sorted(set(found)) if found else 'NOT REFERENCED BY ANY CRT'}")

print("\n=== for contrast: does any CRT reference a known EFFECT/CONTAINER node? ===")
aware2 = (AWARE/'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
for sid in (11, 13, 14, 15):
    reader, _, count = d.read_gom_update(aware2, 0, 'aware')
    sample = None
    for _ in range(count):
        rec = d.read_object_record(aware2, reader)
        if rec['structure_id'] == sid:
            sample = rec['node']
            break
    if sample is None:
        continue
    found = [n for n, b in crt_blobs.items()
             if packed(sample) in b or sample.to_bytes(8, 'little') in b]
    print(f"  struct{sid:3} sample node 0x{sample:016X}: "
          f"{found if found else 'not referenced by any CRT'}")