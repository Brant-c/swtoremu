"""Utility: print source of key decoder functions plus the tail schema fields."""
import importlib.util
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / '_dump_src.txt'
lines = []


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


d7 = load('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
lines.append('### d7.field_states')
lines.append(inspect.getsource(d7.field_states))
for attr in ('BitReader', 'describe_part', 'read_schema', 'name_table'):
    if hasattr(d7, attr):
        try:
            lines.append('### d7.%s' % attr)
            lines.append(inspect.getsource(getattr(d7, attr)))
        except Exception as exc:                        # noqa: BLE001
            lines.append('  <%r>' % (exc,))

schemas, _, _ = d7.read_schema()
names = d7.name_table()
for sid in (64, 66):
    st = schemas[sid]
    lines.append('### struct %d base=%s fields=%d' % (
        sid, names.get(st.base_class, ''), len(st.fields)))
    for i, f in enumerate(st.fields):
        lines.append('  %3d 0x%016X %-32s kinds=%s' % (
            i, f.definition, names.get(f.definition, 'unnamed'),
            [p.kind for p in f.parts]))

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('wrote %s' % OUT)