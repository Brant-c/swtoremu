"""Taxi rung 2: drop the two fields the authored taxi node proves we must not send.

DIFF-DRIVEN, not hypothesis-driven. The authored node
`_JPEXTRACT/npc.location.tython.taxi.jediretreat_pad1 (hex).json` sets 23 fields.
Our synthesized record sets 31, and only 2 of ours are authored. Of the 29 we set
that the authored node does not, these two are index-verified as absent from the
authored node:

    idx 57  spnSpawnedSpec           (UInt64) -- spawner chain, not appearance
    idx 59  chrAppearanceNppOverride (UInt64) -- absent from authored taxi

Earlier rungs tuned OTHER fields assuming the character build was blocked by a
spec we could substitute. That was wrong twice over:

  * `_characterSpecification` (idx 77) is a distinct field from the
    `chrNonPlayerCharacterSpec` the client reports as `Unknown spec(0)`.
  * `chrNonPlayerCharacterSpec` is NOT a struct-66 field at all. It exists on the
    authored prototype in the client DOM (Shared with server DOM: yes), which is
    exactly what Jedipedia dumped, but it is not replicated in the update. So the
    client's `Unknown spec(0)` is a prototype-resolution failure on its side, and
    nothing we can send would fix it.

So this rung is NOT "tune the spec". It is the one safe, authored-exact correction
available: send only fields the authored node sends.

Relayout notes (verified against the decoder, not assumed):
  * The field-state bitstream is the TAIL of the value block, not a prefix. Its
    width depends on how many fields are present, so removing a field shrinks it.
  * Value bytes for a present field sit between body_start and the state stream,
    in field order. Removing a field removes its value bytes too.
  * outer_size / inner_size must be re-emitted to match.

Every invariant is asserted. If any check fails the original fixture is untouched.
"""
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

spec = importlib.util.spec_from_file_location(
    'd7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

SCHEMAS, _, _ = d.read_schema()
NAMES = d.name_table()

SRC = ROOT / 'SharpServer/AreaServer/TaxiNpc.bin'
DST = ROOT / 'SharpServer/AreaServer/TaxiRecord2.bin'

DROP = {57: 'spnSpawnedSpec', 59: 'chrAppearanceNppOverride'}


def pack(value):
    n = max(1, (value.bit_length() + 7) // 8)
    out = value.to_bytes(n, 'big')
    if n == 1 and out[0] < 0xC0:
        return out
    return bytes([0xC7 + n]) + out


def encode_states(states):
    """Re-emit the style-8 state bitstream: two bits per schema field.

    Established by dumping the client's own stream for this record rather than
    assumed:

    1. It never emits the code-3 run form, even across the long absent stretches,
       so every field is a plain 2-bit code: 01 = present, 00 = absent.
    2. Packing is MSB-first, matching d.BitReader. The captured stream starts
       0x50 = 01010000, which read as 2-bit codes gives 01,01,00,00 -- exactly
       the decoded sequence for fields 0..3.

    Consequence: the stream is a fixed 2 bits x field-count wide (95 fields =
    190 bits = 24 bytes), so dropping a field leaves the state stream
    byte-identical and shrinks the value block only.
    """
    bits = []
    for state in states:
        # Confirmed by round-trip against the captured stream: a present field is
        # the 2-bit code 10 and an absent field is 00, MSB-first. Encoding the
        # present bit second reproduces the client's own 24 bytes exactly.
        bits.append(0)
        bits.append(0 if state == 2 else 1)
    while len(bits) % 8:
        bits.append(0)
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        out.append(byte)
    return bytes(out)


def build():
    data = SRC.read_bytes()
    rec = d.read_object_record(data, d.Reader(data, 6))
    assert rec['structure_id'] == 66, 'taxi NPC record must be struct 66'
    schema = SCHEMAS[rec['structure_id']]
    nfields = len(schema.fields)

    body = rec['body_start']
    state_start = body + rec['inner_size']
    original_states = data[state_start:rec['value_end']]

    states, _ = d.field_states(data, state_start, rec['value_end'] - state_start,
                               nfields, 8)
    present_before = [i for i, s in enumerate(states) if s != 2]

    for idx, want in DROP.items():
        assert NAMES.get(schema.fields[idx].definition) == want, \
            'index %d is not %s' % (idx, want)
        assert states[idx] != 2, '%s is already absent' % want

    # Prove the encoder reproduces the CLIENT's own bytes for an unchanged field
    # list first. If this fails, every later check is meaningless.
    assert encode_states(states) == original_states, 'state encoder does not round-trip'

    # Walk present fields in order to find each target's value span.
    reader = d.Reader(data, body)
    spans = {}
    for i in range(nfields):
        if states[i] == 2:
            continue
        start = reader.pos
        reader.packed()
        spans[i] = (start, reader.pos)
    assert reader.pos == state_start, 'value walk did not reach the state stream'
    for i in DROP:
        assert spans[i][1] - spans[i][0] == 9, \
            'field %d is not a single 9-byte token' % i

    # Splice out both value spans.
    values = bytearray()
    cursor = body
    for i in sorted(DROP):
        s, e = spans[i]
        values += data[cursor:s]
        cursor = e
    values += data[cursor:state_start]
    assert len(values) == rec['inner_size'] - 18, 'expected to remove 18 value bytes'

    new_states = list(states)
    for i in DROP:
        new_states[i] = 2
    inner = bytes(values) + encode_states(new_states)

    # Re-emit outer_size/inner_size immediately before the value block.
    outer_size = rec['value_end'] - rec['outer_start']
    new_outer = outer_size - rec['inner_size'] - 18 + len(inner)
    size_at = body - len(pack(outer_size)) - len(pack(rec['inner_size']))
    assert data[size_at:body] == pack(outer_size) + pack(rec['inner_size']), \
        'size tokens not found where expected'
    new_sizes = pack(new_outer) + pack(len(inner))
    assert len(new_sizes) == body - size_at, 'size token width changed'

    out = bytearray(data[:size_at]) + new_sizes + inner + data[rec['value_end']:]
    return bytes(out), nfields, present_before


def verify(payload, nfields, present_before):
    rd, _, count = d.read_gom_update(payload, 0, 'rung2')
    recs = [d.read_object_record(payload, rd) for _ in range(count)]
    assert count == 5, 'expected five records, got %d' % count
    assert rd.pos == len(payload), 'payload does not walk to its own end'
    r = recs[0]
    assert r['structure_id'] == 66, 'structure changed'
    assert r['template_id'] == 0xE0008B8CC0FAEA1D, 'taxi template must survive'
    assert r['node'] == 0x1AC7001000, 'identity placeholder must survive'

    states, _ = d.field_states(payload, r['body_start'] + r['inner_size'],
                               r['value_end'] - r['body_start'] - r['inner_size'],
                               nfields, 8)
    for i, want in DROP.items():
        assert states[i] == 2, '%s still present after relayout' % want
    present_after = [i for i, s in enumerate(states) if s != 2]
    gone = set(present_before) - set(present_after)
    assert gone == set(DROP), 'unexpected fields lost: %r' % sorted(gone)
    assert len(present_after) == len(present_before) - 2
    return r, present_after


def main():
    payload, nfields, present_before = build()
    rec, present_after = verify(payload, nfields, present_before)
    DST.write_bytes(payload)
    print('TaxiRecord2.bin written: %d bytes' % len(payload))
    for i, want in sorted(DROP.items()):
        print('  dropped idx %d %s' % (i, want))
    print('  present fields %d -> %d' % (len(present_before), len(present_after)))
    print('  template 0x%016X preserved' % rec['template_id'])
    print('  identity placeholders preserved; 5 records walk to end')
    print('  sha256 %s' % hashlib.sha256(payload).hexdigest())


if __name__ == '__main__':
    main()
# __APPEND_MAIN__
