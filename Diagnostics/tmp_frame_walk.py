import struct, mmap
from pathlib import Path

p = Path(r'D:\\SWTORClassic\\swtoremu\\Diagnostics\\world-entry-20260919-002833-79616-first.dmp')
f = open(p,'rb')
m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
sig, ver, nstreams, dirrva, _ = struct.unpack('<IIIII', m[:20])
streams = {}
for i in range(nstreams):
    st, size, rva = struct.unpack('<III', m[dirrva+i*12:dirrva+i*12+12])
    streams.setdefault(st, []).append((rva,size))
rva6, _ = streams[6][0]
ctx_size, ctx_rva = struct.unpack('<II', m[rva6+160:rva6+168])
ebp = struct.unpack('<I', m[ctx_rva+180:ctx_rva+184])[0]
print('ebp', hex(ebp), 'ctx_rva', hex(ctx_rva))
rva4, _ = streams[4][0]
count = struct.unpack('<I', m[rva4:rva4+4])[0]
p2 = rva4+4
base=None
for _ in range(count):
    mb, ms, cksum, tstamp, name_rva = struct.unpack('<QIIII', m[p2:p2+24])
    nlen = struct.unpack('<I', m[name_rva:name_rva+4])[0]
    name = m[name_rva+4:name_rva+4+nlen].decode('utf-16-le').rstrip('\0')
    if 'swtor-emu.exe' in name.lower():
        base = mb
        break
    p2 += 108
print('base', hex(base))
bp = ebp
for i in range(64):
    raw = m[bp:bp+16]
    if len(raw) != 16: break
    next_bp, ret, arg1, arg2 = struct.unpack('<4I', raw)
    if ret == 0: break
    print('frame %2d bp=%08X ret=%08X off=%08X arg1=%08X arg2=%08X' % (i, bp, ret, (ret-base) if base else 0, arg1, arg2))
    if next_bp <= bp or next_bp - bp > 0x10000 or next_bp % 4:
        break
    bp = next_bp
m.close(); f.close()
