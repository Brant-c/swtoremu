"""Diagnostic exclusion, NOT a semantics-preserving asset converter."""
import hashlib, json, pathlib, struct
here = pathlib.Path(__file__).resolve().parent
raw = (here / 'client.gom').read_bytes()
bad = 4611686316368904000
owner = 4611690223225570000
out = bytearray(raw[:8])
pos = 8
removed = changed = 0
while pos < len(raw):
    length = struct.unpack_from('<I', raw, pos)[0]
    if not length:
        out.extend(raw[pos:])
        break
    record = bytearray(raw[pos:pos+length])
    ident = struct.unpack_from('<Q', record, 8)[0]
    kind = (struct.unpack_from('<H', record, 16)[0] >> 3) & 15
    pos = (pos + length + 7) & ~7
    if ident == bad:
        assert kind == 3
        removed += 1
        continue
    if ident == owner:
        assert kind == 4
        count, offset = struct.unpack_from('<HH', record, 46)
        ids = [struct.unpack_from('<Q', record, offset+8*i)[0] for i in range(count)]
        assert ids.count(bad) == 1
        kept = [i for i in ids if i != bad]
        struct.pack_into('<H', record, 46, len(kept))
        for i, value in enumerate(kept + [0]):
            struct.pack_into('<Q', record, offset+8*i, value)
        changed += 1
    out.extend(record)
    out.extend(b'\0' * ((-len(out)) % 8))
assert removed == changed == 1
(here / 'client-field-isolation.gom').write_bytes(out)
(here / 'field-isolation.json').write_text(json.dumps(dict(
    warning='Diagnostic only: omitted one modern field and its direct class reference. Scripts, prototypes, and network values may still require it.',
    omitted_field=str(bad), changed_class=str(owner), original_size=len(raw), test_size=len(out),
    original_sha256=hashlib.sha256(raw).hexdigest(), test_sha256=hashlib.sha256(out).hexdigest()), indent=2))
print(f'Diagnostic GOM: {len(out)} bytes; removed one field and one class reference')
