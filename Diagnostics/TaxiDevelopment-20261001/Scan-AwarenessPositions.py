"""List captured awareness object positions and structures (field 0 only)."""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, flags, count = g.d7.read_gom_update(data, 0, 'awareness')
rows = []
for _ in range(count):
    rec = g.d7.read_object_record(data, reader)
    structure = schemas.get(rec['structure_id'])
    pos = None
    if structure is not None and rec['inner_size']:
        end = rec['body_start'] + rec['inner_size']
        states = g.dc.field_states(data, end, rec['value_end'] - end, len(structure.fields), rec['style'])
        if states and states[0] == 1 and structure.fields[0].parts[0].kind == 18:
            pos = struct.unpack('<3f', data[rec['body_start']:rec['body_start'] + 12])
    rows.append((rec['node'], rec['structure_id'], rec['template_id'], pos))

# Sort by distance to the compatibility taxi position and to the authored pad.
taxi = (-59.7872, -6.8998, -125.8348)
pad = (-53.5, -7.7, -125.5)
print(f"records={len(rows)}")
for label, target in (('taxi-compat', taxi), ('authored-pad', pad)):
    print(f"\n-- nearest captured objects to {label} {target}")
    def dist(row):
        if row[3] is None:
            return 1e9
        return sum((a - b) ** 2 for a, b in zip(row[3], target)) ** 0.5
    for node, sid, template, pos in sorted(rows, key=dist)[:8]:
        d = dist((node, sid, template, pos))
        print(f"  0x{node:016X} struct={sid} template=0x{template:016X} dist={d:8.2f} pos={pos}")

print("\n-- position range --")
pts = [r[3] for r in rows if r[3]]
for i, axis in enumerate('XYZ'):
    vals = [p[i] for p in pts]
    print(f"  {axis}: {min(vals):.2f} .. {max(vals):.2f}")
