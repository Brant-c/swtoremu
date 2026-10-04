"""Dump generated taxi NPC and the captured vendor donor side by side.

Read-only diagnostic. Uses the existing compact-schema decoder with the
enum/signed packing corrections from Inspect-Awareness.py. Prints field
index, definition name, kind, and value for each transmitted field so the
omitted taxi appearance/agent fields can be named precisely.
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

_original_parse = g.parse_part
def parse_part(walker, field, index, style):
    kind = field.parts[index].kind
    if kind == 5:
        return g.Part(kind, walker.packed())
    if kind == 2:
        return g.Part(kind, walker.packed_signed())
    return _original_parse(walker, field, index, style)
g.parse_part = parse_part

schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()


def dump_record(data, rec, label):
    structure = schemas[rec['structure_id']]
    print(f"\n=== {label} node=0x{rec['node']:016X} struct={rec['structure_id']} "
          f"flags=0x{rec['flags']:02X} class=0x{rec['class_id']:016X} "
          f"template=0x{rec['template_id']:016X} parent=0x{rec['parent_id']:016X} "
          f"style={rec['style']} inner={rec['inner_size']}")
    base = names.get(structure.base_class, hex(structure.base_class))
    print(f"  base_class={base} additional={[hex(c) for c in structure.additional_classes]} "
          f"fields={len(structure.fields)}")
    start = rec['body_start']
    end = start + rec['inner_size']
    states = g.dc.field_states(data, end, rec['value_end'] - end, len(structure.fields), rec['style'])
    walker = g.ValueWalker(data, start, end, rec['style'])
    for index, state in enumerate(states):
        if state != 1:
            continue
        field = structure.fields[index]
        fname = names.get(field.definition, hex(field.definition))
        if field.parts[0].kind == 3:
            print(f"  {index:3} {fname:55} BOOLEAN_STATE")
            continue
        try:
            part = (g.parse_container(walker, field, rec['style'])
                    if field.parts[0].kind in (7, 8)
                    else g.parse_part(walker, field, 0, rec['style']))
            extra = ''
            if part.kind == 4:
                try:
                    extra = f' float={struct.unpack("<f", struct.pack("<I", part.value & 0xFFFFFFFF))[0]:.4f}'
                except Exception:
                    extra = ''
            print(f"  {index:3} {fname:55} kind={part.kind} value={part.value}"
                  f"{extra} children={[(p.kind, p.value) for p in part.children][:6]}")
        except Exception as exc:
            print(f"  {index:3} {fname:55} ERROR {exc}")
    print(f"  CONSUMED {walker.pos}/{end}  states={states}")


awareness = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
             'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, flags, count = g.d7.read_gom_update(awareness, 0, 'captured awareness')
records = [g.d7.read_object_record(awareness, reader) for _ in range(count)]

print(f"captured awareness flags=0x{flags:02X} objects={count}")
for rec in records:
    print(f"  node=0x{rec['node']:016X} flags=0x{rec['flags']:02X} struct={rec['structure_id']} "
          f"template=0x{rec['template_id']:016X} class=0x{rec['class_id']:016X}")

donor = next(x for x in records if x['node'] == 0x1AC68957EB)
dump_record(awareness, donor, 'captured vendor donor')

generated = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
reader, flags, count = g.d7.read_gom_update(generated, 0, 'generated taxi')
gen_records = [g.d7.read_object_record(generated, reader) for _ in range(count)]
dump_record(generated, gen_records[0], 'generated taxi NPC')

print("\n=== schema 66 fields (id + name) ===")
for i, f in enumerate(schemas[66].fields):
    print(f"  {i:3} 0x{f.definition:016X} {names.get(f.definition, hex(f.definition)):55} kinds={[p.kind for p in f.parts]}")
print("\n=== schema 66 additional classes ===")
for c in schemas[66].additional_classes:
    print(f"  0x{c:016X} {names.get(c, '')}")
print("\n=== schema 64 fields ===")
for i, f in enumerate(schemas[64].fields):
    print(f"  {i:3} {names.get(f.definition, hex(f.definition)):55} kinds={[p.kind for p in f.parts]}")
