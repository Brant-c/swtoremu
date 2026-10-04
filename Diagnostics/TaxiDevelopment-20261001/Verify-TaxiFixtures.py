"""Verify our generated taxi fixtures with the now-trusted value grammar.

The captured data walks; that only proves the grammar is right. The question
that matters now is whether OUR record does. Until the walk reconciled no value
in a character record was admissible and no fixture edit was safe. That caveat
is lifted, so this measures the fixtures we actually send.

Reuses the resolved grammar from Solve-TailWidths.py (ref_walk / ref_part) and
reports, per record: whether it walks to exactly inner_size, the full present
field list with offsets and bytes, and the decoded values of the two fields the
taxi's replicated surface consists of.

Run: python Diagnostics/TaxiDevelopment-20261001/Verify-TaxiFixtures.py
Writes: taxi-fixture-verification.txt
"""
import importlib.util
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

TAXI_STRUCTURE = 66
TAX_TERMINAL_SPEC = 0xE000DC42A2436F58     # authored taxTerminalSpec
TAXI_TEMPLATE = 0xE0008B8CC0FAEA1D         # npc.location.tython.taxi.jediretreat_pad1
TAXI_PARENT = 0x1AC688BE1E


def load_fixture(path):
    blob = path.read_bytes()
    reader, _, count = m.d7.read_gom_update(blob, 0, path.name)
    if reader is None:
        return blob, []
    return blob, [m.d7.read_object_record(blob, reader) for _ in range(count)]


def present_fields(rec, structure):
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = m.d7.field_states(blob_of(rec), end, rec['value_end'] - end,
                              len(structure.fields), rec.get('style', 7))
    return [k for k in range(len(st)) if st[k] == 1]


def blob_of(rec):
    return m.data


def walk_fixture(path):
    global m
    blob, recs = load_fixture(path)
    m.data = blob
    m.records = recs
    say('')
    say('=' * 72)
    say('%s  (%d bytes, %d objects)' % (path.name, len(blob), len(recs)))
    say('=' * 72)
    ok_all = True
    for i, rec in enumerate(recs):
        if rec['inner_size'] is None:
            say('  %2d node=%#x  no value body (flags=0x%02X)'
                % (i, rec['node'], rec['flags']))
            continue
        structure = m.schemas.get(rec['structure_id'])
        if structure is None:
            say('  %2d node=%#x  unknown structure %s'
                % (i, rec['node'], rec['structure_id']))
            continue
        m.style_halve = rec.get('style', 7) in (8, 10)
        m.LIST_MODE = 'B'
        body = rec['body_start']
        end = body + rec['inner_size']
        st, _ = m.d7.field_states(blob, end, rec['value_end'] - end,
                                  len(structure.fields), rec.get('style', 7))
        present = [k for k in range(len(st)) if st[k] == 1]
        pos = body
        good = True
        say('')
        say('  %2d node=%#x struct=%d (%s) style=%s inner=%d body=%d '
            'value_end=%d states=%dB present=%d/%d' % (
                i, rec['node'], rec['structure_id'],
                m.names.get(structure.base_class, '?'), rec['style'],
                rec['inner_size'], body, rec['value_end'],
                rec['value_end'] - end, len(present), len(structure.fields)))
        if rec['template_id']:
            say('       template=%#018X%s' % (
                rec['template_id'],
                '  == taxi template' if rec['template_id'] == TAXI_TEMPLATE
                else ('  == vendor template' if rec['template_id'] ==
                      0xE0005CB11264F32D else '')))
        if rec['parent_id']:
            say('       parent  =%#018X%s' % (
                rec['parent_id'],
                '  == captured parent' if rec['parent_id'] == TAXI_PARENT else ''))
        for k in present:
            begin = pos
            try:
                pos = m.ref_part(structure.fields[k].parts, 0, pos, end)
            except m.Bad as exc:
                say('       %3d @+%-4d <ERROR %s>' % (k, begin - body, exc))
                good = False
                break
            say('       %3d @+%-4d len=%-4d %-30s | %s' % (
                k, begin - body, pos - begin,
                m.names.get(structure.fields[k].definition, '?'),
                blob[begin:pos].hex(' ')))
        if good:
            delta = pos - end
            verdict = 'RECONCILES %d/%d' % (pos - body, rec['inner_size'])
            if delta:
                verdict += '  MISMATCH delta=%+d' % delta
                ok_all = False
            else:
                ok_all = ok_all and True
            say('       -> %s' % verdict)
        else:
            ok_all = False
    return ok_all


candidates = [
    ROOT / 'SharpServer/AreaServer/TaxiNpc.bin',
    ROOT / 'SharpServer/AreaServer/TaxiRecord1.bin',
    ROOT / 'SharpServer/AreaServer/TaxiClone.bin',
]
# awareness-8.bin / awareness-19.bin are deliberately NOT gated: they predate the
# current GOM framing (their first dword is read as a contract count) and are
# superseded by TaxiNpc.bin, which is the payload actually shipped.
say('Value-grammar verification of generated taxi fixtures')
say('grammar: Solve-TailWidths.py ref_walk / ref_part (LIST_MODE=B)')
allgood = True
for path in candidates:
    if path.exists():
        allgood = walk_fixture(path) and allgood
    else:
        say('')
        say('%s  NOT PRESENT' % path.name)

say('')
say('=' * 72)
say('all records reconcile exactly: %s' % allgood)
(HERE / 'taxi-fixture-verification.txt').write_text('\n'.join(lines),
                                                    encoding='utf-8')
print('\nwrote taxi-fixture-verification.txt')