'''
Decode the header layout of every tython CRT fixture and test whether the
declared payload length is authoritative (file_size == header + declared).

Established context:
  CRT3 (55 B) and CRT12 (26 B) are extreme outliers; siblings are 621-736 B.
  The client throws G::SerializationException on CRT3's payload because its
  FINAL byte 0xc0 (=192) is an invalid token under TransportVersion>1, which
  only permits literals 0..191 and packed tokens 200..207.

This script is read only.
'''

import re
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
GLOB = 'tython_blockout-4611686019869492753-1.*'


def idx(name):
    return int(re.search(r'-1\.(\d+)', name).group(1))


def collect():
    out = []
    for p in CRT_DIR.glob(GLOB):
        out.append((idx(p.name), p))
    out.sort(key=lambda t: t[0])
    return out


def token_scan(payload):
    '''Walk the packed-token grammar. TV>1: 0..191 literal, 200..207 packed, else invalid.'''
    i = 0
    n = 0
    while i < len(payload):
        b = payload[i]
        if b < 192:
            i += 1
        elif 200 <= b <= 207:
            i += 1 + (b - 199)
        else:
            return n, i, b
        n += 1
    return n, i, None


def main():
    print('%-5s %-7s %-40s %s' % ('CRT', 'size', 'first 30 bytes', 'payload'))
    for n, p in collect():
        b = p.read_bytes()
        head = ' '.join('%02x' % x for x in b[:30])
        # length field is at offset 29 for the 30-byte header shape
        decl = b[29] if len(b) > 29 else None
        if decl is not None and 30 + decl == len(b):
            verdict = 'declared=%d MATCHES file (30+%d=%d)' % (decl, decl, len(b))
        else:
            verdict = 'declared=%s file=%d' % (decl, len(b))
        print('%-5d %-7d %-40s %s' % (n, len(b), head, verdict))

    print('\n=== token walk of each payload (TV>1 grammar) ===')
    for n, p in collect():
        b = p.read_bytes()
        if len(b) <= 30:
            print('  CRT%-3d payload=%d bytes -> %s' % (n, len(b) - 30, 'EMPTY / NO PAYLOAD'))
            continue
        payload = b[30:]
        count, consumed, bad = token_scan(payload)
        if bad is None:
            print('  CRT%-3d payload=%-5d tokens=%-4d consumed=%-5d OK (clean end)'
                  % (n, len(payload), count, consumed))
        else:
            print('  CRT%-3d payload=%-5d tokens=%-4d consumed=%-5d INVALID TOKEN 0x%02x at payload offset %d'
                  % (n, len(payload), count, consumed, bad, consumed))

    print('\n=== the two outliers in full ===')
    for n, p in collect():
        b = p.read_bytes()
        if n in (3, 12):
            print('  CRT%d (%d bytes): %s' % (n, len(b), ' '.join('%02x' % x for x in b)))


if __name__ == '__main__':
    main()