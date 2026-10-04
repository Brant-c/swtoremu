import sys, struct

def read_packed(buf, i):
    b = buf[i]
    if b < 0xC0:
        return b, i + 1
    ln = b - 0xC7
    v = 0
    for k in range(ln):
        v = (v << 8) | buf[i + 1 + k]
    return v, i + 1 + ln

def parse_object(buf, i):
    node, i = read_packed(buf, i)
    flags = buf[i]; i += 1
    rec = {'node': node, 'flags': flags}
    if flags & 0x80:
        rec['class'], i = read_packed(buf, i)
    if flags & 0x40:
        rec['template'], i = read_packed(buf, i)
    if flags & 0x20:
        rec['parent'], i = read_packed(buf, i)
    if flags & 0x10:
        sub = buf[i]; i += 1
        rec['lists'] = sub
        if sub & 0x01:
            cnt, i = read_packed(buf, i)
            rec['l1'] = [read_packed(buf, i)[0] for _ in range(cnt)][:0] if False else None
            vals = []
            for _ in range(cnt):
                v, i = read_packed(buf, i); vals.append(v)
            rec['l1'] = vals
        if sub & 0x02:
            cnt, i = read_packed(buf, i)
            vals = []
            for _ in range(cnt):
                v, i = read_packed(buf, i); vals.append(v)
            rec['l2'] = vals
    if flags & 0x08:
        ver, i = read_packed(buf, i)
        fmt, i = read_packed(buf, i)
        cnt, i = read_packed(buf, i)
        rec['field'] = (ver, fmt, cnt)
        rec['data'] = buf[i:i+cnt]
        i += cnt
    return rec, i

path = sys.argv[1]
buf = open(path, 'rb').read()
stream = struct.unpack('<I', buf[0:4])[0]
print('== %s (%d bytes) stream=0x%08X ==' % (path, len(buf), stream))
i = 4
flags = buf[i]; i += 1
if flags & 0x01:
    cnt, i = read_packed(buf, i)
    print('objects: %d' % cnt)
    for n in range(cnt):
        rec, i = parse_object(buf, i)
        parts = ['[%d] node=0x%016X flags=0x%02X' % (n, rec['node'], rec['flags'])]
        if 'class' in rec: parts.append('class=0x%016X' % rec['class'])
        if 'template' in rec: parts.append('template=0x%016X' % rec['template'])
        if 'parent' in rec: parts.append('parent=0x%016X' % rec['parent'])
        if 'l1' in rec: parts.append('l1=%s' % ['0x%X' % v for v in rec['l1']])
        if 'l2' in rec: parts.append('l2=%s' % ['0x%X' % v for v in rec['l2']])
        if 'field' in rec:
            v, f, c = rec['field']
            d = rec['data']
            ascii_part = ''.join(chr(x) if 32 <= x < 127 else '.' for x in d)
            parts.append('field=(%d,%d,%d) hex=%s ascii=%r' % (v, f, c, d.hex(' '), ascii_part))
        print('  ' + ' '.join(parts))
if flags & 0x02:
    cnt, i = read_packed(buf, i)
    print('removed: %d' % cnt)
    for n in range(cnt):
        v, i = read_packed(buf, i)
        print('  remove 0x%016X' % v)
print('consumed %d/%d' % (i, len(buf)))
