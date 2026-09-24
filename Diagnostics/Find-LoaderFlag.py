from pathlib import Path
import struct
b=Path('nexusclient/nexusclient/swtor-emu.exe').read_bytes();pe=struct.unpack_from('<I',b,60)[0];n=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0];sections=[]
for i in range(n):
 s=pe+24+opt+40*i;vs,rva,rs,raw=struct.unpack_from('<IIII',b,s+8);sections.append((raw,rs,rva))
def va(off):
 for raw,size,rva in sections:
  if raw<=off<raw+size:return off-raw+rva+0x400000

for addr in [0x138d038,0x138d039]:
 print('flag',hex(addr));p=0
 while True:
  p=b.find(struct.pack('<I',addr),p)
  if p<0:break
  print('ref',hex(va(p) or 0));p+=4

