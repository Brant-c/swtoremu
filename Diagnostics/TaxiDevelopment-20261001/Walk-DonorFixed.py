"""Walk the donor vendor end-to-end with corrected kinds.

Corrections vs the earlier walk:
  * Boolean -> present with no value byte (state carries the value)
  * Enum    -> one raw byte (values >= 0xC0 are legal), not a packed token
  * Int64   -> signed packed token (0xC0..0xC7 are large negative values)
  * List/Map count -> halved for styles 8/10 (SerializeLookupList doubles it)
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
s, _, _ = g.d7.read_schema()
n = g.d7.name_table()


def read_field(walker, field, style, depth=0):
    kind = field.parts[0].kind
    if kind == 7:
        raw = walker.packed()
        c = raw >> 1 if style in (8, 10) else raw
        for _ in range(c):
            read_part(walker, field, 1, style, depth)
        return None
    if kind == 8:
        raw = walker.packed()
        c = raw >> 1 if style in (8, 10) else raw
        for _ in range(c):
            read_part(walker, field, 1, style, depth)
            read_part(walker, field, 2, style, depth)
        return None
    return read_part(walker, field, 0, style, depth)


def read_part(walker, field, index, style, depth):
    kind = field.parts[index].kind
    if kind == 2:
        return walker.packed_signed()
    if kind in (1, 9, 15, 17):
        return walker.packed()
    if kind == 5:
        return walker.byte()
    if kind == 3:
        return None
    if kind == 4:
        return struct.unpack('<f', walker.raw(4))[0]
    if kind == 18:
        return struct.unpack('<3f', walker.raw(12))
    if kind == 6:
        return walker.raw(walker.packed())
    raise Exception(f"kind {kind}")


data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'donor')
donor = next(r for r in (g.d7.read_object_record(data, reader) for _ in range(count))
             if r['node'] == 0x1AC68957EB)
structure = s[donor['structure_id']]
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
    try:
        read_field(walker, structure.fields[index], donor['style'])
    except Exception as exc:
        print(f"[{index}] {n.get(structure.fields[index].definition, '?'):26} ERROR {exc} at {walker.pos}")
        break
    spans[index] = (begin, walker.pos, data[begin:walker.pos])
print(f"walk {walker.pos}/{end} delta {walker.pos-end}")
print("\ntransplantable tail fields:")
for index in (62, 63, 66, 68, 70, 77, 78, 80, 86):
    if index in spans:
        b, e, raw = spans[index]
        print(f"  s64[{index}] {n.get(structure.fields[index].definition,'?'):26} {b}..{e} {raw.hex()}")
