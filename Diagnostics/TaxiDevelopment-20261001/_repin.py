"""Repin the identity manifest for the fixture this session deliberately changed.

Only rows whose current hash differs from its pin are rewritten, and every
rewrite is printed. Launch.ps1 refuses to start if any pinned input has drifted,
so a fixture edit is not usable until this is run deliberately.
"""
import csv
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
path = HERE / 'identity.csv'
rows = list(csv.DictReader(path.open(encoding='utf-8-sig')))
fieldnames = list(rows[0].keys())

changed = 0
for row in rows:
    target = Path(row['Path'])
    if not target.exists():
        print('MISSING  %s' % target)
        continue
    data = target.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    size = len(data)
    if digest == row['SHA256'] and str(size) == row['Bytes']:
        continue
    print('REPIN')
    print('   path %s' % target)
    print('   was  %s  %s bytes' % (row['SHA256'], row['Bytes']))
    print('   now  %s  %s bytes' % (digest, size))
    row['SHA256'] = digest
    row['Bytes'] = str(size)
    changed += 1

if changed:
    with path.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
print()
print('%d row(s) repinned in %s' % (changed, path.name))