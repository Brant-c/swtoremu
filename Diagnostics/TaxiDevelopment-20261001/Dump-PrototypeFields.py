"""Name the jediretreat_pad1 prototype field IDs from taxi-content.txt."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
names = g.d7.name_table()

ids = [
    0x4000000027BDA14B, 0x4000000027BDA14C, 0x40000003DE992C09, 0x40000004DDA27A71,
    0x40000005618EC27C, 0x40000007EE70D683, 0x40000007EE70D684, 0x40000007F6B3B43C,
    0x40000007F6B3B43D, 0x400000082CFBE218, 0x400000082DE6DE61, 0x400000097E10EBAB,
    0x400000098A308CF7, 0x40000009AF9F1222, 0x4000000A1D72EA3C, 0x4000000A4E63E821,
    0x4000000A4FA14A24, 0x4000000A731CD8C0, 0x4000000E582939A7, 0x4000000F3BBA9ABC,
    0x4000000F9C1EB267, 0x40000013A787EE87, 0x400000355F990B41,
]
for i in ids:
    print(f"0x{i:016X} {names.get(i, '<unnamed>')}")

print("\n-- schema66 name lookup for prototype-matched IDs --")
schemas, _, _ = g.d7.read_schema()
by_id = {f.definition: idx for idx, f in enumerate(schemas[66].fields)}
for i in ids:
    if i in by_id:
        print(f"0x{i:016X} -> schema66[{by_id[i]}] {names.get(i, '')}")
