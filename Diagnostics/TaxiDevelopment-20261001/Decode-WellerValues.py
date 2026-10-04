"""Decode Weller's field values -- the only NPC whose char spec resolves.

The client reports "Char spec missing: Unknown spec(0)" against our taxi node, and
"Mag node doesn't have a valid asset spec" / "not a valid animation agent". The
appearance tail currently transplanted into the taxi record came from the captured
struct-64 record, which the operator reports renders a model but has NO nameplate
and is not interactable -- i.e. it is the medcenter droid, itself not fully
resolved. Weller is the only confirmed working NPC, so its values are the ones
worth transplanting.
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
gspec = importlib.util.spec_from_file_location('gen', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(g)
schemas, _, _ = d.read_schema()
names = d.name_table()

_orig = g.parse_part


def read_part(walker, field, index, style):
    kind = field.parts[index].kind
    if kind == 3:
        return g.Part(kind, 1)
    if kind == 2:
        return g.Part(kind, walker.packed_signed())
    if kind == 5:
        return g.Part(kind, walker.byte())
    return _orig(walker, field, index, style)


def read_field(walker, field, style):
    kind = field.parts[0].kind
    if kind == 7:
        raw = walker.packed()
        n = raw >> 1 if style in (8, 10) else raw
        for _ in range(n):
            read_part(walker, field, 1, style)
        return None
    if kind == 8:
        raw = walker.packed()
        n = raw >> 1 if style in (8, 10) else raw
        for _ in range(n):
            read_part(walker, field, 1, style)
            read_part(walker, field, 2, style)
        return None
    return read_part(walker, field, 0, style)


data = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
        'tython_blockout-4611686019869492753-1.2.aaw').read_bytes()
reader, _, count = g.d7.read_gom_update(data, 0, 'weller')
recs = [g.d7.read_object_record(data, reader) for _ in range(count)]
weller = next(r for r in recs if r['node'] == 0x1AC6F6DC6D)

st = schemas[weller['structure_id']]
start = weller['body_start']
end = start + weller['inner_size']
states, _ = d.field_states(data, end, weller['value_end'] - end, len(st.fields), weller['style'])
present = [i for i, s in enumerate(states) if s == 1]
print(f"Weller struct{weller['structure_id']} inner={weller['inner_size']} style={weller['style']} "
      f"present={len(present)}")

walker = g.ValueWalker(data, start, end, weller['style'])
out = {}
for i in present:
    field = st.fields[i]
    label = names.get(field.definition, '?')
    begin = walker.pos
    try:
        part = read_field(walker, field, weller['style'])
    except Exception as exc:
        print(f"  desync at field {i} ({label}): {exc} (pos {walker.pos}/{end})")
        break
    raw = data[begin:walker.pos]
    value = getattr(part, 'value', None)
    out[field.definition] = (i, label, value, raw)
    print(f"  s62[{i:2}] {label:32} = {value}   bytes={raw.hex() or '-'}")

print(f"\nwalk ended {walker.pos}/{end}  (clean={'yes' if walker.pos == end else 'NO'})")
print("\n--- spec-bearing fields ---")
for k in (0x40000010520A477F, 0x4000001036F1A242, 0x4000000BEC8F20D8,
          0x4000000E582939A7, 0x40000003DE992C09, 0x40000000256AEE1A, 0x40000009EFFE8FFA):
    if k in out:
        idx, label, val, raw = out[k]
        print(f"  s62[{idx:2}] {label:28} = {val}  packed={raw.hex() or '-'}")
    else:
        print(f"  {names.get(k,'?'):28} ABSENT from Weller")