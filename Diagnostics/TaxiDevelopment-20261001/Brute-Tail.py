"""Find the tail field split with corrected kinds (signed Int64, byte enums)."""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
s, _, _ = g.d7.read_schema()
n = g.d7.name_table()

data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'donor')
donor = next(r for r in (g.d7.read_object_record(data, reader) for _ in range(count))
             if r['node'] == 0x1AC68957EB)
end = donor['body_start'] + donor['inner_size']

# struct-64 index -> struct-66 index for the donor's present tail fields.
mapping = [62, 63, 66, 68, 70, 77, 78, 80, 86]
s66 = [62, 63, 66, 68, 69, 76, 77, 79, 85]


def read_field(walker, field, style):
    kind = field.parts[0].kind
    if kind == 7:
        raw = walker.packed()
        count = raw >> 1 if style in (8, 10) else raw
        for _ in range(count):
            _ = walker.byte()
        return f"list[{count}]"
    if kind == 8:
        raw = walker.packed()
        count = raw >> 1 if style in (8, 10) else raw
        return f"map[{count}]"
    if kind == 2:
        return f"int={walker.packed_signed()}"
    if kind in (1, 15, 9, 17):
        return f"id=0x{walker.packed():X}"
    if kind == 5:
        return f"enum={walker.byte()}"
    if kind == 3:
        return "bool"
    if kind == 4:
        return f"float={struct.unpack('<f', walker.raw(4))[0]}"
    if kind == 18:
        return "vec3"
    raise Exception(f"kind {kind}")


for start in range(5300, 5322):
    walker = g.ValueWalker(data, start, end, donor['style'])
    parts = []
    ok = True
    for idx64, idx66 in zip(mapping, s66):
        try:
            parts.append(read_field(walker, s[66].fields[idx66], donor['style']))
        except Exception as exc:
            ok = False
            parts.append(f"X({exc})")
            break
    if ok and walker.pos == end:
        print(f"*** start={start} reconciles to {end}")
        for idx64, idx66, p in zip(mapping, s66, parts):
            print(f"    s64[{idx64}]->s66[{idx66}] {n.get(s[66].fields[idx66].definition,'?'):26} {p}")
