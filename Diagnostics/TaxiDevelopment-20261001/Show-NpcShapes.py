"""Describe every captured chrNonPlayerCharacter record shape (42/62/64/66)."""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

for sid in (42, 62, 64, 66):
    st = schemas[sid]
    print(f"\n=== struct {sid} base={names.get(st.base_class)} fields={len(st.fields)} "
          f"additional={len(st.additional_classes)}")
    print("    components: " + ', '.join(names.get(c, hex(c)) for c in st.additional_classes))

roots = [ROOT/'SharpServer/bin/Debug/AreaServer/Awareness', ROOT/'Diagnostics']
seen = set()
for root in roots:
    if not root.exists():
        continue
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() != '.aaw':
            continue
        if str(path).lower() in seen:
            continue
        seen.add(str(path).lower())
        data = path.read_bytes()
        try:
            reader, flags, count = d.read_gom_update(data, 0, path.name)
            records = [d.read_object_record(data, reader) for _ in range(count)]
        except Exception:
            continue
        for rec in records:
            sid = rec['structure_id']
            if names.get(schemas[sid].base_class) != 'chrNonPlayerCharacter':
                continue
            structure = schemas[sid]
            end = rec['body_start'] + rec['inner_size']
            try:
                states, _ = d.field_states(data, end, rec['value_end'] - end,
                                           len(structure.fields), rec['style'])
                present = [i for i, s in enumerate(states) if s == 1]
            except Exception:
                present = ['?']
            pos = ''
            if isinstance(present, list) and present and present[0] == 1 \
                    and structure.fields[0].parts[0].kind == 18:
                pos = str(tuple(round(v, 2) for v in struct.unpack(
                    '<3f', data[rec['body_start']:rec['body_start'] + 12])))
            print(f"  {path.name} struct{sid:3} node=0x{rec['node']:016X} "
                  f"tmpl=0x{rec['template_id']:016X} parent=0x{rec['parent_id']:016X} "
                  f"inner={rec['inner_size']:4} style={rec['style']} present={len(present):3} {pos}")
            if isinstance(present, list):
                print(f"      {present}")