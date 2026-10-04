"""Resolve character-record field widths empirically, with inner_size as oracle.

A field's encoding is a property of its TYPE, not of one occurrence, so the
search is over a small set of *global* grammar assignments rather than a
per-field width guess. Each assignment is walked deterministically against every
captured record; the winner is the one that consumes exactly inner_size for all
of them. That is the only criterion used here.

Confirmed by hand against the captured vendor (node 0x1AC68957EB, struct 64,
style 8, inner_size 380) before writing this:
  * present Boolean carries ZERO value bytes (f30 then makes f33 start on the
    6-byte ref cc 1a c6 89 57 ec, which is the only reading that keeps the
    record aligned);
  * an Enum value is a PACKED integer, variable width (map keys 232/233/254/255
    use a 0xC8 + 1 payload form), not a fixed byte;
  * a style-8 container count is the packed value halved (0x3E -> 31 entries for
    modStatComputed, landing exactly on the next field's count byte).

Run: python Diagnostics/TaxiDevelopment-20261001/Solve-CharacterWalk.py
Writes: characterwalk-solutions.txt
"""
import importlib.util
import itertools
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'characterwalk-solutions.txt'
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


class Bail(Exception):
    pass


class Grammar:
    """Deterministic value walker driven by one global grammar assignment."""

    def __init__(self, cfg):
        self.cfg = cfg

    def _packed(self, pos, end):
        if pos >= end:
            raise Bail('eof packed')
        t = data[pos]
        if t < 0xC0:
            return t, pos + 1
        if not 0xC8 <= t <= 0xCF:
            raise Bail('bad packed 0x%02X@%d' % (t, pos))
        n = t - 0xC7
        if pos + 1 + n > end:
            raise Bail('packed overrun')
        return int.from_bytes(data[pos + 1:pos + 1 + n], 'big'), pos + 1 + n

    def _signed(self, pos, end):
        if pos >= end:
            raise Bail('eof signed')
        t = data[pos]
        if t < 0xC0:
            return t, pos + 1
        if t == 0xD0:
            return -(1 << 63), pos + 1
        if 0xC0 <= t <= 0xC7:
            n = t - 0xBF
            if pos + 1 + n > end:
                raise Bail('signed overrun')
            return -int.from_bytes(data[pos + 1:pos + 1 + n], 'big'), pos + 1 + n
        return self._packed(pos, end)

    def scalar(self, kind, pos, end, which):
        """Consume one scalar of `kind`; return (value, nextpos)."""
        if kind == 18:                              # Vec3
            if pos + 12 > end:
                raise Bail('vec3 overrun')
            return struct.unpack('<3f', data[pos:pos + 12]), pos + 12
        if kind == 4:                               # Float
            if pos + 4 > end:
                raise Bail('float overrun')
            return struct.unpack('<f', data[pos:pos + 4])[0], pos + 4
        if kind == 3:                               # Boolean
            if self.cfg['bool'] == 'byte':
                if pos >= end:
                    raise Bail('bool eof')
                return data[pos], pos + 1
            return None, pos
        if kind == 15:                              # ClassRef
            if self.cfg['ref'] == 'byte':
                if pos >= end:
                    raise Bail('ref eof')
                return data[pos], pos + 1
            return self._packed(pos, end)
        if kind == 1:                               # UInt64
            if self.cfg['u64'] == 'fixed8':
                if pos + 8 > end:
                    raise Bail('u64 overrun')
                return int.from_bytes(data[pos:pos + 8], 'big'), pos + 8
            return self._packed(pos, end)
        if kind == 2:                               # Int64
            mode = self.cfg['i64']
            if mode == 'fixed8':
                if pos + 8 > end:
                    raise Bail('i64 overrun')
                return int.from_bytes(data[pos:pos + 8], 'big'), pos + 8
            if mode == 'signed':
                return self._signed(pos, end)
            return self._packed(pos, end)
        if kind == 5:                               # Enum
            if self.cfg['enum'] == 'byte':
                if pos >= end:
                    raise Bail('enum eof')
                return data[pos], pos + 1
            return self._packed(pos, end)
        if kind == 6:                               # String
            mode = self.cfg['str']
            n, p = self._packed(pos, end)
            if mode == 'len_only':
                return n, p
            if mode == 'fixed4_bytes':
                if p + 4 > end:
                    raise Bail('str overrun')
                n = int.from_bytes(data[p:p + 4], 'little')
                p += 4
            if n > end - p:
                raise Bail('str len overrun')
            return n, p + n
        if kind == 17:                              # Timer
            if self.cfg['timer'] == 'fixed4':
                if pos + 4 > end:
                    raise Bail('timer overrun')
                return int.from_bytes(data[pos:pos + 4], 'little'), pos + 4
            return self._packed(pos, end)
        if kind in (20, 21):                        # TimeSpan / Time
            return self.scalar(2, pos, end, which)
        if kind == 9:                               # EmbeddedClass: packed box
            return self._packed(pos, end)
        if kind == 0:
            return None, pos
        raise Bail('unhandled kind %d (%s)' % (kind, which))

    def part(self, parts, index, pos, end, style, depth=0):
        if depth > 6:
            raise Bail('deep')
        kind = parts[index].kind
        if kind == 7:
            raw, p = self._packed(pos, end)
            c = raw >> 1 if self._halve(style, 7) else raw
            if c > 4096:
                raise Bail('count %d' % c)
            for _ in range(c):
                _, p = self.part(parts, index + 1, p, end, style, depth + 1)
            return None, p
        if kind == 8:
            raw, p = self._packed(pos, end)
            c = raw >> 1 if self._halve(style, 8) else raw
            if c > 4096:
                raise Bail('count %d' % c)
            for _ in range(c):
                _, p = self.part(parts, index + 1, p, end, style, depth + 1)
                _, p = self.part(parts, index + 2, p, end, style, depth + 1)
            return None, p
        return self.scalar(kind, pos, end, names.get(parts[index].definition, ''))

    def _halve(self, style, kind):
        """Whether this container's count is the packed value halved.

        This is the SerializeLookupList/SerializeList rule: only styles 8 and 10
        double the count, so only those halve on read. Style 7 records (the
        container children) carry the count literally, which is why the captured
        effContainer at struct13 walks 33/33 today.
        """
        if style in (8, 10):
            return self.cfg['cnt_map' if kind == 8 else 'cnt_list'] == 'half'
        return False

    def field(self, field, pos, end, style):
        return self.part(field.parts, 0, pos, end, style)[1]
BOOL = {'zero', 'byte'}
U64 = {'packed', 'fixed8'}
I64 = {'signed', 'unsigned', 'fixed8'}
ENUM = {'packed', 'byte'}
STR = {'len_bytes', 'len_only', 'fixed4_bytes'}
REF = {'packed', 'byte'}
TIMER = {'packed', 'fixed4'}
STATES = {'one', 'zero_or_one'}


def states_for(rec, structure, mode):
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = d7.field_states(data, end, rec['value_end'] - end,
                            len(structure.fields), rec.get('style', 7))
    if mode == 'one':
        return [k for k in range(len(st)) if st[k] == 1]
    return [k for k in range(len(st)) if st[k] in (0, 1)]


def trace(cfg, rec, structure, label):
    """Print each present field's span under `cfg`, for one record."""
    g = Grammar(cfg)
    body = rec['body_start']
    end = body + rec['inner_size']
    say('')
    say('--- trace %s  node=%#x struct=%d style=%s inner=%d' % (
        label, rec['node'], rec['structure_id'], rec['style'],
        rec['inner_size']))
    pos = body
    for k in states_for(rec, structure, cfg['states']):
        begin = pos
        try:
            pos = g.field(structure.fields[k], pos, end, rec.get('style', 7))
        except Exception as exc:                        # noqa: BLE001
            say('  %3d @+%d %-30s k=%s <ERROR %s>' % (
                k, begin - body, names.get(structure.fields[k].definition, '?'),
                [p.kind for p in structure.fields[k].parts], exc))
            return
        say('  %3d @+%-4d len=%-4d %-30s k=%s | %s' % (
            k, begin - body, pos - begin,
            names.get(structure.fields[k].definition, '?'),
            [p.kind for p in structure.fields[k].parts],
            data[begin:pos].hex(' ')))


def diagnose(cfg, rec, structure):
    """Walk one record; return (ok, pos-offset, failing field index, reason)."""
    g = Grammar(cfg)
    body = rec['body_start']
    end = body + rec['inner_size']
    present = states_for(rec, structure, cfg['states'])
    pos = body
    for order, k in enumerate(present):
        try:
            pos = g.field(structure.fields[k], pos, end, rec.get('style', 7))
        except Bail as exc:
            return False, pos - body, k, 'field %d (%s): %s' % (
                k, names.get(structure.fields[k].definition, '?'), exc)
        except Exception as exc:                        # noqa: BLE001
            return False, pos - body, k, 'field %d: %r' % (k, exc)
    if pos == end:
        return True, pos - body, None, ''
    return False, pos - body, None, 'over/under by %d' % (pos - end)


def evaluate(cfg, rec, structure):
    try:
        return diagnose(cfg, rec, structure)[0]
    except Exception:                                   # noqa: BLE001
        return False


targets = [(i, r) for i, r in enumerate(records)
           if r['inner_size'] is not None and r['structure_id'] in schemas]
say('records with a value body: %d' % len(targets))
say('structures: %s' % sorted({r['structure_id'] for _, r in targets}))

axes = list(itertools.product(
    sorted(BOOL), sorted(U64), sorted(I64), sorted(ENUM), sorted(STR),
    sorted(REF), sorted(TIMER), ('half', 'literal'), ('half', 'literal'),
    sorted(STATES)))
say('grammar assignments to test: %d' % len(axes))

results = []
for (b, u, i, e, s, rf, t, cm, cl, st) in axes:
    cfg = {'bool': b, 'u64': u, 'i64': i, 'enum': e, 'str': s, 'ref': rf,
           'timer': t, 'cnt_map': cm, 'cnt_list': cl, 'states': st}
    ok = 0
    fails = []
    for idx, rec in targets:
        if evaluate(cfg, rec, schemas[rec['structure_id']]):
            ok += 1
        else:
            fails.append(idx)
    results.append((ok, cfg, fails))

results.sort(key=lambda row: -row[0])
top = results[0][0]
say('')
say('best reconciliation: %d/%d records' % (top, len(targets)))
tied = [row for row in results if row[0] == top]
for ok, cfg, fails in tied[:15]:
    say('  %d/%d  %s' % (ok, len(targets), cfg))
    say('       first failures: %s' % fails[:24])
say('')
say('assignments tied at the best score: %d' % len(tied))
if len(tied) > 1:
    say('NOTE: still ambiguous; needs a second record family to break the tie.')

# The hand-verified reading of the vendor record fixes enum=packed and
# cnt_map=half (0x3E -> 31 entries, landing exactly on the next count byte) and
# bool=zero (f30 then puts f33 on the 6-byte ref cc 1a c6 89 57 ec). Diagnose
# that specific reading rather than the alphabetically-first tie.
REFERENCE = {'bool': 'zero', 'u64': 'packed', 'i64': 'signed', 'enum': 'packed',
             'str': 'len_bytes', 'ref': 'packed', 'timer': 'packed',
             'cnt_map': 'half', 'cnt_list': 'literal', 'states': 'one'}
say('')
say('pass counts by structure under the reference reading:')
by_struct = {}
for idx, rec in targets:
    ok = evaluate(REFERENCE, rec, schemas[rec['structure_id']])
    key = rec['structure_id']
    good, bad = by_struct.get(key, (0, 0))
    by_struct[key] = (good + (1 if ok else 0), bad + (0 if ok else 1))
for key in sorted(by_struct):
    good, bad = by_struct[key]
    say('  struct %-3d  %d pass  %d fail' % (key, good, bad))

say('')
say('detail under the reference reading:')
say('  %s' % REFERENCE)
for idx, rec in targets:
    ok, off, field, reason = diagnose(REFERENCE, rec, schemas[rec['structure_id']])
    if not ok:
        say('  rec %2d node=%#x struct=%d style=%s inner=%d -> at +%d %s' % (
            idx, rec['node'], rec['structure_id'], rec['style'],
            rec['inner_size'], off, reason))
        body = rec['body_start']
        lo = max(0, off - 16)
        chunk = data[body + lo:body + min(rec['inner_size'], off + 16)]
        say('      bytes +%d..%d: %s' % (lo, off + 16, chunk.hex(' ')))

for idx, label in ((4, 'effContainer child (struct 13)'),
                   (8, 'eqpContainer child (struct 14)'),
                   (3, 'rendering NPC (struct 42)'),
                   (16, 'vendor (struct 64)'),
                   (13, 'large record (struct 48)')):
    rec = records[idx]
    trace(REFERENCE, rec, schemas[rec['structure_id']], label)

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote %s' % OUT)