import sys, struct, re
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

# load gom_type_names.xml
names = {}
xml = open(sys.argv[2], encoding='utf-8', errors='replace').read()
for m in re.finditer(r'<gom_type id="(\d+)" name="([^"]+)"', xml):
    names[int(m.group(1))] = m.group(2)

def nm(cid):
    return names.get(cid, '???')

path = sys.argv[1]
buf = open(path, 'rb').read()
count = struct.unpack('<I', buf[4:8])[0]   # byte size of schema block
i = 8
_, i = read_packed(buf, i)  # leading packed value
schema_end = 8 + count
bases = Counter()
n = 0
while i < schema_end:
    cid, i = read_packed(buf, i)
    base, i = read_packed(buf, i)
    gcnt, i = read_packed(buf, i)
    for _ in range(gcnt):
        _, i = read_packed(buf, i)
    fcnt, i = read_packed(buf, i)
    for _ in range(fcnt):
        _, i = read_packed(buf, i)
        scnt, i = read_packed(buf, i)
        for _ in range(scnt):
            _, i = read_packed(buf, i)
            _, i = read_packed(buf, i)
            _, i = read_packed(buf, i)
    bases[base] += 1
    n += 1
print('parsed %d contracts; schema block ends at %d; next byte offset %d' % (n, schema_end, i))
print('--- distinct base class ids with names ---')
for cid, c in sorted(bases.items(), key=lambda kv: -kv[1]):
    print('  0x%016X  %-42s x%d' % (cid, nm(cid), c))
