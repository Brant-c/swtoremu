"""Find any CAPTURED structure-66 record to use as ground truth for a rendering NPC.

Our taxi record is the only synthesized structure-66 record we know of. If any
captured awareness/CRT fixture contains a structure-66 chrNonPlayerCharacter
object, its exact field set and byte layout is a proven-rendering template we
can diff against instead of reasoning from structure 64.
"""
import importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

bases = {}
for sid, st in schemas.items():
    bases[sid] = names.get(st.base_class, hex(st.base_class))

roots = [
    ROOT/'SharpServer/bin/Debug/AreaServer/Awareness',
    ROOT/'SharpServer/bin/Debug/AreaServer/CRT',
    ROOT/'Diagnostics',
]
exts = {'.aaw', '.acrt', '.aef'}
seen = set()
summary = Counter()
hits = []

for root in roots:
    if not root.exists():
        continue
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        key = str(path).lower()
        if key in seen or path.name.startswith(('awareness-8', 'awareness-19')):
            continue
        seen.add(key)
        data = path.read_bytes()
        # GOM update streams start with a u32 then flags; try each plausible start.
        for offset in (0, 8, 12):
            if offset >= len(data):
                continue
            try:
                reader, flags, count = d.read_gom_update(data, offset, path.name)
                if count is None or count > 400:
                    continue
                records = [d.read_object_record(data, reader) for _ in range(count)]
            except Exception:
                continue
            for rec in records:
                sid = rec['structure_id']
                summary[(sid, bases.get(sid, '?'))] += 1
                if sid == 66:
                    hits.append((path, offset, rec))
            break

print("structure/base histogram across captured fixtures:")
for (sid, base), n in sorted(summary.items()):
    print(f"  struct {sid:3} {base:34} x{n}")

print(f"\nstructure 66 records found: {len(hits)}")
for path, offset, rec in hits:
    print(f"  {path.relative_to(ROOT)} @{offset} node=0x{rec['node']:016X} "
          f"template=0x{rec['template_id']:016X} parent=0x{rec['parent_id']:016X} "
          f"inner={rec['inner_size']} style={rec['style']}")
    structure = schemas[66]
    end = rec['body_start'] + rec['inner_size']
    try:
        states, _ = d.field_states(path.read_bytes(), end, rec['value_end'] - end,
                                   len(structure.fields), rec['style'])
        present = [i for i, s in enumerate(states) if s == 1]
        print(f"    present({len(present)}): {present}")
        for i in present:
            print(f"      [{i}] {names.get(structure.fields[i].definition, '?')}")
    except Exception as exc:
        print(f"    state decode failed: {exc}")