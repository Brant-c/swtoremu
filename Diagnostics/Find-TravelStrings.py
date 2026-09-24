from pathlib import Path
import struct
b=Path('nexusclient/nexusclient/swtor-emu.exe').read_bytes()
p=struct.unpack_from('<I',b,60)[0]; n=struct.unpack_from('<H',b,p+6)[0]; opt=struct.unpack_from('<H',b,p+20)[0]; image=struct.unpack_from('<I',b,p+52)[0]
sections=[struct.unpack_from('<IIII',b,p+24+opt+40*i+8) for i in range(n)]
for needle in [b'SendToArea',b'TravelStatus',b'OmegaWorldObject']:
 start=0
 while True:
  at=b.find(needle,start)
  if at<0:break
  start=at+len(needle)
  va=next((image+rva+at-raw for vs,rva,rs,raw in sections if raw<=at<raw+rs),None)
  print(needle,hex(va) if va else hex(at),repr(b[at:at+110].split(b'\0')[0]))
