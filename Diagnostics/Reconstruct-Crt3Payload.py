'''
Characterise the tython CRT3 payload against the other (healthy) fixtures.

Established so far:
  CRT3  payload (25 bytes) = 01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00
                             cf 40 00 01 0e 21 8a 83 9c c0
  Its final 11 bytes are  cf 40 00 01 0e 21 8a 83 9c c0  (a 9-byte class id
  plus one byte), and 15 other fixtures contain that same 9-byte class id.

Tests performed here (read only):
  1. For every fixture, locate the byte string END = 'cf 40 00 01 0e 21 8a 83 9c c0'
     and print what follows it. If a healthy fixture contains END followed by
     more bytes, those bytes are the candidate continuation CRT3 is missing.
  2. Print each fixture's declared payload length and trailing bytes so the
     record shape can be compared.
DISABLED = 'tython_blockout-4611686019869492753-1.3.acrt'
  3. Decode the ASCII runs inside any continuation found (the client stores
     user-visible strings in plain text, e.g. "On Enter").

Nothing is written by this script.
'''

import re
import sys
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
GLOB = 'tython_blockout-4611686019869492753-1.*.acrt'
DISABLED = 'tython_blockout-4611686019869492753-1.3.acrt'
PAYLOAD_OFFSET = 30
CLASS_ID = bytes.fromhex('cf 40 00 01 0e 21 8a 83 9c')
END = CLASS_ID + b'\xc0'


def idx(name):
    return int(re.search(r'-1\.(\d+)\.acrt', name).group(1))


def payload(b):
    '''Field run starting at PAYLOAD_OFFSET, length taken from the byte before it.'''
    if len(b) <= PAYLOAD_OFFSET:
        return b''
    return b[PAYLOAD_OFFSET:PAYLOAD_OFFSET + b[PAYLOAD_OFFSET - 1]]


def hexs(b, limit=None):
    s = ' '.join('%02x' % x for x in b)
    return s if limit is None else s[:limit]


def ascii_runs(b):
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{4,}', b):
        out.append(m.group().decode('ascii'))
    return out


def main():
    disabled = CRT_DIR / DISABLED
    b3 = disabled.read_bytes()
    P3 = payload(b3)
    print('CRT3 payload (%d bytes): %s' % (len(P3), hexs(P3)))
    print('CRT3 payload ends with END(%s) ? %s\n'
          % (hexs(END), P3.endswith(END)))

    pool = []
    for p in CRT_DIR.glob(GLOB):
        n = idx(p.name)
        if n != 3:
            pool.append((n, p.read_bytes()))
    pool.sort(key=lambda t: t[0])

    print('=== declared payload length and last 12 payload bytes per fixture ===')
    for n, b in pool:
        P = payload(b)
        print('  CRT%-3d len=%-5d tail: %s' % (n, len(P), hexs(P[-12:])))
    print()

    print('=== fixtures containing CRT3 tail %s ===' % hexs(END))
    found = []
    for n, b in pool:
        P = payload(b)
        start = 0
        while True:
            i = P.find(END, start)
            if i < 0:
                break
            after = P[i + len(END):i + len(END) + 40]
            print('  CRT%-3d at=%-6d  continuation: %s' % (n, i, hexs(after)))
            runs = ascii_runs(after)
            if runs:
                print('         ascii: %s' % runs)
            found.append((n, i, after))
            start = i + 1
    if not found:
        print('  none - END does not appear in any healthy fixture payload')

    print('\n=== how long does the stream continue after that point per fixture ===')
    for n, i, after in found:
        P = payload(dict(pool)[n])
        print('  CRT%-3d  %d payload bytes follow the class-id+c0'
              % (n, len(P) - (i + len(END))))

    if found:
        best = max(found, key=lambda t: len(payload(dict(pool)[t[0]])) - t[1])
        n, i, after = best
        P = payload(dict(pool)[n])
        cont = P[i + len(END):]
        print('\n=== richest continuation (CRT%d, %d bytes) ===' % (n, len(cont)))
        print(hexs(cont[:200]))
        print('ascii runs:', ascii_runs(cont))


if __name__ == '__main__':
    sys.exit(main())