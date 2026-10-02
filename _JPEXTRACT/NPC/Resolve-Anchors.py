"""Resolve spnParentAnchorId values and confirm the struct-62 index question.

spnSpawnedComponentClassMethods gives the chain:

    GetSpawner()     -> Me.spnParentAnchorId
    GetSpawnerSpec() -> $SPAWNER.GetSpawnerSpecForNode(GetSpawner())

so the anchor must be a node the client can resolve. This looks each captured
anchor up in the GOM name table, and re-checks struct 62 (whose index 27 may not
be spnParentAnchorId -- that shape is a different field layout).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

for sid in (42, 62, 64, 66):
    f27 = schemas[sid].fields[27]
    print(f"struct{sid:3}[27] = {names.get(f27.definition, hex(f27.definition))}")
for sid in (42, 62, 64, 66):
    for idx, label in ((57, 'spnSpawnedSpec'), (91, 'entryAppearance'), (90, 'runScriptProtoId')):
        if idx < len(schemas[sid].fields):
            n = names.get(schemas[sid].fields[idx].definition, '?')
            if 'Spawned' in n or 'runScript' in n:
                print(f"struct{sid:3}[{idx}] = {n}")

print("\n=== captured spnParentAnchorId values, resolved ===")
anchors = {
    'set1 struct42 0x1AC68967A3': 0x4000000C5CCBAD0D,
    'set1 struct64 0x1AC68957EB': 0x400000136330355E,
    'set1 struct42 0x1AC689748C': 0x40000012F72F47E3,
    'set1 struct42 0x1AC68975A6': 0x40000012F72F47F3,
    'set1 struct42 0x1AC689385F': 0x40000004D61CD214,
}
for label, value in anchors.items():
    print(f"  {label:26} 0x{value:016X} -> {names.get(value, '<not in name table>')}")

print("\n=== the taxi values a record could borrow ===")
for label, value in (('vendor anchor', 0x400000136330355E),
                     ('vendor tmrContainer', 0x1AC68957EC),
                     ('vendor ablContainer', 0x1AC68957EE),
                     ('taxi template', 0xE0008B8CC0FAEA1D)):
    print(f"  {label:20} 0x{value:016X} -> {names.get(value, '<not in name table>')}")