"""Debug the NPC record's state bytes against both decoders."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
gspec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(g)
schemas, _, _ = d.read_schema()
n = d.name_table()

data = (HERE/'awareness-8.bin').read_bytes()
payload = data[8:]
r, flags, count = d.read_gom_update(payload, 0, 'taxi')
rec = d.read_object_record(payload, r)
print(f"struct={rec['structure_id']} inner={rec['inner_size']} "
      f"body_start={rec['body_start']} value_end={rec['value_end']} style={rec['style']}")
nend = rec['body_start'] + rec['inner_size']
size = rec['value_end'] - nend
print(f"state bytes = {size}, fields = {len(schemas[66].fields)}")

try:
    a = d.field_states(payload, nend, size, len(schemas[66].fields), 8)
    print("d7 present:", [i for i, x in enumerate(a) if x == 1])
except Exception as exc:
    print("d7 field_states error:", exc)
b = g.dc.field_states(payload, nend, size, len(schemas[66].fields), 8)
print("g  present:", [i for i, x in enumerate(b) if x == 1])
print("raw state hex:", payload[nend:rec['value_end']].hex())
