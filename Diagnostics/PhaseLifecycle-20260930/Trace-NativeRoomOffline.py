"""Preserve bounded existing disassembly and verify printed byte prefixes against PE.

Reads files only; no running process, native hook, or packet operation.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'native-room-offline'
OUT.mkdir(exist_ok=True)
exe = ROOT / 'nexusclient/nexusclient/swtor-emu.exe'
listing = ROOT / 'Diagnostics/swtor-disasm.txt'
data = exe.read_bytes()
pe = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe + 4] == b'PE\0\0'
count = struct.unpack_from('<H', data, pe + 6)[0]
optional_size = struct.unpack_from('<H', data, pe + 20)[0]
assert struct.unpack_from('<H', data, pe + 24)[0] == 0x10b
base = struct.unpack_from('<I', data, pe + 24 + 28)[0]
sections = []
for n in range(count):
    p = pe + 24 + optional_size + n * 40
    virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', data, p + 8)
    sections.append((rva, raw_size, raw_offset))

def offset(va):
    rva = va - base
    for start, size, raw in sections:
        if start <= rva < start + size:
            return raw + rva - start
    raise ValueError(f'VA {va:08X} lacks backed bytes')

ranges = {
    'area-selection-loop': (0x71c610, 0x71c736),
    'room-activate': (0xb7c390, 0xb7c598),
    'room-content-apply': (0xb79c30, 0xb7a000),
    'area-register': (0xb90c00, 0xb90e10),
    'area-select': (0xb93700, 0xb93a00),
    'area-secondary-select': (0xb8f5e0, 0xb8f800),
    'room-selection-change': (0xb91ae0, 0xb91df0),
    'room-position-select': (0xb92300, 0xb92620),
    'area-startup-readiness': (0xb92ee0, 0xb93110),
    'room-movement-callers': (0x6f9200, 0x6f9340),
    'entity-room-propagation': (0x6df370, 0x6df3e0),
    'room-position-test': (0xb7b010, 0xb7b0d0),
    'room-selection-refresh': (0xb92680, 0xb92750),
    'related-room-reference': (0xb7a040, 0xb7a0b0),
    'related-room-fallback': (0xb8d0f0, 0xb8d2e0),
    'set-character-dispatch': (0x650405, 0x65046b),
    'room-reference-setter': (0xb79f70, 0xb7a040),
    'room-setting-parser': (0xb7d53b, 0xb7d588),
}
saved = {name: [] for name in ranges}
refs = []
verified = 0
pattern = re.compile(r'^\s+([0-9A-F]{8}): ((?:[0-9A-F]{2} )+)\s*(.*)$')
targets = {'00B7C390', '00B7C8B0', '00B79C30', '00B90CF0', '00B91AE0', '00B8F5E0'}
with listing.open(errors='replace') as f:
    active = []
    for line in f:
        match = pattern.match(line)
        if match:
            va = int(match[1], 16)
            active = [name for name, (lo, hi) in ranges.items() if lo <= va < hi]
            if active:
                raw = bytes.fromhex(match[2])
                p = offset(va)
                assert data[p:p + len(raw)] == raw, f'Listing mismatch {va:08X}'
                verified += 1
            if re.search(r'call\s+(?:' + '|'.join(targets) + r')\b', match[3]):
                refs.append(line.rstrip())
        for name in active:
            saved[name].append(line.rstrip())
for name, lines in saved.items():
    (OUT / (name + '.txt')).write_text('\n'.join(lines) + '\n')
(OUT / 'direct-call-references.txt').write_text('\n'.join(refs) + '\n')
strings = {}
for va in [0x10bdf48, 0x1158040, 0x10bfc84, 0x10bfa00, 0x10be638, 0x10bdce0, 0x115a950]:
    p = offset(va)
    strings[f'{va:08X}'] = {
        'ascii': data[p:p + 160].split(b'\0')[0].decode('ascii', errors='replace'),
        'utf16': data[p:p + 160].decode('utf-16le', errors='replace').split('\0')[0],
    }
index_path = ROOT / '_JPEXTRACT/Scriptdef.listdump.csv'
with index_path.open(newline='', encoding='utf-8-sig') as f:
    scripts = [row for row in csv.DictReader(f) if re.search(
        r'BaseClient|phsOracle|phsGateway|phsPhasedInstance|phsPhaseInfo', row['Name'], re.I)]
with (OUT / 'script-targets.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=scripts[0].keys())
    writer.writeheader()
    writer.writerows(scripts)
summary = {
    'Executable': str(exe), 'ExecutableSHA256': hashlib.sha256(data).hexdigest(),
    'ImageBase': hex(base), 'Listing': str(listing),
    'VerifiedInstructionPrefixes': verified, 'DirectCallReferences': len(refs),
    'Strings': strings,
    'Limits': 'Existing dumpbin listing, not fresh decoding. Printed instruction byte prefixes verified; omitted continuation bytes and instruction boundaries not independently decoded. Direct calls only, not all xrefs.',
}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
