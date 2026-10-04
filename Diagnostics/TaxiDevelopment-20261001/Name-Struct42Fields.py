"""Name struct 42's present fields and decode its field-32 value per record.

Struct 42 is the shape used by the NPCs the operator actually saw rendering in
the retreat. If its field 32 is taxTerminalSpec then a captured taxi-terminal
NPC exists and can be cloned instead of synthesized.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, flags, count = d.read_gom_update(data, 0, 'aaw')
records = [d.read_object_record(data, reader) for _ in range(count)]

st = schemas[42]
present = [0, 1, 9, 10, 13, 22, 23, 24, 25, 26, 27, 32, 33, 34, 35, 37, 38, 42, 55,
           59, 60, 61, 64, 66, 73, 74, 76, 82]
print("struct 42 present-field names:")
for i in present:
    print(f"  [{i:2}] 0x{st.fields[i].definition:016X} {names.get(st.fields[i].definition,'?'):28} "
          f"kinds={[p.kind for p in st.fields[i].parts]}")

print("\nfield 32 raw value per struct-42 record:")
for rec in records:
    if rec['structure_id'] != 42:
        continue
    end = rec['body_start'] + rec['inner_size']
    states, _ = d.field_states(data, end, rec['value_end'] - end, len(st.fields), rec['style'])
    if states[32] != 1:
        print(f"  node=0x{rec['node']:016X} field32 absent")
        continue
    r = d.Reader(data, rec['body_start'], end)
    for i in present:
        if i == 32:
            value = r.packed()
            break
        field = st.fields[i]
        kind = field.parts[0].kind
        if kind in (1, 2, 9, 15, 17):
            r.packed()
        elif kind == 3:
            pass
        elif kind == 4:
            r.pos += 4
        elif kind == 5:
            r.byte()
        elif kind == 18:
            r.pos += 12
        else:
            print(f"  node=0x{rec['node']:016X} unexpected kind {kind} at field {i}")
            break
    print(f"  node=0x{rec['node']:016X} tmpl=0x{rec['template_id']:016X} "
          f"field32=0x{value:X} ({value})")