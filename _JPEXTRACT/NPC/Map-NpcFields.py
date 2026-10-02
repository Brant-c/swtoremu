"""Resolve Jedipedia node field IDs to chrCharacter schema field names.

The extracted `npc.location.tython.taxi.jediretreat_pad1` node has baseClass
chrNonPlayerCharacter, the same class the awareness record uses (structure 66),
so its field IDs must resolve against the same type-name table.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
names = d.name_table()
schemas, _, _ = d.read_schema()

bydef = {}
for sid, st in schemas.items():
    for index, field in enumerate(st.fields):
        bydef.setdefault(field.definition, []).append((sid, index, names.get(field.definition, '?')))


def hexid(value):
    return f"0x{int(value):016X}"


for path in sorted((ROOT/'_JPEXTRACT/NPC').glob('npc.*.json')):
    node = json.loads(path.read_text())
    meta = node['_metadata']
    print(f"\n=== {path.name}")
    print(f"    id={meta['id']} ({hexid(meta['id'])}) baseClass={meta['baseClass']}")
    for component in meta.get('glommed', []):
        print(f"    glom {component} ({hexid(component)}) -> {names.get(int(component), '<unnamed>')}")
    for key, value in node.items():
        if key.startswith('_'):
            continue
        hid = hexid(key)
        entries = bydef.get(int(key), [])
        where = ', '.join(f"struct{a}[{b}] {c}" for a, b, c in entries) or 'no schema field'
        print(f"  {hid} {names.get(int(key), '<unnamed>'):28} = {str(value)[:110]}  <- {where}")