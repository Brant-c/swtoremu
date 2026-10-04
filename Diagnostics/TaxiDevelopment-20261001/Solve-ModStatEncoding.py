"""Solve the LookupList entry encoding for modStatComputed/modStatBase (style 8).

Both the vendor (struct 64) and our taxi (struct 66) fail to walk at field 34,
modStatComputed, kinds [Map, Enum, Float]. Every other field in a 90+ field
character schema walks correctly, so this single encoding is the whole blocker
for reconciling any character record to its exact inner_size.

Rather than guess (literal vs halved count, 5- vs 9-byte entries), brute-force
the interpretations that make the walk reconcile to inner_size EXACTLY on the
captured VENDOR record, which is known-good production data. Reconciliation is
the oracle: only the correct interpretation lands on the boundary.

Run: python Diagnostics/TaxiDevelopment-20261001/Solve-ModStatEncoding.py
Writes: modstat-encoding.txt
"""
import importlib.util
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


d7 = load('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
cv = load('cv', ROOT / 'Diagnostics/Decode-CrtValues.py')
schemas, _, _ = d7.read_schema()
names = d7.name_table()
OUT = Path(__file__).resolve().parent / 'modstat-encoding.txt'
lines = []


def say(t=''):
    print(t)
    lines.append(t)


AAW = ROOT / ('SharpServer/bin/Debug/AreaServer/Awareness/'
              'tython_blockout-4611686019869492753-1.1.aaw')


def records(data):
    rd, _, n = d7.read_gom_update(data, 0, 'x')
    return [d7.read_object_record(data, rd) for _ in range(n)]


def packed_at(data, pos, end):
    """Return (value, nextpos) or None."""
    if pos >= end:
        return None
    t = data[pos]
    if t < 0xC0:
        return t, pos + 1
    if not (0xC8 <= t <= 0xCF):
        return None
    c = t - 0xC7
    if pos + 1 + c > end:
        return None
    return int.from_bytes(data[pos + 1:pos + 1 + c], 'big'), pos + 1 + c


# Locate field 34 and field 35 in the vendor by walking with the working walker
# up to the first container (field 34).
data = AAW.read_bytes()
vendor = next(r for r in records(data) if r.get('structure_id') == 64)
s = schemas[64]
body = vendor['body_start']
st_end = body + vendor['inner_size']
st, _ = d7.field_states(data, st_end, vendor['value_end'] - st_end,
                        len(s.fields), vendor.get('style', 7))

w = cv.ValueWalker(data, body, st_end, vendor.get('style', 7))
f34 = f35 = f62 = None
for k in range(len(s.fields)):
    if st[k] != 1:
        continue
    f = s.fields[k]
    nm = names.get(f.definition, '')
    if nm == 'modStatComputed' and f34 is None:
        f34 = (k, w.pos)
        break
    if f.parts[0].kind in (7, 8):
        cv._sequence(w, f, 1, names, 0, pairs=(f.parts[0].kind == 8))
    else:
        w.part(f.parts[0], names)

k34, p34 = f34
say('VENDOR struct 64: inner_size=%d  field 34 modStatComputed starts at body+%d'
    % (vendor['inner_size'], p34 - body))
say('  raw from there: %s'
    % data[p34:p34 + 48].hex(' '))
say('  parts: %s' % [(p.kind, p.definition) for p in s.fields[k34].parts])
say('')

# Field 34 spans from p34 up to the start of field 35. Find where field 35
# begins by locating its (empty) map: after field 34's entries, the next bytes
# are field 35's count. We know field 35 modStatBase renders as an empty map, so
# its count byte should be 0 -> field35 begins at p34 + span34.
# Brute force: try each interpretation, walk all remaining fields, require the
# walk to land exactly on st_end.

def _prt(data, pos, end, part, names):
    w = cv.ValueWalker(data, pos, end, 7)
    return w.part_end(part, names)


def _seq(data, pos, end, field, names, style):
    w = cv.ValueWalker(data, pos, end, style)
    return w.sequence_end(field, 1, names, 0, pairs=(field.parts[0].kind == 8))


def walk_from(start, modstat_span_fn):
    """Walk every present field from `start`, using modstat_span_fn for field 34."""
    pos = start
    try:
        for k in range(k34, len(s.fields)):
            if st[k] != 1:
                continue
            f = s.fields[k]
            if k == k34:
                nxt = modstat_span_fn()
                if nxt is None or nxt <= pos or nxt > st_end:
                    return None
                pos = nxt
                continue
            if f.parts[0].kind in (7, 8):
                nxt = _seq(data, pos, st_end, f, names, vendor.get('style', 7))
            else:
                nxt = _prt(data, pos, st_end, f.parts[0], names)
            if nxt is None or nxt <= pos:
                return None
            pos = nxt
        return pos
    except Exception:
        return None


best = []
for count_mode in ('literal', 'half', 'half_minus1'):
    for entry_bytes in (5, 6, 9, 10):
        cnt = data[p34]
        entries = {'literal': cnt, 'half': cnt >> 1, 'half_minus1': (cnt >> 1) - 1}[count_mode]
        # entries are (packed int) + (4-byte float); if the key is always a single
        # byte literal the cost is 1+4 = 5, else the packed key may be wider.
        for key_w in (1, 2):
            span = 1 + entries * (key_w + 4)
            end34 = p34 + span
            if end34 > st_end:
                continue

            def mk(end34=end34):
                return end34

            final = walk_from(p34, mk)
            if final == st_end:
                best.append((count_mode, entries, key_w, span, end34 - p34))
                say('RECONCILES: count=%s(%d) keybytes=%d  span=%d -> lands exactly on inner_size'
                    % (count_mode, entries, key_w, span))
if best:
    say('')
    say('solutions found: %d' % len(best))
else:
    say('no simple (count,entry-size) combination reconciled; the map likely')
    say('carries a per-entry structure the walker must read, not a fixed size.')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote %s' % OUT)