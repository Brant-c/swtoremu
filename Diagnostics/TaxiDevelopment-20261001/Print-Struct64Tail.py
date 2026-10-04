import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
s, _, _ = g.d7.read_schema()
n = g.d7.name_table()
for sid in (64, 66):
    st = s[sid]
    print(f"=== struct {sid} base={n.get(st.base_class, '')} fields={len(st.fields)}")
    for i, f in enumerate(st.fields):
        if i >= 55:
            print(f"  {i:3} 0x{f.definition:016X} "
                  f"{n.get(f.definition, 'unnamed'):30} kinds={[p.kind for p in f.parts]}")
