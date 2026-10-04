"""Extract bounded hook guards from the pinned PE and verify relocations."""
from pathlib import Path
import hashlib, struct
root = Path(__file__).resolve().parents[2]
data = (root / 'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
assert hashlib.sha256(data).hexdigest().upper() == '2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe = struct.unpack_from('<I', data, 60)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
assert base == 0x400000
sections = []
for i in range(struct.unpack_from('<H', data, pe + 6)[0]):
    p = opt + struct.unpack_from('<H', data, pe + 20)[0] + i * 40
    _, rva, size, raw = struct.unpack_from('<4I', data, p + 8)
    sections.append((rva, size, raw))
def offset(rva):
    return next(raw + rva - start for start, size, raw in sections if start <= rva < start + size)
reloc_rva, reloc_size = struct.unpack_from('<2I', data, opt + 96 + 5 * 8)
relocations = set()
p, end = offset(reloc_rva), offset(reloc_rva) + reloc_size
while p < end:
    page, size = struct.unpack_from('<2I', data, p)
    assert size >= 8
    for q in range(p + 8, p + size, 2):
        item = struct.unpack_from('<H', data, q)[0]
        if item >> 12 == 3:
            relocations.add(page + (item & 0xfff))
    p += size
parts = ['// Generated from pinned April PE; exact48 bytes, validated relocation offsets.']
for name, va, expected in [('movementSweepPrefix', 0x7B7450, [9]),
                           ('movementSupportPrefix', 0xCEF540, [25]),
                           ('movementGroundPrefix', 0x738F80, [])]:
    rva = va - base
    found = sorted(x - rva for x in relocations if rva <= x < rva + 48)
    assert found == expected, (name, found, expected)
    block = data[offset(rva):offset(rva) + 48]
    parts.append('static const BYTE ' + name + '[] = {\n    ' +
                 ',\n    '.join(', '.join(f'0x{x:02X}' for x in block[i:i+16]) for i in range(0,48,16)) + ' };')
    print(f'PASS {name} VA={va:08X}, relocations={found}, SHA256={hashlib.sha256(block).hexdigest()}')
(root / 'Client/Hook/Src/MovementCollisionPrefixes.h').write_text('\n'.join(parts) + '\n')
