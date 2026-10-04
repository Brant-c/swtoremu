"""Decode the donor vendor's tail fields into struct-66 field indices.

The donor is struct 64 (96 fields); the generated taxi record is struct 66
(95 fields) which drops struct-64 index 69 (vndVendorIconOnExtraMaps). Every
struct-64 index >= 70 therefore maps to struct-66 index-1. This walks the tail
with the struct-66 field definitions and reports the byte span + emitted bytes
for each appearance/identity field, so they can be transplanted verbatim.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
s, _, _ = g.d7.read_schema()
n = g.d7.name_table()

_orig = g.parse_part


def parse_part(walker, field, index, style):
    kind = field.parts[index].kind
    if kind == 3:
        return g.Part(kind, 1)
    if kind == 2:
        return g.Part(kind, walker.packed_signed())
    if kind == 5:
        return g.Part(kind, walker.packed())
    return _orig(walker, field, index, style)


g.parse_part = parse_part

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'donor')
donor = next(r for r in (g.d7.read_object_record(data, reader) for _ in range(count))
             if r['node'] == 0x1AC68957EB)

# struct-64 index -> struct-66 index for the donor's present tail fields.
mapping = [(62, 62), (63, 63), (66, 66), (68, 68), (70, 69),
           (77, 76), (78, 77), (80, 79), (86, 85)]

start = 5312
end = donor['body_start'] + donor['inner_size']
walker = g.ValueWalker(data, start, end, donor['style'])
for s64, s66 in mapping:
    field = s[66].fields[s66]
    begin = walker.pos
    try:
        if field.parts[0].kind in (7, 8):
            part = g.parse_container(walker, field, donor['style'])
        else:
            part = g.parse_part(walker, field, 0, donor['style'])
    except Exception as exc:
        print(f"struct64[{s64}]->struct66[{s66}] {n.get(field.definition, '?'):26} "
              f"ERROR {exc} at {walker.pos}")
        break
    out = bytearray()
    g.emit_part(out, part)
    print(f"struct64[{s64}]->struct66[{s66}] {n.get(field.definition, '?'):26} "
          f"off={begin:5}..{walker.pos:5} bytes={walker.pos-begin:3} "
          f"value={getattr(part, 'value', None)} emit={bytes(out).hex()}")
print(f"\nwalk {walker.pos}/{end} delta {walker.pos-end}")
print(f"remaining: {data[walker.pos:end].hex()}")
