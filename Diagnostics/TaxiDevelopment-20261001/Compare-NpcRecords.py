"""Three-way comparison of character records, aligned by GOM definition id.

Structures 62 (Weller, the only NPC the client resolves), 64 (the captured
vendor: renders a model, no nameplate, not interactable) and 66 (our taxi) have
different field *indices* for the same definition, so aligning by definition id
is the only way to compare them. Values are decoded with the grammar resolved in
Solve-TailWidths.py, which is why this comparison is admissible now.

Run: python Diagnostics/TaxiDevelopment-20261001/Compare-NpcRecords.py
Writes: npc-record-comparison.txt
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
lines = []


def say(text=''):
    print(text)
    lines.append(text)


spec = importlib.util.spec_from_file_location('stw', HERE / 'Solve-TailWidths.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

AWARENESS = ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness'

TARGETS = [
    ('Weller (works)', 62, 0x1AC6F6DC6D,
     AWARENESS / 'tython_blockout-4611686019869492753-1.2.aaw'),
    ('Vendor (model, no nameplate)', 64, 0x1AC68957EB,
     AWARENESS / 'tython_blockout-4611686019869492753-1.1.aaw'),
]


def capture(path):
    blob = path.read_bytes()
    reader, _, count = m.d7.read_gom_update(blob, 0, path.name)
    return blob, [m.d7.read_object_record(blob, reader) for _ in range(count)]


def decode(blob, field, pos, end, style):
    """Human text for one scalar field; containers report their entry count."""
    kind = field.parts[0].kind
    try:
        if kind == 3:
            return 'true'
        if kind in (1, 15, 17, 9):
            v, _ = m.packed(pos, end)
            return '0x%X' % v if kind != 17 else str(v)
        if kind == 2:
            v, _ = m.signed(pos, end)
            return '%d (0x%X)' % (v, v & 0xFFFFFFFFFFFFFFFF)
        if kind == 4:
            return '%g' % struct.unpack('<f', blob[pos:pos + 4])[0]
        if kind == 18:
            return '%g,%g,%g' % struct.unpack('<3f', blob[pos:pos + 12])
        if kind == 5:
            v, _ = m.packed(pos, end)
            return 'enum=%d' % v
        if kind == 6:
            if pos < end and blob[pos] == 0xD2:
                n, p = m.packed(pos + 1, end)
            else:
                n, p = m.packed(pos, end)
            return '"%s"' % blob[p:p + n].decode('latin-1')
        if kind in (7, 8):
            q = pos
            if kind == 7 and q < end and blob[q] == 0xD2:
                return 'string entries'
            if kind == 7 and q < end and blob[q] == 0xCF:
                _, q = m.packed(q, end)
            raw, _ = m.packed(q, end)
            n = raw >> 1 if style in (8, 10) else raw
            return '%d entries' % n
    except m.Bad as exc:
        return '<%s>' % exc
    return '?'


def scan(label, structure_id, node, path):
    blob, recs = capture(path)
    m.data = blob
    rec = next(r for r in recs if r['node'] == node)
    structure = m.schemas[structure_id]
    style = rec.get('style', 7)
    m.style_halve = style in (8, 10)
    m.LIST_MODE = 'B'
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = m.d7.field_states(blob, end, rec['value_end'] - end,
                              len(structure.fields), style)
    present = [k for k in range(len(st)) if st[k] == 1]
    say('')
    say('#' * 72)
    say('# %s' % label)
    say('# struct %d, node %#x, style %s, inner %d, present %d/%d, '
        'template %#018X' % (structure_id, node, style, rec['inner_size'],
                             len(present), len(structure.fields),
                             rec['template_id']))
    say('#' * 72)
    say('  %-34s %-9s %s' % ('field', 'offset', 'value'))
    out = {}
    pos = body
    for k in present:
        begin = pos
        try:
            pos = m.ref_part(structure.fields[k].parts, 0, pos, end)
        except m.Bad:
            say('  %-34s %-9s <tail unresolved from here>' % (
                m.names.get(structure.fields[k].definition, '?'),
                '+%d' % (begin - body)))
            break
        field = structure.fields[k]
        name = m.names.get(field.definition, '0x%016X' % field.definition)
        out[field.definition] = (name, decode(blob, field, begin, end, style))
        say('  %-34s %-9s %s' % (name, '+%d' % (begin - body),
                                 out[field.definition][1]))
    reconciled = (pos == end)
    say('  ---> walks %d/%d (%s)' % (pos - body, rec['inner_size'],
                                     'EXACT' if reconciled else 'PARTIAL'))
    return out, reconciled


results = {}
for label, sid, node, path in TARGETS:
    results[label] = scan(label, sid, node, path)

taxi_blob, taxi_recs = capture(ROOT / 'SharpServer/AreaServer/TaxiNpc.bin')
m.data = taxi_blob
results['Taxi (ours)'] = scan('Taxi (ours)', 66, taxi_recs[0]['node'],
                              ROOT / 'SharpServer/AreaServer/TaxiNpc.bin')

WORK = 'Weller (works)'
TAXI = 'Taxi (ours)'
VENDOR = 'Vendor (model, no nameplate)'
work, _ = results[WORK]
taxi, _ = results[TAXI]
vend, _ = results[VENDOR]

say('')
say('=' * 72)
say('DIFF vs the one NPC the client actually resolves')
say('=' * 72)
say('')
say('A. Replicated by Weller, NOT replicated by our taxi record:')
for defn, (name, value) in sorted(work.items(), key=lambda kv: kv[1][0]):
    if defn not in taxi:
        say('   %-34s Weller=%s' % (name, value))
say('')
say('B. Replicated by our taxi, NOT by Weller (all must be vendor/template '
    'artifacts - the taxi surface is only 2 fields):')
for defn, (name, value) in sorted(taxi.items(), key=lambda kv: kv[1][0]):
    if defn not in work:
        say('   %-34s ours=%-22s vendor=%s' % (
            name, value, vend.get(defn, ('-', 'ABSENT'))[1]))
say('')
say('C. Replicated by all three but carrying DIFFERENT values:')
for defn, (name, value) in sorted(taxi.items(), key=lambda kv: kv[1][0]):
    if defn in work and defn in vend:
        wv, vv = work[defn][1], vend[defn][1]
        if wv != value or vv != value:
            say('   %-34s ours=%-24s Weller=%-24s vendor=%s'
                % (name, value, wv, vv))
say('')
say('D. Replicated by all three with the SAME value (control group):')
same = 0
for defn, (name, value) in sorted(taxi.items(), key=lambda kv: kv[1][0]):
    if defn in work and defn in vend and work[defn][1] == value == vend[defn][1]:
        same += 1
        say('   %-34s = %s' % (name, value))
say('   (%d fields identical across all three)' % same)

(HERE / 'npc-record-comparison.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote npc-record-comparison.txt')