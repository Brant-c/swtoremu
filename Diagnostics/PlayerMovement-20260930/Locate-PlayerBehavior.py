"""Locate player behavior RTTI and bounded code references in the pinned PE."""
from pathlib import Path
import hashlib, json, re, struct

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
b = (ROOT / 'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
assert hashlib.sha256(b).hexdigest().upper() == '2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe = struct.unpack_from('<I', b, 60)[0]
opt = pe + 24
base = struct.unpack_from('<I', b, opt + 28)[0]
sections = []
for i in range(struct.unpack_from('<H', b, pe + 6)[0]):
    p = opt + struct.unpack_from('<H', b, pe + 20)[0] + 40 * i
    size, rva, raw_size, raw = struct.unpack_from('<4I', b, p + 8)
    flags = struct.unpack_from('<I', b, p + 36)[0]
    sections.append((rva, raw_size, raw, flags))

def va(p):
    for rva, size, raw, flags in sections:
        if raw <= p < raw + size:
            return base + rva + p - raw
    raise ValueError(hex(p))

def executable(p):
    return any(raw <= p < raw + size and flags & 0x20000000 for rva, size, raw, flags in sections)

def code_address(address):
    return any(base + rva <= address < base + rva + size and flags & 0x20000000
               for rva, size, raw, flags in sections)

def refs(address):
    return [m.start() for m in re.finditer(re.escape(struct.pack('<I', address)), b)]

results = []
for name in (b'.?AVBehaviorPlayerCharacterBWA@@', b'.?AVCharacterNode@@'):
    p = b.index(name + b'\0')
    descriptor = va(p - 8)
    tables = []
    for ref in refs(descriptor):
        col = ref - 12
        if col < 0:
            continue
        sig, offset, cd, td, hierarchy = struct.unpack_from('<5I', b, col)
        if sig != 0 or td != descriptor:
            continue
        for ptr in refs(va(col)):
            slots = struct.unpack_from('<38I', b, ptr + 4)
            if not all(code_address(x) for x in slots[:3]):
                continue
            end = next((i for i,x in enumerate(slots) if not code_address(x)), len(slots))
            table = va(ptr + 4)
            # The secondary table is followed by UTF16 data whose words happen
            # to lie in .text's numeric VA interval. Do not call them slots.
            if name == b'.?AVBehaviorPlayerCharacterBWA@@' and offset == 8:
                end = min(end, 6)
            tables.append({'vtable':hex(table), 'object_offset':offset,
                           'slots':[hex(x) for x in slots[:end]],
                           'code_operand_refs':[hex(va(x)) for x in refs(table) if executable(x)]})
    results.append({'name':name.decode(), 'descriptor':hex(descriptor), 'tables':tables})
assert all(x['tables'] for x in results)
(OUT / 'player-behavior-rtti.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))

# Save a bounded player-behavior code interval, verifying printed instruction
# prefixes against the PE; do not interpret section data as function pointers.
pattern = re.compile(r'^\s+([0-9A-F]{8}): ((?:[0-9A-F]{2} )+)\s*(.*)$')
lines = []
for line in (ROOT / 'Diagnostics/swtor-disasm.txt').open(errors='replace'):
    m = pattern.match(line)
    if not m or not any(lo <= int(m[1], 16) < hi for lo,hi in
                       ((0x720B00,0x723DC0),(0x734680,0x734820),(0xC1A970,0xC1AAF0),
                        (0xAFA130,0xAFA620),(0xC1A2E0,0xC1A3A0),
                        (0x727000,0x7283B0),(0x7E9B80,0x7E9E00),
                        (0x7EA870,0x7EB080),(0xC19300,0xC19700),
                        (0xC1A780,0xC1A870),(0xC1DB70,0xC1DC00),
                        (0x733C20,0x733DE0),(0x737120,0x738DE0),
                        (0x738DE0,0x73A100),
                        (0xC150E0,0xC15300),(0xCEF540,0xCEF800),
                        (0x7B73D0,0x7B78D0),(0xD1F330,0xD1F4A0),
                        (0xD020A0,0xD02530),(0x6D5D60,0x6D6020),
                        (0x6CBFD0,0x6CC180),(0x723860,0x723DC0))):
        continue
    address = int(m[1], 16)
    raw_bytes = bytes.fromhex(m[2])
    raw_offset = next(raw + address - base - rva for rva,size,raw,flags in sections
                      if base+rva <= address < base+rva+size)
    assert b[raw_offset:raw_offset+len(raw_bytes)] == raw_bytes, hex(address)
    lines.append(line.rstrip())
assert lines
(OUT / 'player-behavior-native.txt').write_text('\n'.join(lines) + '\n')
print('Verified player behavior instruction prefixes:', len(lines))

hashes = {'chrLocoAnim_PreAnimUpdate_CPP':0xD97553EA,
          'GetBehaveMoveVector_w':0x9E01F9A0,
          'GetBehaveActionTransformer_w':0x32D34133,
          'BehaviorPostAnimUpdate':0xEEED7B75,
          'BehaviorFinalAnimUpdate':0xD742E6A9,
          'GetCharacterColliderBounds_o':0x103589FD,
          'GetCharacterGroundingBounds_o':0x5BBE1820,
          'GetCharacterSlopeThreshold':0xCED9BDA4,
          'GetSupportingSurface':0x9478901D}
hash_results = []
for name,value in hashes.items():
    hash_results.append({'name':name,'hash':hex(value),
        'source':'Jedipedia chrBehaviorClassMethods / chrStandDebugClassMethods dictionaries, April1.2.0',
        'refs':[{'va':hex(va(p)),'context':b[p-12:p+20].hex()} for p in refs(value)]})
(OUT / 'movement-name-bindings.json').write_text(json.dumps(hash_results,indent=2)+'\n')
print(json.dumps(hash_results,indent=2))
