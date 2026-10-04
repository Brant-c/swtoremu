"""Cross-check the resolved value grammar against the Weller capture.

The grammar was derived from tython_blockout-...-1.1.aaw. Weller lives in
...-1.2.aaw and is the only NPC the client actually resolves, so it is an
independent record family. If the same rule reconciles it too, the grammar is
not an artefact of one file.

Run: python Diagnostics/TaxiDevelopment-20261001/Crosscheck-Weller.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location('stw', HERE / 'Solve-TailWidths.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

m.data = (ROOT / ('SharpServer/bin/Debug/AreaServer/Awareness/'
                  'tython_blockout-4611686019869492753-1.2.aaw')).read_bytes()
reader, _, count = m.d7.read_gom_update(m.data, 0, 'weller')
m.records = [m.d7.read_object_record(m.data, reader) for _ in range(count)]

print('records: %d' % len(m.records))
for rec in m.records:
    if rec['inner_size'] is None:
        continue
    struct = m.schemas.get(rec['structure_id'])
    if struct is None:
        continue
    m.style_halve = rec.get('style', 7) in (8, 10)
    good, off, field, why = m.ref_walk(rec, struct)
    name = m.names.get(struct.base_class, '?')
    if good:
        print('  PASS node=%#x struct=%d (%s) style=%s inner=%d' % (
            rec['node'], rec['structure_id'], name, rec['style'],
            rec['inner_size']))
    else:
        print('  FAIL node=%#x struct=%d (%s) style=%s inner=%d -> at +%d %s' % (
            rec['node'], rec['structure_id'], name, rec['style'],
            rec['inner_size'], off, why))

# Detail for the confirmed-working NPC.
weller = next(r for r in m.records if r['node'] == 0x1AC6F6DC6D)
m.print_ref_layout(weller, m.schemas[weller['structure_id']], 'Weller')
m.solve(weller, m.schemas[weller['structure_id']], 'Weller width search')
Path(HERE / 'weller-crosscheck.txt').write_text('\n'.join(m.lines),
                                                encoding='utf-8')
print('\nstruct 62 fields 50..70:')
for i in range(50, 71):
    f = m.schemas[62].fields[i]
    print('  %3d 0x%016X %-34s kinds=%s' % (
        i, f.definition, m.names.get(f.definition, '?'),
        [p.kind for p in f.parts]))
print('\nwrote weller-crosscheck.txt')