"""Decode the client script-error node id and its component list.

The client reported errors against node 115007815681 with class list
4611686018435310013,4611686018455170113,4611686018456770059,4611686019631751166,
4611686035046870024. This resolves every id against the type-name table and
compares the component set with the taxi prototype's glommed components.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

NODE = 115007815681
print(f"error node {NODE} = 0x{NODE:X}")
print(f"  our NPC base placeholder 0x1AC7001000 = {0x1AC7001000}")
print(f"  runtime first taxi node 0x1AC7000001 = {0x1AC7000001}   <-- match: {NODE == 0x1AC7000001}")

classes = [4611686018435310013, 4611686018455170113, 4611686018456770059,
           4611686019631751166, 4611686035046870024]
print("\nreported component list:")
for c in classes:
    print(f"  {c}  0x{c:X}  {names.get(c, '<unnamed>')}")

print("\nschema66 additional classes the record declares:")
for c in schemas[66].additional_classes:
    print(f"  {c}  0x{c:X}  {names.get(c, '<unnamed>')}")

print("\ntaxi prototype glommed (from _JPEXTRACT/NPC/npc.location.tython.taxi.jediretreat_pad1.json):")
print("  4611686019631751166  brkOwnerComponent")
print("  4611686035046870024  taxTerminalComponent")

print("\nschema64/62/42 shapes for comparison:")
for sid in (42, 62, 64, 66):
    print(f"  struct{sid}: " + ', '.join(names.get(c, hex(c)) for c in schemas[sid].additional_classes))