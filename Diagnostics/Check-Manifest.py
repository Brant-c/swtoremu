import pathlib,struct,zlib
for name in ['AssetsConverted/swtor_main_global_1.tor','AssetOriginals/swtor_main_global_1.tor']:
 with open(name,'rb') as f:
  h=f.read(36);p=struct.unpack_from('<Q',h,12)[0]
  while p:
   f.seek(p);n,p=struct.unpack('<IQ',f.read(12))
   for i in range(n):
    e=struct.unpack('<QIIIQIH',f.read(34))
    if e[0]+e[1]==258688942:
     at=f.tell();f.seek(e[0]+e[1]);data=f.read(e[2]);print(name,'entry',e,'prefix',data[:8].hex())
     print('data',repr(data[:250]))
     f.seek(at)

