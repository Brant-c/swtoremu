r'''
Disassemble exact RVA ranges from the April-2012 client exe with correct
instruction boundaries (dumpbin desyncs in data regions; capstone does not).

Usage:
  python Diagnostics/Disasm-Range.py 0x34F2B0 0x34F400
  python Diagnostics/Disasm-Range.py 0x34F2B0 60        # 60 instructions
'''
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

try:
    import pefile  # noqa: F401
except ImportError:
    sys.exit('pefile missing: python -m pip install pefile')

EXE = r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe'

pe = pefile.PE(EXE)
image_base = pe.OPTIONAL_HEADER.ImageBase
data = pe.__data__


def rva_to_offset(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None


def read_at(rva, n):
    off = rva_to_offset(rva)
    if off is None:
        raise SystemExit('RVA %08X not mapped' % rva)
    return data[off:off + n]


def disasm(start_rva, count=80, length=None):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    code = read_at(start_rva, length if length else count * 8)
    out = []
    for i, ins in enumerate(md.disasm(code, image_base + start_rva)):
        rva = ins.address - image_base
        out.append('%08X: %-24s %s %s' % (rva, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        if length is None and i + 1 >= count:
            break
        if length is not None and ins.address - image_base >= start_rva + length:
            break
    return '\n'.join(out)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    start = int(args[0], 16) if args[0].startswith('0x') else int(args[0], 16)
    if len(args) >= 2:
        v = args[1]
        if v.lower().startswith('0x'):
            print(disasm(start, length=int(v, 16)))
        else:
            print(disasm(start, count=int(v)))
    else:
        print(disasm(start, count=60))
