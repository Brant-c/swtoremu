"""Drop the two authored-absent fields from the taxi wire surface.

chrGender (struct-66 field 8, chrNPCGenderComplete=5) and
chrAppearanceNppOverride (field 59, npcAppearanceOverride=3) are authored on the
taxi prototype but are NOT part of its replicated surface -- that is exactly
taxTerminalSpec + brkResourceName -- and neither appears in any reference NPC
record. Removing them makes this record present the same field set the captured
vendor does.

Single variable of Diagnostics/Experiments/2026-10-02-07. It shortens the record
by 2 bytes, so every downstream identity-patch offset must move with it; the
regenerated fixture.json reports the new offsets.

Patches Generate-Taxi.py in place, by line number, preserving line endings.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
path = HERE / 'Generate-Taxi.py'
raw = path.read_bytes().decode('utf-8')
eol = '\r\n' if '\r\n' in raw else '\n'
lines = raw.split(eol)

# 1-based line numbers validated against the current file.
CHECKS = {
    84: 'TAXI_GENDER = 5',
    85: 'TAXI_APPEARANCE_OVERRIDE = 3',
    88: '8:pack(TAXI_GENDER),',
    92: '57:pack(TEMPLATE),59:pack(TAXI_APPEARANCE_OVERRIDE)}',
}
for num, expect in CHECKS.items():
    got = lines[num - 1]
    if expect not in got:
        print('ABORT: line %d is %r, expected %r' % (num, got, expect))
        sys.exit(1)

note = [
    '# chrGender (struct-66 field 8) and chrAppearanceNppOverride (field 59) were',
    '# sent as chrNPCGenderComplete=5 and npcAppearanceOverride=3. Both are AUTHORED on',
    '# the taxi prototype but NEITHER is in its replicated surface, which is exactly',
    '# taxTerminalSpec + brkResourceName, and neither appears in any reference NPC',
    '# record. Dropping them makes this record present the same field set the captured',
    '# vendor does: the single variable of Experiments/2026-10-02-07. The record gets 2',
    '# bytes shorter, so every identity-patch offset downstream must move with it.',
]
new = lines[:83] + note + [
    '  values = {0:struct.pack(\'<3f\', *PLACEMENT),',
    '            1:data[donor[\'body_start\']+12:donor[\'body_start\']+24],',
    '            9:struct.pack(\'<f\',1), 10:struct.pack(\'<f\',.1), 13:pack(2),',
    '            22:pack(1),23:pack(EQP),24:pack(POS),25:pack(NEG),26:pack(OTHER),',
    '            32:pack(TERMINAL),33:pack(TMR_CONTAINER),',
    '            57:pack(TEMPLATE)}',
] + lines[92:]

path.write_bytes(eol.join(new).encode('utf-8'))
print('patched %s (%d -> %d lines)' % (path.name, len(lines), len(new)))
print('removed field 8 (chrGender) and field 59 (chrAppearanceNppOverride)')