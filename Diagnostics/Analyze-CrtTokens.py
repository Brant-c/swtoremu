'''
Token-level validation of every tython CRT fixture payload.

Grammar
-------
Mirrors SWTORParser/Hero/PackedStream.cs, Read(out UInt64), the
TransportVersion > 1 branch (PackedStream2 always sets TransportVersion = 5):

    b = next byte
    if b <  192          -> literal value b            (1 byte total)
    elif b <  200        -> INVALID token
    elif b <= 207        -> n = b - 199 (1..8)
                            followed by n little-endian payload bytes
    else                 -> INVALID token

So 192..199 and 208..255 can never appear as a leading token byte.

For each fixture this script finds every header length whose remainder
parses cleanly to the very end, then reports the cleanest one. A payload
that has no clean header length is malformed under this grammar.

Read only: nothing is written.
'''

import re
import sys
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
FIXED_PREFIX = 'tython_blockout-4611686019869492753-1.'
HEADER_RANGE = range(8, 41)


def fixtures():
    out = []
    for p in CRT_DIR.glob('*.acrt*'):
        m = re.search(r'-1\.(\d+)\.acrt(\.disabled)?$', p.name)
        if not m:
            continue
        out.append((int(m.group(1)), p, bool(m.group(2))))
    out.sort(key=lambda t: t[0])
    return out


def parse(data, start):
    '''Walk the token grammar from start. Returns (ok, end, error_index, token_count).'''
    i = start
    n = len(data)
    tokens = 0
    while i < n:
        b = data[i]
        i += 1
        tokens += 1
        if b >= 192:
            if b < 200 or b > 207:
                return False, i - 1, i - 1, tokens
            need = b - 199
            if i + need > n:
                return False, i, i, tokens          # truncated mid-token
            i += need
    return True, i, None, tokens


def describe(data, start):
    parts = []
    i = start
    n = len(data)
    while i < n and len(parts) < 14:
        b = data[i]
        s = i
        i += 1
        if b >= 192:
            if b < 200 or b > 207:
                parts.append('%02x@%d<INVALID>' % (b, s))
                break
            need = b - 199
            chunk = data[i:i + need]
            i += need
            parts.append('%02x:%s' % (b, chunk.hex()))
        else:
            parts.append('%02x' % b)
    tail = ' ...' if i < n else ''
    return ' '.join(parts) + tail


def main():
    rows = []
    for idx, path, disabled in fixtures():
        b = path.read_bytes()
        clean = []
        for h in HEADER_RANGE:
            if h >= len(b):
                break
            ok, end, err, toks = parse(b, h)
            if ok and end == len(b):
                clean.append((h, toks))
        rows.append((idx, disabled, len(b), clean, b))

    print('%-4s %-8s %-6s %s' % ('CRT', 'state', 'size', 'clean header length (tokens)'))
    print('-' * 78)
    bad = []
    for idx, disabled, size, clean, b in rows:
        state = 'DISABLED' if disabled else 'active'
        if clean:
            desc = ', '.join('hdr=%d (%d tokens)' % (h, t) for h, t in clean)
        else:
            desc = '*** NO CLEAN PARSE AT ANY HEADER LENGTH ***'
            bad.append(idx)
        print('%-4d %-8s %-6d %s' % (idx, state, size, desc))

    print('\n=== detail for the fixtures with no clean parse ===')
    for idx, disabled, size, clean, b in rows:
        if clean:
            continue
        print('\nCRT%d (%d bytes, %s)' % (idx, size, 'disabled' if disabled else 'active'))
        for h in HEADER_RANGE:
            if h >= len(b):
                break
            ok, end, err, toks = parse(b, h)
            if not ok:
                print('  hdr=%-3d parsed %d tokens, stops at offset %d (byte %02x), '
                      'consumed %d of %d' % (h, toks - 1, err, b[err], err, len(b)))
        print('  first 40 bytes: %s' % b[:40].hex(' '))
        print('  last  16 bytes: %s' % b[-16:].hex(' '))
        print('  layout from hdr=30: %s' % describe(b, 30))

    print('\n=== malformed fixtures: %s ===' % (bad if bad else 'none'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
