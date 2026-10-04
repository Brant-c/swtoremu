import sys, struct
from collections import Counter

def read_packed(buf, i):
    b = buf[i]
    if b < 0xC0:
        return b, i + 1
    ln = b - 0xC7
    v = 0
    for k in range(ln):
        v = (v << 8) | buf[i + 1 + k]
    return v, i + 1 + ln

def parse_contract(buf, i):
    cid, i = read_packed(buf, i)
    base, i = read_packed(buf, i)
    gcnt, i = read_packed(buf, i)
    if gcnt > 100000: raise ValueError('glom count huge %d' % gcnt)
    for _ in range(gcnt):
        _, i = read_packed(buf, i)
    fcnt, i = read_packed(buf, i)
    if fcnt > 100000: raise ValueError('field count huge %d' % fcnt)
    nsubs = 0
    for _ in range(fcnt):
        _, i = read_packed(buf, i)
        scnt, i = read_packed(buf, i)
        if scnt > 100000: raise ValueError('sub count huge %d' % scnt)
        for _ in range(scnt):
            _, i = read_packed(buf, i)
            _, i = read_packed(buf, i)
            _, i = read_packed(buf, i)
            nsubs += 1
    return (cid, base, gcnt, fcnt, nsubs), i

path = sys.argv[1]
buf = open(path, 'rb').read()
stream = struct.unpack('<I', buf[0:4])[0]
count = struct.unpack('<I', buf[4:8])[0]
print('file=%s bytes=%d stream=0x%08X contract_count=%d' % (path, len(buf), stream, count))
i = 8
checksum, j = read_packed(buf, i)
print('leading packed (checksum?) = %d (%d bytes)' % (checksum, j - i))
i = j
bases = Counter(); cids = Counter()
total_fields = total_subs = 0
n = 0
err = None
for n in range(count):
    try:
        (cid, base, gcnt, fcnt, nsubs), i = parse_contract(buf, i)
    except Exception as e:
        err = (n, i, str(e)); break
    bases[base] += 1; cids[cid] += 1
    total_fields += fcnt; total_subs += nsubs
print('parsed %d contracts, consumed %d/%d bytes' % (n, i, len(buf)))
if err: print('ERR at contract %d offset %d: %s' % err)
print('distinct base class ids: %d; distinct contract ids: %d; fields=%d subs=%d' % (len(bases), len(cids), total_fields, total_subs))
print('--- top 60 base class ids ---')
for cid, c in bases.most_common(60):
    print('  0x%016X x%d' % (cid, c))
print('--- tail (should be flags+objects) ---')
print('  ' + buf[i:i+24].hex(' '))
