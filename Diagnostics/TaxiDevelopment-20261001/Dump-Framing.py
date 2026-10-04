"""Dump the raw bytes around the donor record boundaries to see the framing."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, flags, count = g.d7.read_gom_update(data, 0, 'awareness')
records = [g.d7.read_object_record(data, reader) for _ in range(count)]

print(f"header bytes 0..26: {data[0:26].hex()}")
for i, rec in enumerate(records):
    if rec['node'] in (0x1AC68957EB, 0x1AC68957ED):
        prev = records[i-1]
        print(f"\nrecord node=0x{rec['node']:016X} outer_start={rec['outer_start']} "
              f"start={rec['start']} value_end={rec['value_end']}")
        print(f"  previous node=0x{prev['node']:016X} value_end={prev['value_end']}")
        gap = data[prev['value_end']:rec['start']]
        print(f"  gap prev.value_end..rec.start ({len(gap)}): {gap.hex()}")
        print(f"  rec.start..outer_start ({rec['outer_start']-rec['start']}): "
              f"{data[rec['start']:rec['outer_start']].hex()}")
        head = data[rec['start']:rec['start']+12]
        print(f"  record head 12: {head.hex()}")
