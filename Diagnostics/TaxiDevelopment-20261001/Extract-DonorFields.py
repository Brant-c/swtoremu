"""Walk the rendering donor vendor through every present field.

Reports each field's wire byte span and whether the walk lands exactly on the
record's inner_size. A clean reconciliation means the donor's appearance and
identity fields (chrTemplateVisualIndex, _characterSpecification, chrClass,
cbtFaction, cbtCreatureType, brkResourceName, chrLevel, ablContainer, ...) can be
transplanted into the generated schema66 taxi record.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()

# Recover signed Int64 fields and keep Boolean value bytes out of the stream,
# matching the generated-record walk that reconciles to inner_size exactly.
_orig_parse_part = g.parse_part


def parse_part(walker, field, index, style):
    kind = field.parts[index].kind
    if kind == 3:
        return g.Part(kind, 1)
    if kind == 2:
        return g.Part(kind, walker.packed_signed())
    if kind == 5:
        return g.Part(kind, walker.packed())
    return _orig_parse_part(walker, field, index, style)


g.parse_part = parse_part

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'donor')
donor = None
for _ in range(count):
    rec = g.d7.read_object_record(data, reader)
    if rec['node'] == 0x1AC68957EB:
        donor = rec
        break

structure = schemas[donor['structure_id']]
start = donor['body_start']
end = start + donor['inner_size']
states = g.dc.field_states(data, end, donor['value_end'] - end,
                           len(structure.fields), donor['style'])
walker = g.ValueWalker(data, start, end, donor['style'])
spans = {}
for index, state in enumerate(states):
    if state != 1:
        continue
    begin = walker.pos
    field = structure.fields[index]
    try:
        if field.parts[0].kind in (7, 8):
            part = g.parse_container(walker, field, donor['style'])
        else:
            part = g.parse_part(walker, field, 0, donor['style'])
    except Exception as exc:
        print(f"[{index}] {names.get(field.definition, '?')}: ERROR {exc} at {walker.pos}")
        break
    spans[index] = data[begin:walker.pos]
    with_bytes = bytearray()
    g.emit_part(with_bytes, part)
    print(f"[{index:3}] off={begin:5}..{walker.pos:5} bytes={len(spans[index]):3} "
          f"emit_match={bytes(with_bytes) == spans[index]} "
          f"hex={spans[index].hex() if len(spans[index]) <= 20 else spans[index][:20].hex()+'..'}")

print(f"\nwalk ended at {walker.pos}, inner end {end}, delta {walker.pos - end}")
print(f"remaining {end - walker.pos} bytes: {data[walker.pos:end].hex()}")
