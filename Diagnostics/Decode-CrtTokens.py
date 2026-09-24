r'''
Walk a CRT fixture payload with the exact token grammar used by the client,
as reimplemented in Parser/SWTORParser/Hero/PackedStream.cs.

Grammar (PackedStream.Read, TransportVersion > 1, i.e. PackedStream2 sets 5):

  unsigned:  b <  192          -> value = b                         (1 byte)
             192 <= b <= 198   -> INVALID TOKEN  (throws)
             199 <= b <= 207   -> 8-bit-packed value, (b-199) bytes follow
             b == 208         -> Int64.MinValue
             b >  208         -> INVALID TOKEN  (throws)

  signed:    b <  192          -> value = b
             193 <= b <= 199   -> negative value, (b-191) bytes follow
             200 <= b <= 207   -> positive value, (b-199) bytes follow
             b == 192         -> negative value, 1 byte must follow
             b == 208         -> Int64.MinValue
             else             -> INVALID TOKEN  (throws)

Reading a byte past the end of the stream returns 0xFF (Stream.ReadByte EOF),
which is itself an invalid token, so an exhausted stream reports the same
failure as a bad token.

Nothing is written by this script.
'''

import sys
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
GLOB = 'tython_blockout-4611686019869492753-1.*.acrt'
PAYLOAD_OFFSET = 30


def load(n):
    p = CRT_DIR / ('tython_blockout-4611686019869492753-1.%d.acrt' % n)
    return p.read_bytes()


def payload(b):
    return b[PAYLOAD_OFFSET:PAYLOAD_OFFSET + b[PAYLOAD_OFFSET - 1]]


def hx(bs):
    return ' '.join('%02x' % x for x in bs)


def classify(b):
    if b < 192:
        return 'value', 0, b
    if b <= 198:
        return 'INVALID', 0, None          # 192..198 illegal for unsigned
    if b <= 207:
        return 'packed', b - 199, None
    if b == 208:
        return 'min', 0, None
    return 'INVALID', 0, None


def signed_classify(b):
    if b < 192:
        return 'value', 0, b
    if b == 192:
        return 'neg-packed', 1, None       # needs 1 byte
    if 193 <= b <= 199:
        return 'neg-packed', b - 191, None
    if 200 <= b <= 207:
        return 'pos-packed', b - 199, None
    if b == 208:
        return 'min', 0, None
    return 'INVALID', 0, None


def walk(label, P):
    print('=== %s : %d payload bytes ===' % (label, len(P)))
    print('    %s' % hx(P))
    i = 0
    step = 0
    while i < len(P):
        b = P[i]
        kind, need, val = classify(b)
        if kind == 'INVALID':
            print('  FAIL at payload offset %d: token 0x%02x (%d) is not a legal '
                  'unsigned token' % (i, b, b))
            print('       remaining bytes at this offset: %d' % (len(P) - i))
            print('       unsigned reading of 0x%02x throws "Invalid token in stream"' % b)
            sk, sn, _ = signed_classify(b)
            print('       signed   reading of 0x%02x is %s, needs %d more byte(s), '
                  'available %d' % (b, sk, sn, len(P) - i - 1))
            return i
        if kind in ('packed', 'neg-packed', 'pos-packed'):
            have = len(P) - i - 1
            if have < need:
                print('  FAIL at payload offset %d: token 0x%02x needs %d packed '
                      'byte(s) but only %d remain (stream exhausted)'
                      % (i, b, need, have))
                print('       this is the EOF case: the next byte read returns 0xFF')
                return i
            raw = P[i + 1:i + 1 + need]
            print('  ok  off %-3d token 0x%02x -> %-10s %d byte(s) = %s'
                  % (i, b, kind, need, hx(raw)))
            i += 1 + need
        else:
            print('  ok  off %-3d token 0x%02x -> %s %s'
                  % (i, b, kind, ('%d' % val) if val is not None else ''))
            i += 1
        step += 1
        if step > 400:
            print('  ... stopped after 400 tokens')
            break
    print('  -> entire payload decoded with no invalid token')
    return None


def main():
    numbers = sorted(int(p.name.split('.')[-2])
                     for p in CRT_DIR.glob(GLOB))
    print('fixtures present: %s\n' % numbers)
    for n in numbers:
        b = load(n)
        P = payload(b)
        if n == 3 or n in (4, 5, 12):
            walk('CRT%d' % n, P)
            print()
    print('=== surface shape: bytes after the 8-byte class id ===')
    for n in numbers:
        P = payload(load(n))
        key = bytes.fromhex('cf 40 00 01 0e 21 8a 83 9c')
        i = P.find(key)
        if i >= 0:
            after = P[i + len(key):i + len(key) + 10]
            print('  CRT%-3d class id at payload+%-5d next bytes: %s'
                  % (n, i, hx(after)))
        else:
            print('  CRT%-3d class id absent' % n)


if __name__ == '__main__':
    sys.exit(main())