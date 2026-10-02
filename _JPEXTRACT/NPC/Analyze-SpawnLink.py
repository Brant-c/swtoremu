"""Why can we not reuse an existing pattern? Compare every rendering NPC.

Every object that renders in this client came from a captured awareness payload.
The codebase therefore has a pattern for REPLAYING objects and none for
AUTHORING them. This compares the three captured chrNonPlayerCharacter shapes
against the synthesized taxi record field by field, to identify which differences
are semantic (a missing spawn link, missing model inputs) rather than incidental.
"""
import importlib.util
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()


def load(path, skip_header=0):
    data = Path(path).read_bytes()[skip_header:]
    reader, _, count = d.read_gom_update(data, 0, Path(path).name)
    return data, [d.read_object_record(data, reader) for _ in range(count)]


def name_of(sid, index):
    return names.get(schemas[sid].fields[index].definition, '?')


def present_of(data, rec):
    st = schemas[rec['structure_id']]
    end = rec['body_start'] + rec['inner_size']
    states, _ = d.field_states(data, end, rec['value_end'] - end, len(st.fields), rec['style'])
    return st, {i for i, s in enumerate(states) if s == 1}


def field_value(data, rec, fields, index):
    """Return the raw packed value of one present field, or None if absent."""
    if index not in fields:
        return None
    st = schemas[rec['structure_id']]
    r = d.Reader(data, rec['body_start'], rec['body_start'] + rec['inner_size'])
    for i in sorted(fields):
        if i == index:
            return r.packed()
        kind = st.fields[i].parts[0].kind
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
            raise SystemExit(f'unsupported kind {kind} at field {i} of struct {rec["structure_id"]}')
    return None


aware1, recs1 = load(ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
                     'tython_blockout-4611686019869492753-1.1.aaw')
aware2, recs2 = load(ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
                     'tython_blockout-4611686019869492753-1.2.aaw')
taxi_data, taxi = load(ROOT/'Diagnostics/TaxiDevelopment-20261001/awareness-8.bin', skip_header=8)

sets = {}
print("=== captured chrNonPlayerCharacter shapes, with spnParentAnchorId ===")
for tag, data, recs in (('set1', aware1, recs1), ('set2', aware2, recs2)):
    for rec in recs:
        sid = rec['structure_id']
        if names.get(schemas[sid].base_class) != 'chrNonPlayerCharacter':
            continue
        st, fields = present_of(data, rec)
        anchor = field_value(data, rec, fields, 27)
        sets[(tag, sid)] = fields
        print(f"  {tag} struct{sid:3} node=0x{rec['node']:016X} present={len(fields):3} "
              f"spnParentAnchorId(27)="
              f"{'ABSENT' if anchor is None else hex(anchor)}")

taxi_rec = next(r for r in taxi if r['node'] == 0x1AC7002000)
_, taxi_fields = present_of(taxi_data, taxi_rec)
print(f"\n  synthesized taxi struct{taxi_rec['structure_id']} present={len(taxi_fields)} "
      f"spnParentAnchorId(27)={'present' if 27 in taxi_fields else 'ABSENT'}")

print("\n=== fields EVERY captured rendering NPC carries, that the taxi record lacks ===")
common = set.intersection(*sets.values()) if sets else set()
missing = sorted(common - taxi_fields)
for i in missing:
    label = names.get(schemas[66].fields[i].definition, '?') if 66 in schemas else '?'
    print(f"  [{i:3}] {label}")
print(f"\n  {len(missing)} of {len(common)} commonly-present fields are missing; "
      f"taxi-only fields: {sorted(taxi_fields - common)}")