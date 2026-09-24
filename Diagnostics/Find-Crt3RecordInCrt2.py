r'''
Locate CRT3's record inside CRT2 and print the surrounding bytes.

CRT2 (6543 bytes) is the largest single-object fixture and it contains the same
first id that CRT3's 25-byte field payload contains (cf ff 5f 18 4a aa 9e ce),
followed by 0x77 and then further data, where CRT3 stops after 0x77 00 with the
illegal token c0.

Read only. Writes nothing.
'''

import sys
from pathlib import Path

D = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT')
ID1 = bytes.fromhex('cf ff 5f 18 4a aa 9e ce')
CLASS = bytes.fromhex('cf 40 00 01 0e 21 8a 83 9c')
CRT3_PAYLOAD = bytes.fromhex(
    '01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00 '
    'cf 40 00 01 0e 21 8a 83 9c c0'.replace(' ', ''))


def hx(bs):
    return ' '.join('%02x' % x for x in bs)


def occ(buf, pat):
    return [i for i in range(len(buf)) if buf.startswith(pat, i)]


def main():
    b2 = (D / 'tython_blockout-4611686019869492753-1.2.acrt').read_bytes()
    b3 = (D / 'tython_blockout-4611686019869492753-1.3.acrt.disabled').read_bytes()

    print('CRT3 file (%d bytes):' % len(b3))
    print('  ' + hx(b3))
    print('  header[0:30]  = %s' % hx(b3[:30]))
    print('  payload[30:55]= %s' % hx(b3[30:55]))
    print()
    print('CRT2 size %d' % len(b2))
    print('  occurrences of ID1   : %s' % occ(b2, ID1))
    print('  occurrences of CLASS : %s' % occ(b2, CLASS))
    print()

    i = b2.find(ID1)
    lo = max(0, i - 40)
    print('CRT2 window around first ID1 at %d:' % i)
    w = b2[lo:lo + 220]
    for k in range(0, len(w), 20):
        print('   +%-6d %s' % (lo + k, hx(w[k:k + 20])))
    print()
    print('  as text, printable runs in that window:')
    run = ''
    for ch in w:
        run += chr(ch) if 32 <= ch < 127 else '.'
    print('   ' + run)
    print()

    j = b2.find(CLASS)
    print('CRT2 window around first CLASS at %d:' % j)
    w2 = b2[max(0, j - 40):max(0, j - 40) + 120]
    for k in range(0, len(w2), 20):
        print('   +%-6d %s' % (max(0, j - 40) + k, hx(w2[k:k + 20])))


if __name__ == '__main__':
    sys.exit(main())