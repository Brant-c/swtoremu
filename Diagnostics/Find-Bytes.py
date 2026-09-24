r'''Locate true instruction addresses by byte signature and disassemble around
them. Usage: python Diagnostics/Find-Bytes.py 3D806E440D 0x120'''
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe'
pe = pefile.PE(EXE)
base = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if b'.text' in s.Name)
raw = sec.get_data()
rva0 = sec.VirtualAddress
md = Cs(CS_ARCH_X86, CS_MODE_32)

sig = bytes.fromhex(sys.argv[1])
span = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x100
hits = []
start = 0
while True:
    i = raw.find(sig, start)
    if i < 0:
        break
    start = i + 1
    hits.append(i)

print('signature %s: %d hit(s)' % (sys.argv[1], len(hits)))
for i in hits:
    print('=== at %08X ===' % (base + rva0 + i))
    lo = max(0, i - 16)
    code = raw[lo:i + span]
    for ins in md.disasm(code, base + rva0 + lo):
        if ins.address == base + rva0 + i:
            print('  >>> %08X: %s %s' % (ins.address - base, ins.mnemonic, ins.op_str))
        else:
            print('      %08X: %s %s' % (ins.address - base, ins.mnemonic, ins.op_str))
