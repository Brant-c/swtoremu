"""Locate the native EF.SetCharacterSpec / EF.CreateReplicatedCharacter dispatch.

These are HeroMachine engine builtins invoked as `!EF.<name>`. Unlike script
methods (e.g. `_Room_Activate`, found as UTF-16 at 0x0cbd148) they carry no
string in the exe, so they must be found structurally:

  * a table of {utf16 name, fnptr} pairs used by the HM.Call resolver, and
  * the `call eax` sites that consume it.

Strategy: find every UTF-16 string ending in "SetCharacterSpec" or
"CreateReplicatedCharacter" (including a bare name with no EF. prefix) by
scanning for the distinctive suffix, then walk backwards from each hit to find
the adjacent function pointer, and report it.

Run:  python Diagnostics/TaxiDevelopment-20261001/Find-EfBuiltin.py
Writes: ef-builtin-findings.txt
"""
import struct
import sys
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / 'nexusclient/nexusclient/swtor-emu.exe'
OUT = Path(__file__).resolve().parent / 'ef-builtin-findings.txt'

pe = pefile.PE(str(EXE))
base = pe.OPTIONAL_HEADER.ImageBase
data = pe.__data__
lines = []


def say(text=''):
    print(text)
    lines.append(text)


def rva_of(off):
    try:
        return pe.get_rva_from_offset(off)
    except Exception:
        return None


def in_image(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return True
    return False


def off_of(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None


say('exe    : %s' % EXE)
say('image  : base 0x%08X  size %d' % (base, len(data)))
say('')

NEEDLES = ['SetCharacterSpec', 'CreateReplicatedCharacter',
           'AddCharacterSpec', 'chrSpecToString']

for name in NEEDLES:
    say('=' * 70)
    say('%s' % name)
    say('=' * 70)
    for enc, label in ((name.encode('utf-16-le'), 'utf16'),
                       (name.encode('ascii'), 'ascii')):
        hits = []
        s = 0
        while True:
            i = data.find(enc, s)
            if i < 0:
                break
            hits.append(i)
            s = i + 1
            if len(hits) > 8:
                break
        say('  %-5s hits=%d %s' % (label, len(hits), [hex(h) for h in hits[:4]]))
        for off in hits[:4]:
            rva = rva_of(off)
            if rva is None:
                continue
            # Show 48 bytes before the string: the sibling name/ptr table layout.
            pre = data[max(0, off - 48):off]
            say('    file 0x%08X  rva 0x%08X  va 0x%08X' % (off, rva, base + rva))
            say('      preceding 48 bytes: %s' % pre.hex(' '))
            # An adjacent 4-byte value that looks like a code pointer.
            for back in range(4, 44, 4):
                if off - back < 0:
                    continue
                cand = struct.unpack_from('<I', data, off - back)[0]
                crva = cand - base
                if in_image(crva) and crva != 0:
                    say('      ptr at -%2d = 0x%08X (rva 0x%08X)' % (back, cand, crva))
    say('')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('wrote %s' % OUT)