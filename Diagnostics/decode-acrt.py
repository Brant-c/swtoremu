import sys, struct

# Packed unsigned 64: value < 0xC0 -> 1 byte; else 0xC7+len prefix then big-endian.
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
    node_id, i = read_packed(buf, i)
    flags = buf[i]; i += 1
    rec = {'node': node_id, 'flags': flags}
    if flags & 0x80:
        rec['class'], i = read_packed(buf, i)
    if flags & 0x40:
        rec['template'], i = read_packed(buf, i)
    if flags & 0x20:
        rec['parent'], i = read_packed(buf, i)
    if flags & 0x10:
        sub = buf[i]; i += 1
        rec['lists_flags'] = sub
        if sub & 0x01:
            cnt, i = read_packed(buf, i)
            rec['list1'] = cnt
            i += cnt * 8  # uint64 each
        if sub & 0x02:
            cnt, i = read_packed(buf, i)
            rec['list2'] = cnt
            i += cnt * 8
    if flags & 0x08:
        ver, i = read_packed(buf, i)
        fmt, i = read_packed(buf, i)
        cnt, i = read_packed(buf, i)
        rec['field'] = (ver, fmt, cnt)
        rec['field_off'] = i
        i += cnt
    return rec, i

def parse_acrt(path):
    buf = open(path, 'rb').read()
    stream = struct.unpack('<I', buf[0:4])[0]
    schema_count = struct.unpack('<I', buf[4:8])[0]
    i = 8
    print(f'== {path} ({len(buf)} bytes) stream=0x{stream:08X} schema_count={schema_count} ==')
    if schema_count:
        print(f'  (schema of {schema_count} entries not decoded here)')
        return
    flags = buf[i]; i += 1
    if flags & 0x01:
        cnt, i = read_packed(buf, i)
        print(f'  object updates: {cnt}')
        for n in range(cnt):
            try:
                rec, i = parse_object(buf, i)
            except Exception as e:
                print(f'  [ERR at object {n}, offset {i}] {e}')
                break
            parts = [f'node=0x{rec["node"]:016X} flags=0x{rec["flags"]:02X}']
            if 'class' in rec: parts.append(f'class=0x{rec["class"]:016X}')
            if 'template' in rec: parts.append(f'template=0x{rec["template"]:016X}')
            if 'parent' in rec: parts.append(f'parent=0x{rec["parent"]:016X}')
            if 'field' in rec:
                v,f,c = rec['field']
                fd = buf[rec['field_off']:rec['field_off']+c].hex(' ')
                parts.append(f'field=({v},{f},{c}) [{fd}]')
            print('  [%d] %s' % (n, ' '.join(parts)))
    if flags & 0x02:
        cnt, i = read_packed(buf, i)
        print(f'  removed nodes: {cnt}')
        for n in range(cnt):
            v, i = read_packed(buf, i)
            print(f'  remove 0x{v:016X}')
    print(f'  consumed {i}/{len(buf)} bytes')

for p in sys.argv[1:]:
    parse_acrt(p)
