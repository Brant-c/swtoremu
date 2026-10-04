"""Confirm the client actually received the fixture we generated.

AreaTaxiAwareness.BuildPayload() hashes the payload AFTER it substitutes the
placeholder identities for this session's nodes, so the logged sha256 can never
equal the sha256 of TaxiNpc.bin itself. This replays the substitution using the
node values from the run log and compares the result, proving whether the built
binary embedded the current fixture.
"""
import hashlib
import re
from pathlib import Path

FIXTURE = Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiNpc.bin')
LOG = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\NexusToR.log')

OFFSETS = [6, 109, 115, 121, 127, 486, 502, 531, 538, 554, 584, 600, 630, 646]
SLOTS = [0, 1, 2, 3, 4, 1, 0, 0, 2, 0, 3, 0, 4, 0]


def pack(value):
    out = bytearray()
    while True:
        out.insert(0, value & 0xFF)
        value >>= 8
        if not value:
            break
    if len(out) <= 8 and (out[0] & 0x80 or len(out) == 1):
        return bytes(out)
    return bytes([0xC7 + len(out)]) + bytes(out)


line = next(l for l in LOG.read_text(errors='ignore').splitlines()
            if 'AreaTaxiAwareness:' in l and 'sha256=' in l)
logged = re.search(r'sha256=([0-9A-F]{64})', line).group(1).lower()
nodes = [int(x, 16) for x in re.findall(
    r'0x([0-9A-F]{16})', line.split('npc=')[1])]
print('logged sha256 : %s' % logged)
print('fixture sha256: %s' % hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
print('nodes         : %s' % ['0x%016X' % n for n in nodes])

payload = bytearray(FIXTURE.read_bytes())
for offset, slot in zip(OFFSETS, SLOTS):
    expected = pack(0x1AC7001000 + slot)
    assert bytes(payload[offset:offset + len(expected)]) == expected, \
        'placeholder mismatch at %d' % offset
    payload[offset:offset + len(pack(nodes[slot]))] = pack(nodes[slot])

replayed = hashlib.sha256(bytes(payload)).hexdigest()
print('replayed sha  : %s' % replayed)
print()
print('MATCH - the run used the generated fixture' if replayed == logged
      else 'MISMATCH - the run used a DIFFERENT fixture')