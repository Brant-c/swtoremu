"""Print the exact byte layout of one character record's present fields.

Reports, per present field, the byte offset relative to body_start, the bytes
the current walker consumed, and the decoded text. That makes the divergence
point visible instead of inferred.

Usage: python Show-CharacterBytes.py [node_hex] [structure]
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / '_characterbytes.txt'
lines = []


def say(text=''):
    print(text)
    lines.append(text)


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


d7 = load('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
cv = load('cv', ROOT / 'Diagnostics/Decode-CrtValues.py')
schemas, _, _ = d7.read_schema()
names = d7.name_table()

AAW = ROOT / ('SharpServer/bin/Debug/AreaServer/Awareness/'
              'tython_blockout-4611686019869492753-1.1.aaw')
data = AAW.read_bytes()
reader, flags, count = d7.read_gom_update(data, 0, 'awareness')
records = [d7.read_object_record(data, reader) for _ in range(count)]

want_node = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1AC68957EB
rec = next(r for r in records if r['node'] == want_node)
structure = schemas[rec['structure_id']]
body = rec['body_start']
end = body + rec['inner_size']
states = cv.field_states(data, end, rec['value_end'] - end,
                         len(structure.fields), rec.get('style', 7))

say('node=%#x struct=%d style=%s inner=%d body=%d value_end=%d' % (
    rec['node'], rec['structure_id'], rec['style'], rec['inner_size'],
    body, rec['value_end']))
present = [k for k in range(len(states)) if states[k] == 1]
say('present(%d): %s' % (len(present), present))
say('')
say('body bytes 0..%d:' % rec['inner_size'])
for off in range(0, rec['inner_size'], 16):
    chunk = data[body + off:body + min(off + 16, rec['inner_size'])]
    say('  +%03d  %s' % (off, chunk.hex(' ')))
say('')
say('state bytes: %s' % data[end:rec['value_end']].hex(' '))

walker = cv.ValueWalker(data, body, end, rec.get('style', 7))
say('')
say('field layout under current grammar:')
for index in present:
    field = structure.fields[index]
    begin = walker.pos - body
    kinds = [p.kind for p in field.parts]
    try:
        kind = field.parts[0].kind
        if kind in (7, 8):
            text = cv._sequence(walker, field, 1, names, 0, pairs=(kind == 8))
        else:
            text = walker.part(field.parts[0], names)
    except Exception as exc:                            # noqa: BLE001
        say('  %3d @+%3d k=%s %-28s <ERROR %s>' % (
            index, begin, kinds,
            names.get(field.definition, '?'), exc))
        break
    used = walker.pos - body - begin
    raw = data[body + begin:walker.pos].hex(' ')
    say('  %3d @+%3d len=%-3d k=%s %-28s %s | %s' % (
        index, begin, used, kinds, names.get(field.definition, '?'),
        text, raw))
say('')
say('consumed=%d inner=%d' % (walker.pos - body, rec['inner_size']))

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote %s' % OUT)