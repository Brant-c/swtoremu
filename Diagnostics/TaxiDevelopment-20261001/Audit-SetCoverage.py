"""Which awareness set actually covers the authored taxi pad?

The taxi pad anchor (-53.5,-7.7,-125.5) came from the area instance dump. This
checks whether any object in the captured awareness sets lies near it, and what
each set contains. If neither set covers the pad, the NPC cannot render no
matter how correct its record is, and the problem is which set is being sent.
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

PAD = (-53.5, -7.7, -125.5)
base = ROOT/'SharpServer/bin/Debug/AreaServer/Awareness'


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


for f in sorted(base.glob('tython_blockout-*.aaw')):
    data = f.read_bytes()
    r, _, c = d.read_gom_update(data, 0, f.name)
    recs = [d.read_object_record(data, r) for _ in range(c)]
    print(f"\n=== {f.name} objects={c} bytes={len(data)}")
    rows = []
    for rec in recs:
        sid = rec['structure_id']
        st = schemas[sid]
        base_name = names.get(st.base_class, '?')
        end = rec['body_start'] + rec['inner_size']
        try:
            states, _ = d.field_states(data, end, rec['value_end'] - end,
                                       len(st.fields), rec['style'])
            present = [i for i, s in enumerate(states) if s == 1]
        except Exception:
            present = []
        pos = None
        if 1 in present and st.fields[0].parts[0].kind == 18:
            pos = tuple(round(v, 2) for v in struct.unpack(
                '<3f', data[rec['body_start']:rec['body_start'] + 12]))
        rows.append((sid, base_name, rec['node'], pos, len(present)))

    for sid, base_name, node, pos, n in sorted(
            rows, key=lambda x: dist(x[3], PAD) if x[3] else 1e9)[:12]:
        dd = dist(pos, PAD) if pos else 1e9
        print(f"  struct{sid:3} {base_name:22} node=0x{node:X} present={n:3} "
              f"pos={pos} dist_to_pad={dd:.1f}")

    positions = [x[3] for x in rows if x[3]]
    if positions:
        print(f"  -- position extent: X {min(p[0] for p in positions):.1f}..{max(p[0] for p in positions):.1f}"
              f"  Y {min(p[1] for p in positions):.1f}..{max(p[1] for p in positions):.1f}"
              f"  Z {min(p[2] for p in positions):.1f}..{max(p[2] for p in positions):.1f}")
        nearest = min((dist(p, PAD), p) for p in positions)
        print(f"  -- nearest object to the pad: {nearest[1]} at {nearest[0]:.1f}")