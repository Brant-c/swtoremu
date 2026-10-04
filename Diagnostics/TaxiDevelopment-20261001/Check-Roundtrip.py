"""Round-trip the captured vendor donor and the generated taxi NPC records."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()


def check(data, label, predicate):
    reader, flags, count = g.d7.read_gom_update(data, 0, label)
    for _ in range(count):
        rec = g.d7.read_object_record(data, reader)
        if not predicate(rec):
            continue
        ok, detail = g.roundtrip_record(data, rec, schemas[rec['structure_id']], names)
        print(f"{label} node=0x{rec['node']:016X} struct={rec['structure_id']} roundtrip={ok} :: {detail}")
        return rec
    return None

awareness = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
             'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
check(awareness, 'captured vendor', lambda r: r['node'] == 0x1AC68957EB)

generated = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
check(generated, 'generated taxi', lambda r: r['structure_id'] == 66)
