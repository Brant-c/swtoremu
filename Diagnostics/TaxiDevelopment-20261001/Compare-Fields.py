"""Compare present field indices of the rendering donor vendor vs generated taxi."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()


def present(data, label, predicate):
    reader, _, count = g.d7.read_gom_update(data, 0, label)
    for _ in range(count):
        rec = g.d7.read_object_record(data, reader)
        if not predicate(rec):
            continue
        structure = schemas[rec['structure_id']]
        end = rec['body_start'] + rec['inner_size']
        states = g.dc.field_states(data, end, rec['value_end'] - end,
                                   len(structure.fields), rec['style'])
        active = [i for i, s in enumerate(states) if s == 1]
        print(f"{label} node=0x{rec['node']:016X} struct={rec['structure_id']} "
              f"inner={rec['inner_size']} present({len(active)}): {active}")
        for i in active:
            print(f"    [{i}] {names.get(structure.fields[i].definition, '?')}")
        return


awareness = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
             'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
present(awareness, 'donor', lambda r: r['node'] == 0x1AC68957EB)
generated = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
present(generated, 'taxi', lambda r: r['structure_id'] == 66)
