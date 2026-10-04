import struct, sys

exe = sys.argv[1]
d = open(exe, 'rb').read()

e_lfanew = struct.unpack('<I', d[0x3C:0x40])[0]
sig = d[e_lfanew:e_lfanew+4]
assert sig == b'PE\x00\x00', sig
coff = e_lfanew + 4
num_sections = struct.unpack('<H', d[coff+2:coff+4])[0]
size_opt = struct.unpack('<H', d[coff+16:coff+18])[0]
opt = coff + 20
magic = struct.unpack('<H', d[opt:opt+2])[0]
is64 = magic == 0x20B
ib_off = opt + (24 if is64 else 28)
image_base = struct.unpack('<Q' if is64 else '<I', d[ib_off:ib_off+(8 if is64 else 4)])[0]
print('num_sections=%d size_opt=%d is64=%s image_base=0x%X' % (num_sections, size_opt, is64, image_base))

sec_off = opt + size_opt
sections = []
for i in range(num_sections):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\x00').decode('ascii', 'replace')
    vsize, va, rawsize, rawptr = struct.unpack('<IIII', d[o+8:o+24])
    sections.append((name, va, rawptr, rawsize, vsize))
    print('  %-8s VA=0x%08X raw=0x%08X rawsize=0x%X' % (name, va, rawptr, rawsize))

def f2va(foff):
    for name, va, rawptr, rawsize, vsize in sections:
        if rawptr <= foff < rawptr + rawsize:
            return image_base + va + (foff - rawptr)
    return None

for t in [0x00D52C94, 0x00D3F9D0, 0x00D53010]:
    va = f2va(t)
    print('file 0x%X -> VA 0x%X' % (t, va if va else 0))
