r'''Scan the client .text for direct stores to [reg+0x8C] (the area state
field the bridge probes at area+0x8C) and report each candidate with a small
capstone-verified disassembly context.

  python Diagnostics/Find-AreaStateWrites.py
'''
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe'

pe = pefile.PE(EXE)
base = pe.OPTIONAL_HEADER.ImageBase
text = None
for s in pe.sections:
    if b'.text' in s.Name:
        text = s
raw = text.get_data()
text_rva = text.VirtualAddress

# C7 /0 = mov dword ptr [reg + disp32], imm32  (ModRM mod=10)
# C7 40..47 8C 00 00 00 = [reg+0x8C], imm  (mod=01, disp8)
# C7 80..87 8C 00 00 00 imm32 = [reg+0x8C], imm  (mod=10, disp32)
patterns = []
for rex in range(0x40, 0x48):
    patterns.append((bytes([0xC7, rex, 0x8C]), 'disp8'))
for rex in range(0x80, 0x88):
    patterns.append((bytes([0xC7, rex, 0x8C, 0x00, 0x00, 0x00]), 'disp32'))

md = Cs(CS_ARCH_X86, CS_MODE_32)
hits = {}
for pat, kind in patterns:
    start = 0
    while True:
        i = raw.find(pat, start)
        if i < 0:
            break
        start = i + 1
        # verify by disassembling from a little before to cover alignment
        for back in range(0, 4):
            off = i - back
            if off < 0:
                continue
            code = raw[off:off + 16]
            ins_list = list(md.disasm(code, base + text_rva + off))
            if not ins_list:
                continue
            ins = ins_list[0]
            if ins.mnemonic == 'mov' and '+ 0x8c]' in ins.op_str and ins.bytes[0] == 0xC7:
                imm = int(ins.op_str.split(', ', 1)[1], 16)
                hits.setdefault(ins.address - base, (imm, ins.mnemonic + ' ' + ins.op_str))
                break

print('found %d direct [x+0x8C] stores' % len(hits))
for addr in sorted(hits):
    imm, txt = hits[addr]
    print('%08X: %-40s imm=%d' % (addr, txt, imm))
