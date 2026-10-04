#!/usr/bin/env python3
"""Field-isolation ladder: which taxi-authored value kills the taxi droid's model.

BASELINE IS CAPTURED AND PROVABLY UNTOUCHED. The medcenter droid record
(0x1AC68957EB, struct 64) is copied byte-for-byte from captured awareness set 1.
Nothing this project produced makes that droid render -- it has rendered since
Tython was first reachable -- so it is the only honest "known good" sample.

Each rung is a BYTE SPLICE of that captured record, never a re-serialisation. An
earlier version walked and re-emitted the field values, which changed 262 bytes and
silently invalidated the whole ladder; Verify-TaxiLadder.py now rejects that. Because
every edit here is length-preserving, rung 0 is byte-identical to the capture except
the node identity and a 5 m X offset, and each later rung differs from rung 0 by
exactly the 9 bytes of one token.

Only fields PRESENT in the captured record can be tested this way. That means:

  0  baseline   captured record + node + position offset. Renders => transport,
                framing and placement are proven and a record we emit can render.
  1  +_characterSpecification -> taxi prototype self-reference
  2  +brkResourceName         -> taxi model identity
  3  both together            should reproduce the taxi failure if content is the
                                cause; clean => the cause is a field not here.

NOT IN THIS LADDER: chrAppearanceNppOverride. It is absent from BOTH working records
and present in ours (value 3), so it is the top suspect by evidence -- but setting it
requires INSERTING a value into the body and rewriting the size fields, which is the
operation that produced the 262-byte corruption above. It needs a verified
insert-and-relayout path first, so it is deliberately deferred rather than smuggled in.
"""
import importlib.util
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


g = load('gen', ROOT / 'Diagnostics/Generate-CrtValues.py')
schemas, _, _ = g.d7.read_schema()
names = g.d7.name_table()

SET1 = ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw'
OUT = ROOT / 'SharpServer/AreaServer'
DONOR_NODE = 0x1AC68957EB
NPC = 0x1AC7001000                       # placeholder, patched at runtime

# Offset in X from the captured position so a successful render is a visibly
# SEPARATE object rather than stacked invisibly on the original droid.
POSITION_OFFSET = 5.0   # metres in X, so a render is visibly separate from the original

# Captured donor tokens -> taxi values. Both sides are the same width (one length
# prefix byte plus eight big-endian bytes), so each substitution is length-preserving
# and cannot move any other byte.
DONOR_SPEC = 0x5541E56931B58335          # capture-time runtime hash
DONOR_RESOURCE = 0xE000C970F186EEC0     # medcenter droid model identity
TAXI_APPEARANCE_OVERRIDE = 3
TAXI_CHAR_SPEC = 0xE0008B8CC0FAEA1D
TAXI_RESOURCE_NAME = 0xE000AC918E7EA883

RUNGS = [
    (0, (), 'baseline: captured record, node + 5 m X offset only'),
    (1, ('_characterSpecification',), '+_characterSpecification = taxi self-reference'),
    (2, ('brkResourceName',), '+brkResourceName = taxi model identity'),
    (3, ('_characterSpecification', 'brkResourceName'), 'both together'),
]

SUBST = {
    '_characterSpecification': (DONOR_SPEC, TAXI_CHAR_SPEC),
    'brkResourceName': (DONOR_RESOURCE, TAXI_RESOURCE_NAME),
}


def pack(value):
    """Hero packed unsigned 64, matching Decode-Style7Replication.read_packed.

    The decoder treats a leading byte < 0xC0 as a literal single-byte value, and
    otherwise reads (byte - 0xC7) more bytes. So a multi-byte value must ALWAYS
    carry its length prefix. Deciding that from `out[0] & 0x80` is wrong: an
    8-byte value legitimately starts with a high-bit byte yet still needs the
    0xCF prefix, which is exactly how the template ids are encoded on the wire.
    """
    n = max(1, (value.bit_length() + 7) // 8)
    out = value.to_bytes(n, 'big')
    if n == 1 and out[0] < 0xC0:
        return out
    return bytes([0xC7 + n]) + out


def find_field(structure_id, field_name):
    s = schemas[structure_id]
    for i, f in enumerate(s.fields):
        if names.get(f.definition) == field_name:
            return i, f
    raise KeyError('%s not in struct %d' % (field_name, structure_id))
def main():
    data = SET1.read_bytes()
    reader, _, count = g.d7.read_gom_update(data, 0, 'set1')
    records = [g.d7.read_object_record(data, reader) for _ in range(count)]
    idx = next(i for i, r in enumerate(records) if r['node'] == DONOR_NODE)
    donor = records[idx]
    stop = records[idx + 1]['start'] if idx + 1 < len(records) else None
    raw = data[donor['start']:stop]

    sid = donor['structure_id']
    s = schemas[sid]
    begin = donor['body_start']
    end = begin + donor['inner_size']
    node_token = pack(DONOR_NODE)
    assert raw.startswith(node_token), 'donor slice does not start with its node'
    body_in_raw = donor['body_start'] - donor['start']

    pos_idx, _ = find_field(sid, 'character_position')
    captured_pos = struct.unpack_from('<3f', raw, body_in_raw)
    shifted = struct.pack('<3f', captured_pos[0] + POSITION_OFFSET,
                          captured_pos[1],
                          captured_pos[2])

    targets = {}
    for fname in ('chrAppearanceNppOverride', '_characterSpecification', 'brkResourceName'):
        i, f = find_field(sid, fname)
        targets[fname] = (i, f)

    _orig = g.parse_part

    def pp(walker, field, index, style):
        kind = field.parts[index].kind
        if kind == 3:
            return g.Part(kind, 1)
        if kind == 2:
            return g.Part(kind, walker.packed_signed())
        if kind == 5:
            return g.Part(kind, walker.packed())
        return _orig(walker, field, index, style)

# Everything below is a BYTE SPLICE. The captured record's header, body and
    # state-bit run are copied verbatim; only the node token, the 12 position bytes
    # and one 9-byte token per rung are rewritten. Nothing is decoded or re-emitted,
    # which is what made the previous version drift by 262 bytes.
    rec_len = len(raw)
    pos_off = donor['body_start'] - donor['start']        # position is value field 0
    captured_pos = struct.unpack_from('<3f', raw, pos_off)
    shifted = struct.pack('<3f', captured_pos[0] + POSITION_OFFSET,
                          captured_pos[1], captured_pos[2])
    node_token = pack(NPC)
    assert len(node_token) == len(pack(DONOR_NODE)), 'node width changed'

    # Confirm each donor token really is inside this record, and exactly once.
    for fname, (old, _new) in SUBST.items():
        hits = raw.count(pack(old))
        assert hits == 1, '%s donor token appears %d times in the record' % (fname, hits)

    manifest = []
    for rung, introduce, label in RUNGS:
        rec = bytearray(raw)
        rec[0:len(node_token)] = node_token                 # identity
        rec[pos_off:pos_off + 12] = shifted                 # position
        for fname in introduce:
            old, new = SUBST[fname]
            old_tok, new_tok = pack(old), pack(new)
            assert len(old_tok) == len(new_tok), '%s not length-preserving' % fname
            rec = bytearray(rec.replace(old_tok, new_tok))
        assert len(rec) == rec_len, 'rung %d changed the record length' % rung

        payload = struct.pack('<I', 0) + bytes([1]) + pack(1) + bytes(rec)
        out_path = OUT / ('TaxiLadder%d.bin' % rung)
        out_path.write_bytes(payload)

        prd, _, pcount = g.d7.read_gom_update(payload, 0, 'ladder%d' % rung)
        prec = g.d7.read_object_record(payload, prd)
        assert pcount == 1 and prd.pos == len(payload), 'ladder %d framing' % rung
        assert prec['node'] == NPC, 'ladder %d node' % rung
        assert prec['structure_id'] == donor['structure_id'], 'ladder %d struct' % rung
        assert prec['template_id'] == donor['template_id'], 'ladder %d template' % rung
        assert prec['parent_id'] == donor['parent_id'], 'ladder %d parent' % rung
        manifest.append({
            'rung': rung, 'label': label, 'file': out_path.name,
            'bytes': len(payload), 'record_bytes': rec_len,
            'structure_id': donor['structure_id'],
            'template': hex(donor['template_id']), 'parent': hex(donor['parent_id']),
            'introduced': sorted(introduce),
            'position': list(struct.unpack('<3f', shifted)),
            'captured_position': list(captured_pos),
        })
        print('rung %d  %-52s %d bytes' % (rung, label, len(payload)))

    (HERE / 'ladder.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('\nbaseline source: CAPTURED medcenter droid struct=%d template=%s'
          % (donor['structure_id'], hex(donor['template_id'])))
    print('captured position %s -> rung position %s'
          % (tuple(round(v, 2) for v in captured_pos),
             tuple(round(v, 2) for v in struct.unpack('<3f', shifted))))
    print('deferred: chrAppearanceNppOverride (absent in both working records; needs insert)')


if __name__ == '__main__':
    main()