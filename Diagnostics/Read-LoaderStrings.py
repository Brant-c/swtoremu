from pathlib import Path
import struct
b=Path('nexusclient/nexusclient/swtor-emu.exe').read_bytes(); pe=struct.unpack_from('<I',b,60)[0]; n=struct.unpack_from('<H',b,pe+6)[0]; opt=struct.unpack_from('<H',b,pe+20)[0]; image=struct.unpack_from('<I',b,pe+24+28)[0]
for va in [0x1163304,0x1163320,0x11633e0,0x11634bc,0x138ca30]:
 for i in range(n):
  s=pe+24+opt+40*i;vs,rva,rs,raw=struct.unpack_from('<IIII',b,s+8)
  if rva<=va-image<rva+max(vs,rs):
   p=raw+va-image-rva;print(hex(va),repr(b[p:p+100]))

