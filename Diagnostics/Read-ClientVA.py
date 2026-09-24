from pathlib import Path
import struct,sys
b=Path('nexusclient/nexusclient/swtor-emu.exe').read_bytes()
pe=struct.unpack_from('<I',b,60)[0]; n=struct.unpack_from('<H',b,pe+6)[0]; opt=struct.unpack_from('<H',b,pe+20)[0]; image=struct.unpack_from('<I',b,pe+52)[0]
for arg in sys.argv[1:]:
    va=int(arg,16)
    for i in range(n):
        s=pe+24+opt+40*i;vs,rva,rs,raw=struct.unpack_from('<IIII',b,s+8)
        if rva<=va-image<rva+rs:
            p=raw+va-image-rva;data=b[p:p+128]
            print(hex(va),repr(data));print(' '.join(f'{v:08X}' for v in struct.unpack('<32I',data)))
