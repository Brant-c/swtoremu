"""Diff the taxi record against Weller, the only confirmed WORKING npc.

The operator reports the captured struct-64 record at (-59.79,-6.90,-128.33)
renders a model but has no nameplate and is not interactable -- and that
position is med_poi01_masters_retreat_medic_droid.spn_c, so it is the medcenter
droid, not a vendor. It therefore is NOT a working reference.

Weller (0x1AC6F6DC6D, struct 62) is the only NPC the operator can see with a
nameplate and interact. This diffs the taxi record against Weller field by field,
mapping struct-62 indices to struct-66 by field definition id (the two shapes
have different index orders, so index arithmetic is invalid).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()


def load(path, skip=0):
    data = Path(path).read_bytes()[skip:]
    reader, _, count = d.read_gom_update(data, 0, Path(path).name)
    return data, [d.read_object_record(data, reader) for _ in range(count)]


def present(data, rec):
    st = schemas[rec['structure_id']]
    end = rec['body_start'] + rec['inner_size']
    states, _ = d.field_states(data, end, rec['value_end'] - end, len(st.fields), rec['style'])
    return st, {i for i, s in enumerate(states) if s == 1}


def by_def(sid, index):
    return schemas[sid].fields[index].definition


_, weller_recs = load(ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
                     'tython_blockout-4611686019869492753-1.2.aaw')
weller = next(r for r in weller_recs if r['node'] == 0x1AC6F6DC6D)
taxi_data, taxi_recs = load(ROOT/'Diagnostics/TaxiDevelopment-20261001/awareness-8.bin', skip=8)
taxi = next(r for r in taxi_recs if r['node'] == 0x1AC7002000)

wdata = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
         'tython_blockout-4611686019869492753-1.2.aaw').read_bytes()
wst, wfields = present(wdata, weller)
tst, tfields = present(taxi_data, taxi)

print(f"Weller   struct{weller['structure_id']} fields={len(wst.fields)} present={len(wfields)}")
print(f"Taxi     struct{taxi['structure_id']} fields={len(tst.fields)} present={len(tfields)}\n")

wmap = {by_def(62, i): i for i in sorted(wfields)}
tmap = {by_def(66, i): i for i in sorted(tfields)}

print(f"{'field name':30} {'Weller(62)':>14} {'Taxi(66)':>14}")
print("-" * 62)
only_weller = [k for k in wmap if k not in tmap]
only_taxi = [k for k in tmap if k not in wmap]
shared = [k for k in wmap if k in tmap]

for k in sorted(only_weller, key=lambda x: wmap[x]):
    print(f"{names.get(k,'?'):30} {'idx ' + str(wmap[k]):>14} {'ABSENT':>14}")
print()
for k in sorted(only_taxi, key=lambda x: tmap[x]):
    print(f"{names.get(k,'?'):30} {'ABSENT':>14} {'idx ' + str(tmap[k]):>14}")

print(f"\n{len(only_weller)} fields Weller carries that the taxi lacks; "
      f"{len(only_taxi)} the taxi carries that Weller lacks; {len(shared)} shared.")