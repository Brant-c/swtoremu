import struct, sys

exe = sys.argv[1]
d = open(exe, 'rb').read()

# DOS header
e_lfanew = struct.unpack('<I', d[0x3C:0x40])[0]
print('e_lfanew = 0x%X' % e_lfanew)

# PE signature + COFF header
sig = d[e_lfanew:e_lfanew+4]
print('signature = %r' % sig)
machine, num_sections, _, _, _, size_opt = struct.unpack('<HHIIIH', d[e_lfanew+4:e_lfanew+24])
print('machine=0x%X num_sections=%d size_opt=%d' % (machine, num_sections, size_opt))

opt_off = e_lfanew + 24
magic = struct.unpack('<H', d[opt_off:opt_off+2])[0]
print('optional magic=0x%X (0x20B=PE32+)' % magic)
is64 = magic == 0x20B
# ImageBase: PE32 -> opt+28, PE32+ -> opt+24
ib_off = opt_off + (24 if is64 else 28)
image_base = struct.unpack('<Q' if is64 else '<I', d[ib_off:ib_off+(8 if is64 else 4)])[0]
print('image_base = 0x%X' % image_base)

# section headers
sec_off = opt_off + size_opt
print('--- sections ---')
sections = []
for i in range(num_sections):
    o = sec_off + i*40
    name = d[o:o+8].rstrip(b'\x00').decode('ascii', 'replace')
    vsize, va, rawsize, rawptr = struct.unpack('<IIII', d[o+8:o+24])
    sections.append((name, va, rawptr, rawsize, vsize))
    print('  %-8s VA=0x%08X raw=0x%08X rawsize=0x%X vsize=0x%X' % (name, va, rawptr, rawsize, vsize))

def file_to_va(foff):
    for name, va, rawptr, rawsize, vsize in sections:
        if rawptr <= foff < rawptr + rawsize:
            return image_base + va + (foff - rawptr)
    return None

for target in [0x00D52C94, 0x00D3F9D0, 0x00D52C94]:
    va = file_to_va(target)
    print('file 0x%X -> VA 0x%X' % (target, va if va else 0))
