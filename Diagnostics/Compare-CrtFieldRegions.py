r'''
Compare the field region that follows the shared 8-byte class id across all
tython CRT fixtures, to establish which continuation is normal and whether
CRT3's is anomalous.

Read only. Writes nothing.
'''

import sys
from pathlib import Path

CRT_DIR = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
GLOB = 'tython_blockout-4611686019869492753-1.*.acrt'

CLASS_ID = bytes.fromhex('cf 40 00 01 0e 21 8a 83 9c')
CRT3_ID1 = bytes.fromhex('cf ff 5f 18 4a aa 9e ce')
CRT3_SEG = bytes.fromhex(
    '05 07 19 01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00 '
    'cf 40 00 01 0e 21 8a 83 9c c0'.replace(' ', ''))
CRT3_PAYLOAD = bytes.fromhex(
    '01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00 '
    'cf 40 00 01 0e 21 8a 83 9c c0'.replace(' ', ''))


def hx(bs):
    return ' '.join('%02x' % x for x in bs)


def files():
    out = []
    for p in CRT_DIR.glob(GLOB):
        out.append((int(p.name.split('.')[-2]), p))
    return sorted(out)


def main():
    print('=== bytes following the shared class id, per fixture ===')
    for n, p in files():
        d = p.read_bytes()
        i = d.find(CLASS_ID)
        if i < 0:
            print('  CRT%-3d (len %-6d) class id ABSENT' % (n, len(d)))
            continue
        after = d[i + len(CLASS_ID):i + len(CLASS_ID) + 18]
        print('  CRT%-3d (len %-6d) after class id: %s' % (n, len(d), hx(after)))

    print('\n=== leading byte before the class id, per fixture ===')
    for n, p in files():
        d = p.read_bytes()
        i = d.find(CLASS_ID)
        if i < 0:
            continue
        print('  CRT%-3d before(%d): %s' % (n, 2, hx(d[max(0, i - 2):i])))

    print('\n=== does any other fixture contain CRT3 first id %s ? ==='
          % hx(CRT3_ID1))
    found = False
    for n, p in files():
        d = p.read_bytes()
        j = d.find(CRT3_ID1)
        if j >= 0:
            found = True
            print('  CRT%-3d at offset %-6d  context: %s'
                  % (n, j, hx(d[j:j + 30])))
    if not found:
        print('  no other fixture contains it')

    print('\n=== does the exact CRT3 25-byte field payload appear anywhere else? ===')
    found = False
    for n, p in files():
        d = p.read_bytes()
        j = d.find(CRT3_PAYLOAD)
        if j >= 0:
            found = True
            print('  CRT%-3d at offset %d' % (n, j))
    if not found:
        print('  nowhere else')

    print('\n=== where the [xx][yy][len] field header appears, per fixture ===')
    for n, p in files():
        d = p.read_bytes()
        hits = []
        for off in range(4, min(len(d) - 3, 400)):
            if d[off - 1] == 0x19 or True:
                pass
        # look for the literal CRT3 field header 05 07 19
        j = d.find(bytes.fromhex('05 07 19'))
        if j >= 0:
            print('  CRT%-3d contains 05 07 19 at offset %d ; field bytes: %s'
                  % (n, j, hx(d[j + 3:j + 3 + 25])))
        else:
            print('  CRT%-3d no 05 07 19 header' % n)


if __name__ == '__main__':
    sys.exit(main())