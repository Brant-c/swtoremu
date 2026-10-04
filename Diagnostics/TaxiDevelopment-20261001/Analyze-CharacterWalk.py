"""Offline census of every character record in the captured awareness set.

This is the reconnaissance step for resolving field widths empirically. It does
NOT guess: it reports, for each record, the declared inner_size and where the
existing walker diverges from it, so the width search that follows has a fixed
target list.

Run: python Diagnostics/TaxiDevelopment-20261001/Analyze-CharacterWalk.py
Writes: _characterwalk_census.txt next to this file (stdout is also printed).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / '_characterwalk_census.txt'
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

say('update flags=0x%02X objects=%d bytes=%d' % (flags, count, len(data)))
say('')
say('idx  node               flags cls  tmpl                parent              '
    'struct style inner  body_start')
for i, r in enumerate(records):
    say('%3d  %#018x 0x%02X %3s  0x%-16X %#018x  %4s  %5s %5s  %6s' % (
        i, r['node'], r['flags'],
        r['class_id'] if r['class_id'] else '-',
        r['template_id'], r['parent_id'],
        r['structure_id'] if r['structure_id'] is not None else '-',
        r['style'] if r['style'] is not None else '-',
        r['inner_size'] if r['inner_size'] is not None else '-',
        r['body_start'] if r['body_start'] is not None else '-'))
say('')
say('end=0x%X of 0x%X' % (reader.pos, len(data)))

# Character-ish structures: everything derived from chrNonPlayerCharacter.
for i, r in enumerate(records):
    if r['structure_id'] in (64, 66):
        structure = schemas[r['structure_id']]
        body = r['body_start']
        end = body + r['inner_size']
        states = cv.field_states(data, end, r['value_end'] - end,
                                 len(structure.fields), r.get('style', 7))
        present = [k for k in range(len(states)) if states[k] == 1]
        say('')
        say('=== rec %d node=%#x struct=%d style=%s inner=%d present=%d/%d' % (
            i, r['node'], r['structure_id'], r['style'], r['inner_size'],
            len(present), len(states)))
        try:
            rows, summary, ok = cv.walk_record(data, r, structure, names)
        except Exception as exc:                       # noqa: BLE001
            say('    walk raised: %r' % (exc,))
            continue
        say('    -> %s  %s' % (summary, 'OK' if ok else 'MISMATCH'))
        for index, name, text in rows:
            kinds = [p.kind for p in structure.fields[index].parts]
            flag = '' if 'bytes consumed' in text or '<' not in text else ' <<<'
            say('      %3d %-30s k=%s  %s%s' % (
                index, names.get(structure.fields[index].definition, '?'),
                kinds, text, flag))

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote %s' % OUT)