"""Move the identity-patch offsets and fixture length after the field removal.

Dropping chrGender (struct-66 field 8) and chrAppearanceNppOverride (field 59)
shortens TaxiNpc.bin from 677 to 675 bytes. Every guarded identity offset after
those fields therefore moves: by -1 past field 8, and by -2 past field 59.

New offsets come from the regenerated fixture.json `patches` list, which is
computed by scanning the new payload for the five placeholder node tokens; they
are not hand-derived here.

Rung 1 (`taxi.record1`) is deliberately left at its existing 677 bytes -- its
generator is not present in this tree -- so RungBytes records the real per-rung
sizes. Running rung 1 is therefore still valid, and any mismatch would throw and
fall back to the untouched captured set rather than send a malformed list.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKT = ROOT / 'SharpServer/NET/Packets/Server'

OLD_OFFSETS = '6,109,115,121,127,486,502,531,538,554,584,600,630,646'
NEW_OFFSETS = '6,108,114,120,126,484,500,529,536,552,582,598,628,644'
OLD_OFFSETS_SPACED = '6, 109, 115, 121, 127, 486, 502, 531, 538, 554, 584, 600, 630, 646'
NEW_OFFSETS_SPACED = '6, 108, 114, 120, 126, 484, 500, 529, 536, 552, 582, 598, 628, 644'

EDITS = [
    (PKT / 'AreaTaxiAwareness.cs', [
        ('Offsets = { ' + OLD_OFFSETS + ' }', 'Offsets = { ' + NEW_OFFSETS + ' }'),
        ('FixtureBytes = 677', 'FixtureBytes = 675'),
    ]),
    (PKT / 'AreaMergedAwareness.cs', [
        ('Offsets = { ' + OLD_OFFSETS_SPACED + ' }',
         'Offsets = { ' + NEW_OFFSETS_SPACED + ' }'),
        ('RungBytes = { 677, 677 }', 'RungBytes = { 675, 677 }'),
        ('-- an 8-byte change out of 677 that keeps the taxi template,',
         '-- an 8-byte change out of 675 that keeps the taxi template,'),
    ]),
]

fail = False
for path, pairs in EDITS:
    text = path.read_bytes().decode('utf-8')
    for old, new in pairs:
        if text.count(old) != 1:
            print('ABORT %s: %r occurs %d times' % (
                path.name, old, text.count(old)))
            fail = True
            continue
        text = text.replace(old, new)
        print('  %-24s %s' % (path.name, new[:70]))
    if not fail:
        path.write_bytes(text.encode('utf-8'))
sys.exit(1 if fail else 0)