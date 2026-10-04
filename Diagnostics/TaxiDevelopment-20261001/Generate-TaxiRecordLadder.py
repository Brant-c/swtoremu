"""Taxi-record ladder rung 1: revert the taxi's _characterSpecification to the
captured donor value, changing nothing else.

Rung 0 is the shipped TaxiNpc.bin unchanged (control; known to produce six script
errors). This rung exists to test the TAXI record itself rather than a
medcenter-droid stand-in: chrNonPlayerCharacter is the base class of both the
working medcenter droid and our taxi, so if the spec value is what blocks the
character build, reverting just this one token -- while keeping the taxi template,
taxTerminalSpec and position -- turns the errors off on a record that is still
genuinely the taxi.

It is a pure, length-preserving byte splice, so it is verifiable before any client
run. DEFERRED: dropping chrAppearanceNppOverride (present in ours, absent in both
working records) is also worth testing, but it requires removing a value from the
body and rewriting the state run, which is the operation that corrupted an earlier
ladder by 262 bytes. That needs a verified insert/relayout path first rather than
another speculative generator.
"""
import hashlib
import importlib.util
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

spec = importlib.util.spec_from_file_location(
    'd7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

TAXI = ROOT / 'SharpServer/AreaServer/TaxiNpc.bin'
OUT = ROOT / 'SharpServer/AreaServer/TaxiRecord1.bin'

TAXI_SPEC = 0xE0008B8CC0FAEA1D      # taxi prototype self-reference (shipped)
DONOR_SPEC = 0x5541E56931B58335     # captured medcenter droid value


def pack(value):
    n = max(1, (value.bit_length() + 7) // 8)
    out = value.to_bytes(n, 'big')
    if n == 1 and out[0] < 0xC0:
        return out
    return bytes([0xC7 + n]) + out


def main():
    data = TAXI.read_bytes()
    rec = d.read_object_record(data, d.Reader(data, 6))
    assert rec['structure_id'] == 66, 'taxi NPC record must be struct 66'
    body, inner_end = rec['body_start'], rec['body_start'] + rec['inner_size']

    cur, new = pack(TAXI_SPEC), pack(DONOR_SPEC)
    assert len(cur) == len(new) == 9, (len(cur), len(new))
    seg = data[body:inner_end]
    hits = [i for i in range(len(seg)) if seg.startswith(cur, i)]
    # The taxi prototype id legitimately appears TWICE in the body: once as
    # spnSpawnedSpec and once as _characterSpecification. Only the latter is the
    # character spec, and replacing the first would silently repoint the spawner.
    # _characterSpecification is struct-66 index 77, the later of the two, so patch
    # the LAST occurrence and assert the earlier one is left alone.
    if len(hits) == 1:
        target = hits[0]
    elif len(hits) == 2:
        target = hits[-1]
    else:
        raise SystemExit('taxi spec token appears %d times; expected 1 or 2'
                         % len(hits))
    out = bytearray(data)
    out[body + target:body + target + len(new)] = new

    # Pure splice: identical length, and only those 9 bytes differ.
    assert len(out) == len(data), 'record length changed'
    diff = [k for k in range(len(data)) if data[k] != out[k]]
    assert diff and diff[-1] - diff[0] + 1 <= 9, \
        'change spans %d bytes, expected a single 9-byte token' % (
            diff[-1] - diff[0] + 1)
    assert new in bytes(out[body + target:body + target + 9])
    # The EARLIER occurrence (spnSpawnedSpec) must still be the taxi prototype.
    if len(hits) == 2:
        assert bytes(out[body + hits[0]:body + hits[0] + 9]) == cur, \
            'spnSpawnedSpec was disturbed; only _characterSpecification may change'
        print('  spnSpawnedSpec at body+%d left as the taxi prototype' % hits[0])

    # Full re-parse: five records, exact walk to end, identity preserved.
    rd, _, count = d.read_gom_update(bytes(out), 0, 'rung1')
    recs = [d.read_object_record(out, rd) for _ in range(count)]
    assert count == 5 and rd.pos == len(out), 'framing walk failed'
    assert recs[0]['node'] == 0x1AC7001000, 'NPC node placeholder changed'
    assert recs[0]['structure_id'] == 66 and recs[0]['template_id'] == 0xE0008B8CC0FAEA1D, \
        'taxi structure or template must be preserved'

    OUT.write_bytes(bytes(out))
    print('TaxiRecord1.bin written: %d bytes' % len(out))
    print('  changed %d byte(s) at offset %d..%d (one packed token)'
          % (len(diff), diff[0], diff[-1]))
    print('  template 0x%016X preserved (still the taxi)' % recs[0]['template_id'])
    print('  sha256 %s' % hashlib.sha256(bytes(out)).hexdigest())


if __name__ == '__main__':
    main()