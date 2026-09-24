'''
Read-only analysis of the tython CRT (!area client replication transaction)
fixtures against the repository's own Hero token grammar.

Grammar source (authoritative, in-repo):
  Parser/SWTORParser/Hero/PackedStream.cs  -> Read(out UInt64) / Read(out Int64)
  Parser/SWTORParser/Hero/PackedStream2.cs -> TransportVersion = 5
  Parser/SWTORParser/Hero/HeroTypes.cs

For TransportVersion >= 2 the unsigned reader is:

    b = next byte
    if b < 192:  value = b                      # literal, 1 byte
    elif 200 <= b <= 207:                       # packed, (b-199) little-endian bytes
        value = read_u64_le(b - 199)
    else:
        throw "Invalid token in stream"         # 192..199 and 208..255 are invalid

So 0xC0 (192) is an invalid token under transport version 5.

Nothing is written by this script.
'''

import re
import sys
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
GLOB = 'tython_blockout-4611686019869492753-1.*.acrt'

# Fixture layout established earlier:
#   [seq:4][00 00 00 00 00][01 01][7-byte id][9-byte class][00][05 07 19][payload:25]
PAYLOAD_OFFSET = 31
NESTED_CLASS = bytes.fromhex('cf 40 00 01 0e 21 8a 83 9c')


def fixtures():
    fs = list(CRT_DIR.glob(GLOB))
    fs.sort(key=lambda p: int(re.search(r'-1\.(\d+)\.acrt$', p.name).group(1)))
    return fs


def index(name):
    return int(re.search(r'-1\.(\d+)\.acrt$', name).group(1))


def read_u64(buf, i):
    '''TransportVersion 5 iteration of Read(out UInt64). Returns (value, next_i).'''
    t = buf[i]
    i += 1
    if t < 192:
        return t, i
    if 200 <= t <= 207:
        n = t - 199
        return int.from_bytes(buf[i:i + n], 'little'), i + n
    raise ValueError('INVALID token 0x%02X (192..199 are invalid)' % t)


def hexs(b):
    return ' '.join('%02x' % x for x in b)


def main():
    fs = fixtures()
    print('fixtures: %d' % len(fs))

    print('\n=== full hex ===')
    for f in fs:
        b = f.read_bytes()
        print('-%-4d len=%-4d %s' % (index(f.name), len(b), hexs(b)))

    print('\n=== bytes 0..10 (header) ===')
    print('%-5s %-24s %-10s %s' % ('idx', 'bytes 0..3', 'u32', 'bytes 4..10'))
    for f in fs:
        b = f.read_bytes()
        print('%-5d %-24s %-10d %s' % (index(f.name), hexs(b[0:4]),
                                       int.from_bytes(b[0:4], 'little'), hexs(b[4:11])))

    print('\n=== token walk of payload (v5 grammar) ===')
    for f in fs:
        b = f.read_bytes()
        pay = b[PAYLOAD_OFFSET:]
        toks, i, err = [], 0, None
        try:
            while i < len(pay):
                v, j = read_u64(pay, i)
                toks.append('%d@%d-%d' % (v, i, j - 1))
                i = j
        except ValueError as e:
            err = 'THROW at offset %d: %s' % (i, e)
        status = 'OK' if err is None else err
        print('-%-4d len=%-3d %s' % (index(f.name), len(pay), status))
        print('        %s' % ' '.join(toks))
        if err:
            print('        byte at throw offset = 0x%02X' % pay[i])

    print('\n=== fixtures containing nested class %s ===' % hexs(NESTED_CLASS))
    for f in fs:
        b = f.read_bytes()
        i = b.find(NESTED_CLASS)
        if i < 0:
            continue
        tail = b[i + len(NESTED_CLASS):]
        print('-%-4d class_at=%-3d after_class(%d bytes): %s'
              % (index(f.name), i, len(tail), hexs(tail)[:120]))


if __name__ == '__main__':
    sys.exit(main())