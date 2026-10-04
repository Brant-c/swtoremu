"""Enumerate the donor vendor's child records and the node refs in its body."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'awareness')
records = [g.d7.read_object_record(data, reader) for _ in range(count)]

DONOR = 0x1AC68957EB
donor = next(r for r in records if r['node'] == DONOR)
print(f"donor struct={donor['structure_id']} outer={donor['outer_start']}..{donor['value_end']} "
      f"inner={donor['inner_size']} class=0x{donor['class_id']:016X} template=0x{donor['template_id']:016X}")
print("children (parent_id == donor):")
for r in records:
    if r['parent_id'] == DONOR:
        print(f"  node=0x{r['node']:016X} struct={r['structure_id']} "
              f"class=0x{r['class_id']:016X} span={r['outer_start']}..{r['value_end']} "
              f"inner={r['inner_size']} base={names.get(schemas[r['structure_id']].base_class, '') if r['structure_id'] in schemas else '?'}")

print("\nall records (node/struct/parent/span):")
for r in records[:40]:
    print(f"  0x{r['node']:016X} struct={r['structure_id']} parent=0x{r['parent_id']:016X} "
          f"span={r['outer_start']}..{r['value_end']} inner={r['inner_size']}")
