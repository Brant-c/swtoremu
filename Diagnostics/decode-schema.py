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

def parse_contract(buf, i):
    cid, i = read_packed(buf, i)
    base, i = read_packed(buf, i)
    gcnt, i = read_packed(buf, i)
    gloms = []
    for _ in range(gcnt):
        v, i = read_packed(buf, i)
        gloms.append(v)
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
    return (cid, base, gloms, fields), i

path = sys.argv[1]
buf = open(path, 'rb').read()
stream = struct.unpack('<I', buf[0:4])[0]
count = struct.unpack('<I', buf[4:8])[0]
print(f'file={path} bytes={len(buf)} stream=0x{stream:08X} contract_count={count}')
i = 8
# Try: a single leading packed checksum, then the contracts
checksum, j = read_packed(buf, i)
print(f'leading packed value at offset 8 = {checksum} (consumed {j-i} bytes)')
i = j
for n in range(count):
    try:
        (cid, base, gloms, fields), i = parse_contract(buf, i)
    except Exception as e:
        print(f'  [ERR contract {n} at offset {i}] {e}')
        break
    if n < 15:
        fs = ', '.join(f'({x:x}:{len(s)} subs)' for x, s in fields)
        print(f'  [{n}] cid={cid} base=0x{base:X} gloms={[f"{g:X}" for g in gloms]} fields=[{fs}]')
print(f'consumed {i}/{len(buf)} bytes; remaining tail begins: {buf[i:i+16].hex(" ")}')
