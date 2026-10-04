import sys, struct, re

def read_packed(buf, i):
    b = buf[i]
    if b < 0xC0:
        return b, i + 1
    ln = b - 0xC7
    v = 0
    for k in range(ln):
        v = (v << 8) | buf[i + 1 + k]
    return v, i + 1 + ln

names = {}
xml = open(sys.argv[2], encoding='utf-8', errors='replace').read()
for m in re.finditer(r'<gom_type id="(\d+)" name="([^"]+)"', xml):
    names[int(m.group(1))] = m.group(2)

def nm(cid): return names.get(cid, '???')

targets = {int(x, 16) for x in sys.argv[3:]}

path = sys.argv[1]
buf = open(path, 'rb').read()
count = struct.unpack('<I', buf[4:8])[0]
i = 8
_, i = read_packed(buf, i)
schema_end = 8 + count
while i < schema_end:
    cid, i = read_packed(buf, i)
    base, i = read_packed(buf, i)
    gcnt, i = read_packed(buf, i)
    gloms = []
    for _ in range(gcnt):
        v, i = read_packed(buf, i); gloms.append(v)
    fcnt, i = read_packed(buf, i)
    fields = []
    for _ in range(fcnt):
        x, i = read_packed(buf, i)
        scnt, i = read_packed(buf, i)
        subs = []
        for _ in range(scnt):
            t, i = read_packed(buf, i)
            c, i = read_packed(buf, i)
            cc, i = read_packed(buf, i)
            subs.append((t, c, cc))
        fields.append((x, subs))
    if base in targets:
        print('=== base class 0x%016X (%s)  contract id=%d  gloms=%s ===' % (base, nm(base), cid, ['0x%X' % g for g in gloms]))
        for (x, subs) in fields:
            subdesc = ', '.join('(type=0x%X=%s, cls=0x%X=%s, cid=%d)' % (t, nm(t), c, nm(c), cc) for (t, c, cc) in subs)
            print('  field 0x%016X (%s): %d subs -> %s' % (x, nm(x), len(subs), subdesc))
