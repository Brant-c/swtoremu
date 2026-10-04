"""Add the control-clone inputs to the pinned runtime-input manifest.

Update-Identity.ps1 deliberately preserves membership and order and only
recomputes hashes, so a new runtime input must be inserted here first. Each new
file is placed next to its sibling so the manifest stays readable.
"""
import csv
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'identity.csv'

# (new path, sibling path it is inserted after)
ADDITIONS = [
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Server'
          r'\AreaTaxiCloneAwareness.cs'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Server'
          r'\AreaTaxiAwareness.cs')),
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiClone.bin'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiNpc.bin')),
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Server'
          r'\AreaMergedAwareness.cs'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Server'
          r'\AreaTaxiAwareness.cs')),
(Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiLadder0.bin'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiClone.bin')),
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiLadder1.bin'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiLadder0.bin')),
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiLadder2.bin'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiLadder1.bin')),
    (Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiRecord1.bin'),
     Path(r'D:\SWTORClassic\swtoremu\SharpServer\AreaServer\TaxiNpc.bin')),
]


def main():
    with MANIFEST.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]
    for new_path, sibling in ADDITIONS:
        if not new_path.exists():
            raise SystemExit('missing control input: %s' % new_path)
        if any(r[0] == str(new_path) for r in body):
            print('already pinned: %s' % new_path.name)
            continue
        digest = hashlib.sha256(new_path.read_bytes()).hexdigest().upper()
        entry = [str(new_path), str(new_path.stat().st_size), digest]
        idx = next(i for i, r in enumerate(body) if r[0] == str(sibling))
        body.insert(idx + 1, entry)
        print('pinned: %s (%d bytes)' % (new_path.name, new_path.stat().st_size))
    # PowerShell's Import-Csv is what consumes this file, and Update-Identity.ps1
    # rewrites it with Set-Content -Encoding UTF8. That emits a BOM and a literally
    # quoted header, so reproduce that exact shape: writing the header through the
    # csv module instead produces '\ufeff"Path"', which makes $row.Path null and
    # breaks Test-Path in Update-Identity.ps1.
    out = ['"Path","Bytes","SHA256"']
    for row in body:
        out.append(','.join('"%s"' % cell.replace('"', '""') for cell in row))
    MANIFEST.write_text('\r\n'.join(out) + '\r\n', encoding='utf-8-sig')
    print('manifest now holds %d pinned inputs' % len(body))


if __name__ == '__main__':
    main()