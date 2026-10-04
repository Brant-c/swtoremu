"""Read-only verification of exact native prefixes against the pinned April PE."""
from pathlib import Path
import hashlib, re, struct
root = Path(__file__).resolve().parents[2]
data = (root / 'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
assert hashlib.sha256(data).hexdigest().upper() == '2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe = struct.unpack_from('<I', data, 60)[0]
assert data[pe:pe + 4] == b'PE\0\0'
optional = pe + 24
assert struct.unpack_from('<H', data, optional)[0] == 0x10B
base = struct.unpack_from('<I', data, optional + 28)[0]
count = struct.unpack_from('<H', data, pe + 6)[0]
size = struct.unpack_from('<H', data, pe + 20)[0]
header = (root / 'Client/Hook/Src/RoomSelectionTrace.h').read_text()
for name, va in [('roomRegisterPrefix', 0xB90CF0), ('roomSelectPrefix', 0xB91AE0), ('roomActivatePrefix', 0xB7C390)]:
    body = re.search(r'static const BYTE ' + name + r'\[\] = \{(.*?)\};', header, re.S)[1]
    prefix = bytes(int(x, 16) for x in re.findall(r'0x([0-9A-F]{2})\b', body))
    assert len(prefix) == 48
    for n in range(count):
        s = optional + size + 40*n
        _, rva, raw_size, raw_offset = struct.unpack_from('<IIII', data, s + 8)
        if rva <= va - base < rva + raw_size:
            offset = raw_offset + va - base - rva
            assert data[offset:offset + 48] == prefix, name
            print(f'PASS {name}: VA={va:08X}, 48 exact PE bytes')
            break
    else:
        raise AssertionError('Missing backed target')
print('PASS pinned April executable identity. No process access.')

header = (root / 'Client/Hook/Src/TriggerCollisionPrefixes.h').read_text()
for name, va in [('triggerStringPrefix', 0x7FE1F0), ('triggerBooleanPrefix', 0x7FDE70)]:
    body = re.search(r'static const BYTE ' + name + r'\[\] = \{(.*?)\};', header, re.S)[1]
    prefix = bytes(int(x, 16) for x in re.findall(r'0x([0-9A-F]{2})\b', body))
    assert len(prefix) == 48
    for n in range(count):
        s = optional + size + 40*n
        _, rva, raw_size, raw_offset = struct.unpack_from('<IIII', data, s + 8)
        if rva <= va - base < rva + raw_size:
            offset = raw_offset + va - base - rva
            assert data[offset:offset + 48] == prefix, name
            print(f'PASS {name}: VA={va:08X}, 48 exact PE bytes')
            break
    else:
        raise AssertionError('Missing backed target')
