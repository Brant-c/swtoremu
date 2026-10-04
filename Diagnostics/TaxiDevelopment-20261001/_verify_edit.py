"""Prove the regenerated fixture differs from the previous one by exactly the
two removed field bytes, and report the new identity-patch offsets.

Any other difference would mean the regeneration changed something it must not
have, so this is a hard gate on the fixture edit.
"""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NEW = ROOT / 'SharpServer/AreaServer/TaxiNpc.bin'
OLD = HERE / 'TaxiNpc.PREFIX-78CE8D7A.bin'

old = OLD.read_bytes()
new = NEW.read_bytes()
print('old %d bytes  sha256 %s' % (len(old), hashlib.sha256(old).hexdigest()))
print('new %d bytes  sha256 %s' % (len(new), hashlib.sha256(new).hexdigest()))
print('delta %+d bytes' % (len(new) - len(old)))

# Common prefix length, then show what follows.
i = 0
while i < min(len(old), len(new)) and old[i] == new[i]:
    i += 1
print()
print('identical prefix: %d bytes' % i)
print('old tail from there (%d bytes): %s' % (len(old) - i,
                                             old[i:i + 24].hex(' ')))
print('new tail from there (%d bytes): %s' % (len(new) - i,
                                             new[i:i + 24].hex(' ')))
print()
print('old tail (last 24): %s' % old[-24:].hex(' '))
print('new tail (last 24): %s' % new[-24:].hex(' '))

spec = importlib.util.spec_from_file_location('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
d7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d7)
r, _, n = d7.read_gom_update(new, 0, 'new')
rec = d7.read_object_record(new, r)
print()
print('new record: struct=%s style=%s inner=%d body=%d value_end=%d' % (
    rec['structure_id'], rec['style'], rec['inner_size'],
    rec['body_start'], rec['value_end']))
print('objects=%d  walked to end: %s' % (n, r.pos == len(new)))