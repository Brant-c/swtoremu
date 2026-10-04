"""Decode the transplanted appearance tail, field by field.

The tail is the donor struct-64 record's last 57 body bytes, covering struct-64
fields 62,63,66,68,70,77,78,80,86 in that order. Earlier attempts failed because
0xC0-0xC7 were treated as invalid packed tokens, when they are in fact the
signed form: cbtFaction is exactly that encoding.

Two independent confirmations pin the split:
  * cbtFaction decodes to -878620586690540766, which is the taxi prototype's own
    npcFaction (taxi-content.txt / npc.location.tython.taxi.jediretreat_pad1).
  * brkResourceName lands on the ninth-byte pattern the generator patches, i.e.
    at the offset struct-64 field 70 must occupy.

struct66 maps these to indices 62,63,66,68,69,76,77,79,85 because struct66 drops
struct-64 index 69 (vndVendorIconOnExtraMaps).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

TAIL_FIELDS_64 = [62, 63, 66, 68, 70, 77, 78, 80, 86]
TAIL_FIELDS_66 = [62, 63, 66, 68, 69, 76, 77, 79, 85]

taxi = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
reader, _, count = d.read_gom_update(taxi, 0, 'TaxiNpc.bin')
recs = [d.read_object_record(taxi, reader) for _ in range(count)]
npc = recs[0]
st = schemas[66]
end = npc['body_start'] + npc['inner_size']
tail = taxi[end - 57:end]
print(f"tail {len(tail)} bytes: {tail.hex()}\n")

# Split using the known per-field encodings: signed Int64 (0xC0-0xC7 = negative
# with token-0xBF payload bytes), unsigned IDs, raw-byte enums, NodeRefs.
def read_signed(w, pos):
    token = tail[pos]
    if token < 0xC0:
        return token, pos + 1
    if 0xC0 <= token <= 0xC7:
        n = token - 0xBF
        return -int.from_bytes(tail[pos + 1:pos + 1 + n], 'big'), pos + 1 + n
    if 0xC8 <= token <= 0xCF:
        n = token - 0xC7
        return int.from_bytes(tail[pos + 1:pos + 1 + n], 'big'), pos + 1 + n
    raise ValueError(f'bad signed token 0x{token:02X}')


pos = 0
TAXI_FACTION = -878620586690540766
results = []

# 62 chrCreatureTypeList: 9-byte ID + 3 trailing bytes (shape not fully known)
raw0 = tail[0:9]
assert raw0[0] == 0xCF, raw0.hex()
results.append((0, 62, 62, 'chrCreatureTypeList', f'head=0x{int.from_bytes(raw0[1:], "big"):X} + {tail[9:12].hex()}'))
pos = 12

# 63 cbtFaction
value, nxt = read_signed(tail, pos)
assert value == TAXI_FACTION, f'cbtFaction {value} != taxi npcFaction {TAXI_FACTION}'
results.append((pos, 63, 63, 'cbtFaction', value))
pos = nxt

# 66 chrTemplateVisualIndex (Int64), 68 cbtCreatureType (raw byte enum)
value, nxt = read_signed(tail, pos)
results.append((pos, 66, 66, 'chrTemplateVisualIndex', value))
pos = nxt
results.append((pos, 68, 68, 'cbtCreatureType', f'enum={tail[pos]}'))
pos += 1

# 70 brkResourceName (unsigned ID)
assert tail[pos] == 0xCF
rn = int.from_bytes(tail[pos + 1:pos + 9], 'big')
results.append((pos, 70, 69, 'brkResourceName', f'0x{rn:X}'))
pos += 9

# 77 chrClass (unsigned ID)
assert tail[pos] == 0xCF
cls = int.from_bytes(tail[pos + 1:pos + 9], 'big')
results.append((pos, 77, 76, 'chrClass', f'0x{cls:X}'))
pos += 9

# 78 _characterSpecification (signed Int64)
spec_value, nxt = read_signed(tail, pos)
results.append((pos, 78, 77, '_characterSpecification',
                f'{spec_value} (0x{spec_value & 0xFFFFFFFFFFFFFFFF:X})'))
pos = nxt

# 80 ablContainer (NodeRef)
token = tail[pos]
if token < 0xC0:
    ac, nxt = token, pos + 1
else:
    n = token - 0xC7
    ac = int.from_bytes(tail[pos + 1:pos + 1 + n], 'big')
    nxt = pos + 1 + n
results.append((pos, 80, 79, 'ablContainer', f'0x{ac:X}'))
pos = nxt

# 86 chrLevel (signed Int64)
level, nxt = read_signed(tail, pos)
results.append((pos, 86, 85, 'chrLevel', level))
pos = nxt

print(f"{'off':>4} {'s64':>4} {'s66':>4} {'field':26} value")
for off, i64, i66, label, value in results:
    print(f"{off:>4} {i64:>4} {i66:>4} {label:26} {value}")
print(f"\nconsumed {pos}/57 -> {'EXACT' if pos == 57 else 'MISMATCH'}")

print("\ncross-checks against the taxi prototype (authoritative client content):")
print(f"  cbtFaction  == npcFaction          : {results[1][4] == TAXI_FACTION}")
print(f"  chrClass    == npcClassPackage     : {cls == 16140921840742184344} (0x{cls:X})")
print(f"  brkResourceName == taxi brkResourceName: {rn == 16141090805656758403} (0x{rn:X})")
print(f"  _characterSpecification           : {spec_value} <- the 'Unknown spec' candidate")