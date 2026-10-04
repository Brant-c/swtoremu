"""Check the generated taxi fixture carries the borrowed spawn-link fields.

Runs against TaxiNpc.bin directly, so it needs no built assembly and can be run
while the server is still up. It verifies only what this change adds;
Verify-Taxi.py remains the deep byte-level walk over the emitted packet.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('d7', ROOT/'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
schemas, _, _ = d.read_schema()
names = d.name_table()

ANCHOR = 0x400000136330355E
TMR = 0x1AC68957EC
TERMINAL = 0xE000DC42A2436F58

data = (ROOT/'SharpServer/AreaServer/TaxiNpc.bin').read_bytes()
reader, flags, count = d.read_gom_update(data, 0, 'TaxiNpc.bin')
recs = [d.read_object_record(data, reader) for _ in range(count)]
assert reader.pos == len(data) and count == 5, (reader.pos, len(data), count)

npc = recs[0]
st = schemas[npc['structure_id']]
end = npc['body_start'] + npc['inner_size']
states, _ = d.field_states(data, end, npc['value_end'] - end, len(st.fields), npc['style'])
present = {i for i, s in enumerate(states) if s == 1}
print(f"fixture bytes={len(data)} struct={npc['structure_id']} inner={npc['inner_size']} "
      f"present={len(present)}")

# Fields 0..33 contain no containers, so this prefix walks exactly.
r = d.Reader(data, npc['body_start'], end)
values = {}
for i in [i for i in sorted(present) if i <= 33]:
    kind = st.fields[i].parts[0].kind
    if kind in (1, 2, 9, 15, 17):
        values[i] = r.packed()
    elif kind == 3:
        continue
    elif kind == 4:
        r.pos += 4
    elif kind == 5:
        values[i] = r.byte()
    elif kind == 18:
        r.pos += 12
    else:
        raise SystemExit(f'unexpected kind {kind} at field {i}')

for i, expected in ((8, 5), (32, TERMINAL), (33, TMR)):
    label = names.get(st.fields[i].definition, '?')
    assert i in present, f'field {i} ({label}) absent'
    assert values[i] == expected, f'field {i} ({label}) = 0x{values[i]:X}, expected 0x{expected:X}'
    print(f"  [{i:2}] {label:24} = {values[i] if i == 8 else hex(values[i])}  ok")

assert 57 in present, 'spnSpawnedSpec absent'
assert 59 in present, 'chrAppearanceNppOverride absent'
assert 62 in present and 85 in present, 'appearance tail not marked present'
print(f"  [57] {names.get(st.fields[57].definition, '?'):24} present  ok")
print(f"  [59] {names.get(st.fields[59].definition, '?'):24} present  ok")

# The transplanted tail must carry the TAXI's resource name, not the donor's.
TAXI_RN = bytes([0xCF]) + (16141090805656758403).to_bytes(8, 'big')
VENDOR_RN = bytes([0xCF]) + (0xE000C970F186EEC0).to_bytes(8, 'big')
tail = data[npc['body_start'] + npc['inner_size'] - 57:npc['body_start'] + npc['inner_size']]
assert tail.count(TAXI_RN) == 1, tail.count(TAXI_RN)
assert tail.count(VENDOR_RN) == 0, 'donor resource name still present in the tail'
TAXI_SPEC = bytes([0xCF]) + (0xE0008B8CC0FAEA1D).to_bytes(8, 'big')
DONOR_SPEC = bytes([0xCF]) + (0x5541E56931B58335).to_bytes(8, 'big')
assert tail.count(TAXI_SPEC) == 1, tail.count(TAXI_SPEC)
assert tail.count(DONOR_SPEC) == 0, 'donor char spec still present in the tail'
assert 27 not in present, 'spnParentAnchorId must be absent (anchor key collision)'
# staEnterIdle is a Boolean and consumes zero value bytes, so it is carried purely
# by its presence bit. Weller -- the only confirmed working NPC -- has it present,
# and it is the one field the taxi was missing. It is set by the generator, so if
# this fails the change was silently dropped.
assert 37 in present, 'staEnterIdle must be present (matches Weller CRT12 contract)'
print("\n  tail: taxi brkResourceName + taxi _characterSpecification present once; "
      "donor values absent  ok")
print("  spnParentAnchorId(27): absent, as required to avoid the spnReplicatedNpcs "
      "key collision  ok")
print("\nPASS: taxi-authored chrGender(8), taxTerminalSpec(32), tmrContainer(33), "
      "chrAppearanceNppOverride(59); tail carries the taxi resource name and the taxi "
      "character specification; no borrowed anchor.")