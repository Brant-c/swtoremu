"""Read captured NPC fields through the existing compact-schema decoder."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
original_parse = g.parse_part
def parse_part(walker, field, index, style):
    kind = field.parts[index].kind
    if kind == 5:
        return g.Part(kind, walker.packed())
    if kind == 2:
        return g.Part(kind, walker.packed_signed())
    return original_parse(walker, field, index, style)
g.parse_part = parse_part
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()
data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, flags, count = g.d7.read_gom_update(data, 0, 'awareness')
for _ in range(count):
    rec = g.d7.read_object_record(data, reader)
    if rec['structure_id'] != 64:
        continue
    print(rec)
    structure = schemas[64]
    print('ROUNDTRIP', g.roundtrip_record(data, rec, structure, names))
    start = rec['body_start']
    end = start+rec['inner_size']
    states = g.dc.field_states(data, end, rec['value_end']-end, len(structure.fields), rec['style'])
    walker = g.ValueWalker(data, start, end, rec['style'])
    for index, state in enumerate(states):
        field = structure.fields[index]
        if state != 1:
            continue
        if field.parts[0].kind == 3:
            print(index, names.get(field.definition,''), 'BOOLEAN STATE', state)
            continue
        part = g.parse_container(walker, field, rec['style']) if field.parts[0].kind in (7,8) else g.parse_part(walker,field,0,rec['style'])
        print(index, hex(field.definition), names.get(field.definition,''), part.kind, part.value, [(p.kind,p.value) for p in part.children])
    print('CONSUMED',walker.pos,end)
print('TAX SCHEMA')
for i,f in enumerate(schemas[66].fields):
    print(i,hex(f.definition),names.get(f.definition,''),[p.kind for p in f.parts])
