"""Per-field width search: find width assignments that walk a record exactly.

Unlike Solve-CharacterWalk.py (which searches a small space of *global* grammar
choices), this walks a single record and, for every present field, enumerates
the plausible byte spans that field could occupy. A DFS over those spans must
land exactly on inner_size; that is the only acceptance test.

The element grammar inside a container is held FIXED (the reading already
verified on the captured modStat maps) so a container's span is a function of
its count and header, not of an exponential product across entries. What varies
per container is only its header (an optional leading packed spec id) and its
count interpretation (literal vs halved).

Run: python Diagnostics/TaxiDevelopment-20261001/Solve-TailWidths.py [node_hex]
Writes: tailwidth-solutions.txt
"""
import importlib.util
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'tailwidth-solutions.txt'
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
data = (ROOT / ('SharpServer/bin/Debug/AreaServer/Awareness/'
                'tython_blockout-4611686019869492753-1.1.aaw')).read_bytes()
reader, _, count = d7.read_gom_update(data, 0, 'awareness')
records = [d7.read_object_record(data, reader) for _ in range(count)]


class Bad(Exception):
    pass


def packed(pos, end):
    if pos >= end:
        raise Bad('eof')
    t = data[pos]
    if t < 0xC0:
        return t, pos + 1
    if not 0xC8 <= t <= 0xCF:
        raise Bad('token 0x%02X@%d' % (t, pos))
    n = t - 0xC7
    if pos + 1 + n > end:
        raise Bad('overrun')
    return int.from_bytes(data[pos + 1:pos + 1 + n], 'big'), pos + 1 + n


def signed(pos, end):
    if pos >= end:
        raise Bad('eof')
    t = data[pos]
    if t < 0xC0:
        return t, pos + 1
    if t == 0xD0:
        return -(1 << 63), pos + 1
    if 0xC0 <= t <= 0xC7:
        n = t - 0xBF
        if pos + 1 + n > end:
            raise Bad('overrun')
        return -int.from_bytes(data[pos + 1:pos + 1 + n], 'big'), pos + 1 + n
    return packed(pos, end)


# --- fixed element grammar (verified on the modStat maps) ---------------
def fixed_part(parts, idx, pos, end, depth=0):
    if depth > 6:
        raise Bad('deep')
    kind = parts[idx].kind
    if kind == 7:
        raw, p = packed(pos, end)
        c = raw >> 1 if style_halve else raw
        for _ in range(c):
            p = fixed_part(parts, idx + 1, p, end, depth + 1)
        return p
    if kind == 8:
        raw, p = packed(pos, end)
        c = raw >> 1 if style_halve else raw
        for _ in range(c):
            p = fixed_part(parts, idx + 1, p, end, depth + 1)
            p = fixed_part(parts, idx + 2, p, end, depth + 1)
        return p
    if kind in (1, 15, 17, 9):
        return packed(pos, end)[1]
    if kind == 2:
        return signed(pos, end)[1]
    if kind == 3:
        return pos
    if kind == 4:
        return pos + 4
    if kind == 5:
        return packed(pos, end)[1]
    if kind == 6:
        n, p = packed(pos, end)
        if n > end - p:
            raise Bad('str')
        return p + n
    if kind == 18:
        return pos + 12
    if kind in (20, 21):
        return signed(pos, end)[1]
    raise Bad('kind %d' % kind)


def elem(parts, idx, pos, end, list_index):
    """Deterministic element span for one container entry."""
    if list_index:
        _, pos = packed(pos, end)          # list entries carry an index
    return fixed_part(parts, idx, pos, end)


def string_entry(pos, end):
    """One entry encoded as 0xD2 + length + bytes (a String enum/key)."""
    if pos >= end or data[pos] != 0xD2:
        raise Bad('not a string entry')
    _, p = packed(pos + 1, end)
    n, p = packed(p, end)
    if n > end - p:
        raise Bad('str entry')
    return p + n


def d2_list_spans(parts, pos, end, max_entries=12):
    """Candidates for a List whose entries are 0xD2-prefixed strings.

    DeserializeLookupList.GetKeyInt/GetKeyString treat a peek of 210 (0xD2) as
    "this key/enum is carried as a string", so a List can be written either as
    plain packed integers or as 0xD2 + length + text. Both shapes are offered to
    the width search rather than assumed.
    """
    out = {}
    for header in (0, 1):               # no count prefix, or a packed count
        p0 = pos
        try:
            if header:
                _, p0 = packed(pos, end)
        except Bad:
            continue
        for c in range(max_entries + 1):
            p = p0
            try:
                for _ in range(c):
                    p = string_entry(p, end)
            except Bad:
                break
            out[('d2', header, c)] = p
    return out


def container_spans(parts, idx, pos, end):
    """Candidate end offsets for a List/Map value starting at `pos`."""
    is_map = parts[idx].kind == 8
    out = {}
    for spec in (False, True):             # optional inherited-list spec id
        p0 = pos
        if spec:
            try:
                _, p0 = packed(p0, end)
            except Bad:
                continue
        try:
            raw, p1 = packed(p0, end)
        except Bad:
            continue
        for mode in ('literal', 'half'):
            c = raw >> 1 if mode == 'half' else raw
            if c > 256:
                continue
            p = p1
            try:
                for _ in range(c):
                    if is_map:
                        p = elem(parts, idx + 1, p, end, False)
                        p = elem(parts, idx + 2, p, end, False)
                    else:
                        p = elem(parts, idx + 1, p, end, True)
            except Bad:
                p = None
            if p is not None:
                out[(spec, mode, c)] = p
    return out


def field_spans(field, pos, end):
    """Candidate end offsets for a whole field value."""
    parts = field.parts
    kind = parts[0].kind
    res = {}
    try:
        if kind in (1, 15, 17, 9):
            res['packed'] = packed(pos, end)[1]
            if kind == 1:
                res['fixed8'] = pos + 8
            if kind == 15:
                res['byte'] = pos + 1
        elif kind == 2:
            res['signed'] = signed(pos, end)[1]
            res['packed'] = packed(pos, end)[1]
            res['fixed8'] = pos + 8
        elif kind == 3:
            res['zero'] = pos
            res['byte'] = pos + 1
        elif kind == 4:
            res['float4'] = pos + 4
        elif kind == 5:
            res['byte'] = pos + 1
            res['packed'] = packed(pos, end)[1]
        elif kind == 6:
            n, p = packed(pos, end)
            res['len_only'] = p
            if n <= end - p:
                res['len_bytes'] = p + n
        elif kind == 18:
            res['vec12'] = pos + 12
        elif kind in (7, 8):
            for key, val in container_spans(parts, 0, pos, end).items():
                res['%s/%s/c%d' % key] = val
            if kind == 7:
                for key, val in d2_list_spans(parts, pos, end).items():
                    res['str%s/c%d' % (key[1:], key[2])] = val
    except Bad:
        pass
    return {k: v for k, v in res.items() if pos < v <= end}


style_halve = True


def solve(rec, structure, label):
    global style_halve
    style_halve = rec.get('style', 7) in (8, 10)
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = d7.field_states(data, end, rec['value_end'] - end,
                            len(structure.fields), rec.get('style', 7))
    present = [k for k in range(len(st)) if st[k] == 1]
    memo = {}

    def dfs(order, pos):
        if order == len(present):
            return [] if pos == end else None
        key = (order, pos)
        if key in memo:
            return memo[key]
        memo[key] = None
        field = structure.fields[present[order]]
        options = field_spans(field, pos, end)
        for how, nxt in sorted(options.items(), key=lambda kv: kv[1]):
            rest = dfs(order + 1, nxt)
            if rest is not None:
                memo[key] = [(present[order], how, pos - body, nxt - pos)] + rest
                return memo[key]
        return None

    say('')
    say('=== %s  node=%#x struct=%d style=%s inner=%d present=%d' % (
        label, rec['node'], rec['structure_id'], rec['style'],
        rec['inner_size'], len(present)))
    result = dfs(0, body)
    if result is None:
        say('    NO width assignment reconciles this record')
        return False
    off = body
    for index, how, rel, width in result:
        name = names.get(structure.fields[index].definition, '?')
        say('    %3d @+%-4d len=%-4d %-30s %-18s | %s' % (
            index, rel, width, name, how, data[off:off + width].hex(' ')))
        off += width
    say('    -> reconciled exactly to %d bytes' % rec['inner_size'])
    return True


def ref_scalar(kind, pos, end):
    if kind == 18:
        if pos + 12 > end:
            raise Bad('vec')
        return pos + 12
    if kind == 4:
        if pos + 4 > end:
            raise Bad('float')
        return pos + 4
    if kind == 3:
        return pos
    if kind in (1, 15, 17, 9):
        return packed(pos, end)[1]
    if kind == 2:
        return signed(pos, end)[1]
    if kind == 5:
        return packed(pos, end)[1]
    if kind == 6:
        if pos < end and data[pos] == 0xD2:      # LookupList string-key marker
            pos += 1
        n, p = packed(pos, end)
        if n > end - p:
            raise Bad('str')
        return p + n
    raise Bad('kind %d' % kind)


LIST_MODE = 'B'


def ref_part(parts, idx, pos, end, depth=0):
    if depth > 6:
        raise Bad('deep')
    kind = parts[idx].kind
    if kind == 8:
        raw, p = packed(pos, end)
        c = raw >> 1 if style_halve else raw
        for _ in range(c):
            p = ref_part(parts, idx + 1, p, end, depth + 1)
            p = ref_part(parts, idx + 2, p, end, depth + 1)
        return p
    if kind == 7:
        if LIST_MODE in ('B', 'C'):
            t = data[pos] if pos < end else 0
            if t == 0xCF:
                _, pos = packed(pos, end)
        raw, p = packed(pos, end)
        c = raw >> 1 if style_halve else raw
        for _ in range(c):
            if LIST_MODE in ('A', 'B'):
                _, p = packed(p, end)              # per-entry index
            p = ref_part(parts, idx + 1, p, end, depth + 1)
        return p
    return ref_scalar(kind, pos, end)


def ref_walk(rec, structure):
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = d7.field_states(data, end, rec['value_end'] - end,
                            len(structure.fields), rec.get('style', 7))
    present = [k for k in range(len(st)) if st[k] == 1]
    pos = body
    for k in present:
        try:
            pos = ref_part(structure.fields[k].parts, 0, pos, end)
        except Bad as exc:
            return False, pos - body, k, str(exc)
    return pos == end, pos - body, None, ''


def report_reference():
    global style_halve, LIST_MODE
    for mode in ('A', 'B', 'C', 'D'):
        LIST_MODE = mode
        ok = 0
        total = 0
        fails = []
        for i, rec in enumerate(records):
            if rec['inner_size'] is None or rec['structure_id'] not in schemas:
                continue
            total += 1
            style_halve = rec.get('style', 7) in (8, 10)
            good, off, field, why = ref_walk(rec, schemas[rec['structure_id']])
            if good:
                ok += 1
            else:
                fails.append((i, rec['structure_id'], off, why))
        say('LIST_MODE=%s: %d/%d reconcile' % (mode, ok, total))
        for i, sid, off, why in fails[:14]:
            say('    rec %2d struct %-3d at +%d %s' % (i, sid, off, why))
    say('')


def print_ref_layout(rec, structure, label):
    global style_halve, LIST_MODE
    LIST_MODE = 'B'
    style_halve = rec.get('style', 7) in (8, 10)
    body = rec['body_start']
    end = body + rec['inner_size']
    st, _ = d7.field_states(data, end, rec['value_end'] - end,
                            len(structure.fields), rec.get('style', 7))
    present = [k for k in range(len(st)) if st[k] == 1]
    say('')
    say('=== resolved layout: %s node=%#x struct=%d style=%s inner=%d' % (
        label, rec['node'], rec['structure_id'], rec['style'],
        rec['inner_size']))
    pos = body
    for k in present:
        begin = pos
        try:
            pos = ref_part(structure.fields[k].parts, 0, pos, end)
        except Bad as exc:
            say('    %3d @+%-4d <ERROR %s>' % (k, begin - body, exc))
            return
        say('    %3d @+%-4d len=%-4d %-30s | %s' % (
            k, begin - body, pos - begin,
            names.get(structure.fields[k].definition, '?'),
            data[begin:pos].hex(' ')))
    say('    consumed %d/%d' % (pos - body, rec['inner_size']))


def main():
    want = int(sys.argv[1], 16) if len(sys.argv) > 1 else None
    report_reference()
    if want is not None:
        rec = next(r for r in records if r['node'] == want)
        print_ref_layout(rec, schemas[rec['structure_id']], 'requested')
        OUT.write_text('\n'.join(lines), encoding='utf-8')
        print('\nwrote %s' % OUT)
        return
    if want is not None:
        rec = next(r for r in records if r['node'] == want)
        solve(rec, schemas[rec['structure_id']], 'requested')
    else:
        done = 0
        total = 0
        for rec in records:
            if rec['inner_size'] is None or rec['structure_id'] not in schemas:
                continue
            total += 1
            if solve(rec, schemas[rec['structure_id']],
                     'struct %d' % rec['structure_id']):
                done += 1
        say('')
        say('records reconciled: %d/%d' % (done, total))

    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('\nwrote %s' % OUT)


if __name__ == '__main__':
    main()