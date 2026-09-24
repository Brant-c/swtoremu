from pathlib import Path
import re, struct
b=Path('nexusclient/nexusclient/swtor-emu.exe').read_bytes()
pe=struct.unpack_from('<I',b,60)[0]
n=struct.unpack_from('<H',b,pe+6)[0]
opt=struct.unpack_from('<H',b,pe+20)[0]
image=struct.unpack_from('<I',b,pe+52)[0]
def va(p):
    for i in range(n):
        s=pe+24+opt+40*i
        vs,rva,rs,raw=struct.unpack_from('<IIII',b,s+8)
        if raw<=p<raw+rs:return image+rva+p-raw
    return p
for pattern,encoding in [(rb'[\x20-\x7e]{6,}','ascii'),(rb'(?:[\x20-\x7e]\x00){6,}','utf-16le')]:
    for m in re.finditer(pattern,b):
        text=m.group().decode(encoding)
        if re.search(r'gui.*(?:xml|prototype|load)|(?:xml|prototype|load).*gui|Prototype .*not found|createControlType',text,re.I):
            print(f'{va(m.start()):08X}',text)
