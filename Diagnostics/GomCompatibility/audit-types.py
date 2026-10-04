"""Strict legacy type audit. Unknown types are failures, never silently accepted."""
import collections, json, pathlib, struct
here = pathlib.Path(__file__).resolve().parent
raw = (here / 'client.gom').read_bytes()
def read_type(data, at=0, path='root'):
    if at >= len(data):
        raise ValueError('Truncated type at ' + path)
    code = data[at]
    at += 1
    if code >= 23:
        raise ValueError(f'Unsupported type {code} at {path}, byte {at-1}')
    if code in (5, 9, 15):
        if at + 8 > len(data):
            raise ValueError('Truncated reference type')
        at += 8
    elif code == 7:
        at = read_type(data, at, path + '.element')
    elif code == 8:
        at = read_type(data, at, path + '.key')
        at = read_type(data, at, path + '.value')
    return at

fields = {}
classes = []
pos = 8
while pos < len(raw):
    length = struct.unpack_from('<I', raw, pos)[0]
    if not length:
        break
    record = raw[pos:pos+length]
    assert len(record) == length and length >= 24
    ident = struct.unpack_from('<Q', record, 8)[0]
    kind = (struct.unpack_from('<H', record, 16)[0] >> 3) & 15
    nameoff = struct.unpack_from('<H', record, 20)[0]
    name = record[nameoff:].split(b'\0')[0].decode('ascii', errors='replace')
    if kind == 3:
        size, offset = struct.unpack_from('<HH', record, 26)
        data = record[offset:offset+size]
        row = dict(id=str(ident), name=name, file_offset=pos, type_hex=data.hex())
        try:
            consumed = read_type(data)
            if consumed != len(data):
                raise ValueError(f'Trailing bytes: {len(data)-consumed}')
            row['status'] = 'legacy_shape_accepted'
        except ValueError as exc:
            row.update(status='incompatible', reason=str(exc))
        fields[ident] = row
    elif kind == 4:
        count, offset = struct.unpack_from('<HH', record, 46)
        ids = [struct.unpack_from('<Q', record, offset+8*i)[0] for i in range(count)]
        classes.append(dict(id=str(ident), name=name, field_ids=ids))
    pos = (pos + length + 7) & ~7
bad = [row for row in fields.values() if row['status'] == 'incompatible']
bad_ids = {int(row['id']) for row in bad}
references = [dict(id=c['id'], name=c['name'], incompatible_fields=[str(i) for i in c['field_ids'] if i in bad_ids])
              for c in classes if any(i in bad_ids for i in c['field_ids'])]
report = dict(field_count=len(fields), incompatible_field_count=len(bad), affected_class_count=len(references), incompatible_fields=bad, affected_classes=references)
(here / 'type-audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}, indent=2))
for row in bad[:30]:
    print(row)
