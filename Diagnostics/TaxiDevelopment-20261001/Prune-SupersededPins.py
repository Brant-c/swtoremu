"""Prune the pinned-input manifest after the medcenter-droid ladder was superseded.

Update-Identity.ps1 preserves membership and refuses to run when a pinned path is
missing, so removing a fixture requires editing identity.csv first. This drops the
TaxiLadder*.bin rows (and the now-unused generator and verifier that produced them)
and adds TaxiRecord1.bin next to TaxiNpc.bin.

It also reproduces the exact file shape Update-Identity expects: a UTF-8 BOM and a
literally quoted header. Writing the header through the csv module instead produces
'\ufeff"Path"', which makes $row.Path null and breaks Test-Path.
"""
import csv
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'identity.csv'
DROP = ('TaxiLadder', 'Generate-TaxiLadder.py', 'Verify-TaxiLadder.py')
ADD = Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiRecord1.bin')
AFTER = Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiNpc.bin')


def main():
    with MANIFEST.open(newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]
    kept = [r for r in body if not any(k in r[0] for k in DROP)]
    removed = len(body) - len(kept)
    if not any(r[0] == str(ADD) for r in kept):
        if not ADD.exists():
            raise SystemExit('missing %s' % ADD)
        digest = hashlib.sha256(ADD.read_bytes()).hexdigest().upper()
        idx = next((i for i, r in enumerate(kept) if r[0] == str(AFTER)), None)
        entry = [str(ADD), str(ADD.stat().st_size), digest]
        if idx is None:
            kept.append(entry)
        else:
            kept.insert(idx + 1, entry)
    out = ['"%s","%s","%s"' % (header[0], header[1], header[2])]
    for r in kept:
        out.append(','.join('"%s"' % c.replace('"', '""') for c in r))
    MANIFEST.write_text('\r\n'.join(out) + '\r\n', encoding='utf-8-sig')
    print('removed %d superseded pin(s); manifest now %d inputs' % (removed, len(kept)))


if __name__ == '__main__':
    main()