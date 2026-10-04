"""Compare record parent links across every captured NPC and the taxi.

Weller is the only confirmed working NPC (nameplate + interaction), so its
parent/class/template are the reference. The taxi borrows the captured vendor's
parent, which was never verified against a working NPC.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

base = ROOT/'SharpServer/bin/Debug/AreaServer/Awareness'
records = {}
for f in sorted(base.glob('tython_blockout-*.aaw')):
    data = f.read_bytes()
    reader, _, count = d.read_gom_update(data, 0, f.name)
    for _ in range(count):
        rec = d.read_object_record(data, reader)
        records[rec['node']] = (rec, f.name)

allnodes = set(records)
print("=== every chrNonPlayerCharacter: node, template, parent, class ===")
for node, (rec, src) in sorted(records.items()):
    sid = rec['structure_id']
    if names.get(schemas[sid].base_class) != 'chrNonPlayerCharacter':
        continue
    tag = 'WELLER (working)' if node == 0x1AC6F6DC6D else ''
    parent_known = 'present' if rec['parent_id'] in allnodes else 'NOT a captured object'
    print(f"  struct{sid:3} node=0x{node:X} src={src[-5:]} "
          f"template=0x{rec['template_id']:X} class=0x{rec['class_id']:X} "
          f"parent=0x{rec['parent_id']:X} [{parent_known}] {tag}")

taxi_data = (ROOT/'Diagnostics/TaxiDevelopment-20261001/awareness-8.bin').read_bytes()[8:]
reader, _, count = d.read_gom_update(taxi_data, 0, 'taxi')
taxi = [d.read_object_record(taxi_data, reader) for _ in range(count)]
npc = taxi[0]
print(f"\n  struct{npc['structure_id']:3} node=0x{npc['node']:X} src=taxi "
      f"template=0x{npc['template_id']:X} class=0x{npc['class_id']:X} "
      f"parent=0x{npc['parent_id']:X} "
      f"[{'present' if npc['parent_id'] in allnodes else 'NOT a captured object'}] TAXI")

print("\n=== distinct parents used by captured NPCs ===")
parents = {}
for node, (rec, src) in records.items():
    sid = rec['structure_id']
    if names.get(schemas[sid].base_class) != 'chrNonPlayerCharacter':
        continue
    parents.setdefault(rec['parent_id'], []).append(f"0x{node:X}")
for p, users in parents.items():
    resolved = names.get(p, '<not in name table>')
    print(f"  parent=0x{p:X} used by {len(users)} npc(s) -> {resolved}")