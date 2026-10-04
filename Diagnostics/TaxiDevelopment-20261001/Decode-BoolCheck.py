"""Reconcile field walks under two Boolean encodings.

The compact-schema reader either consumes a value byte for a present Boolean or
encodes it by field-state alone. This walks both the captured vendor donor and
the generated taxi NPC under each model and reports whether the walk lands
exactly on inner_size.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()

_orig = g.parse_part


def make_parser(boolean_byte):
    def parse_part(walker, field, index, style):
        kind = field.parts[index].kind
        if kind == 3 and not boolean_byte:
            return g.Part(kind, 1)
        if kind == 5:
            return g.Part(kind, walker.packed())
        if kind == 2:
            return g.Part(kind, walker.packed_signed())
        return _orig(walker, field, index, style)
    return parse_part


def walk(data, rec, boolean_byte):
    g.parse_part = make_parser(boolean_byte)
    structure = schemas[rec['structure_id']]
    start = rec['body_start']
    end = start + rec['inner_size']
    states = g.dc.field_states(data, end, rec['value_end'] - end, len(structure.fields), rec['style'])
    walker = g.ValueWalker(data, start, end, rec['style'])
    try:
        for index, state in enumerate(states):
            if state != 1:
                continue
            field = structure.fields[index]
            if field.parts[0].kind in (7, 8):
                g.parse_container(walker, field, rec['style'])
            else:
                g.parse_part(walker, field, 0, rec['style'])
    except Exception as exc:
        return f"ERROR {exc} at pos {walker.pos}"
    return f"consumed {walker.pos}/{end} delta {walker.pos-end}"


def find(data, label, predicate):
    reader, flags, count = g.d7.read_gom_update(data, 0, label)
    for _ in range(count):
        rec = g.d7.read_object_record(data, reader)
        if predicate(rec):
            for boolean_byte in (True, False):
                print(f"{label} node=0x{rec['node']:016X} struct={rec['structure_id']} "
                      f"booleanByte={boolean_byte}: {walk(data, rec, boolean_byte)}")
            return


awareness = (ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/'
             'tython_blockout-4611686019869492753-1.1.aaw').read_bytes()
find(awareness, 'captured vendor', lambda r: r['node'] == 0x1AC68957EB)
generated = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
find(generated, 'generated taxi', lambda r: r['structure_id'] == 66)
