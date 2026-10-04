"""Bounded static collision-path evidence; no process access or native calls."""
from pathlib import Path
import hashlib, json, re, struct

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
data = (ROOT / 'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
digest = hashlib.sha256(data).hexdigest().upper()
assert digest == '2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe = struct.unpack_from('<I', data, 60)[0]
optional = pe + 24
base = struct.unpack_from('<I', data, optional + 28)[0]
count = struct.unpack_from('<H', data, pe + 6)[0]
size = struct.unpack_from('<H', data, pe + 20)[0]
sections = []
for i in range(count):
    pos = optional + size + 40*i
    _, rva, raw_size, raw_offset = struct.unpack_from('<IIII', data, pos + 8)
    sections.append((rva, raw_size, raw_offset))

def offset(va):
    for rva, raw_size, raw_offset in sections:
        if rva <= va-base < rva+raw_size:
            return raw_offset + va-base-rva
    raise ValueError(hex(va))

def word(va):
    return struct.unpack_from('<I', data, offset(va))[0]

vtable = 0x116116C
col = word(vtable-4)
descriptor = word(col+12)
name = data[offset(descriptor)+8:offset(descriptor)+140].split(b'\0')[0].decode()
assert name == '.?AVTriggerNode@@'
assert word(vtable+0xB4) == 0x7FDE70
ranges = {
    'trigger-property-dispatch': (0x7FD8C0, 0x7FDA3B),
    'trigger-collidable-setter': (0x7FDE70, 0x7FDFA7),
    'trigger-collidable-getter': (0x7FC752, 0x7FC7C8),
    'entity-physics-remove': (0x6D4F60, 0x6D4FA8),
    'entity-physics-add': (0x6D4FB0, 0x6D4FF6),
    'trigger-constructor-vtable': (0x7FB1E0, 0x7FB250),
    'trigger-parameter-setter': (0x7FE1F0, 0x7FE2BB),
    'entity-vector-property': (0x6D3FF0, 0x6D409D),
    'entity-local-position-cache': (0x6D5D60, 0x6D5EC0),
}
lines = {k: [] for k in ranges}
pattern = re.compile(r'^\s+([0-9A-F]{8}): ((?:[0-9A-F]{2} )+)\s*(.*)$')
verified = 0
with (ROOT / 'Diagnostics/swtor-disasm.txt').open(errors='replace') as listing:
    active = []
    for line in listing:
        match = pattern.match(line)
        if match:
            va = int(match[1], 16)
            active = [k for k, (lo, hi) in ranges.items() if lo <= va < hi]
            if active:
                raw = bytes.fromhex(match[2])
                pos = offset(va)
                assert data[pos:pos+len(raw)] == raw, hex(va)
                verified += 1
        for key in active:
            lines[key].append(line.rstrip())
for key, text in lines.items():
    (OUT / (key+'.txt')).write_text('\n'.join(text)+'\n')
summary = {
    'PE_SHA256': digest, 'TriggerNodeVtable': hex(vtable),
    'CompleteObjectLocator': hex(col), 'TypeDescriptor': hex(descriptor),
    'RTTIName': name, 'VirtualB4': hex(word(vtable+0xB4)),
    'VerifiedPrintedInstructionPrefixes': verified,
    'Limit': 'Existing listing prefixes verified; not fresh instruction boundary decoding',
}
(OUT / 'collision-path-verification.json').write_text(json.dumps(summary, indent=2)+'\n')
print(f'PASS TriggerNode RTTI/vtable+ B4 and {verified} printed prefixes; no process access.')
