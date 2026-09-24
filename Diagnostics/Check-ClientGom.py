import pathlib,struct,zlib
for name in ['AssetsConverted/swtor_main_global_1.tor','AssetOriginals/swtor_main_global_1.tor']:
 with open(name,'rb') as f:
  h=f.read(36);p=struct.unpack_from('<Q',h,12)[0]
  while p:
   f.seek(p);n,p=struct.unpack('<IQ',f.read(12))
   for i in range(n):
    e=struct.unpack('<QIIIQIH',f.read(34))
    if e[4] in [0x6107069db7c70d58,0xeecc3afb912d82f9]:
     at=f.tell();f.seek(e[0]+e[1]);data=f.read(e[2]);print(name,'entry',e,'prefix',data[:8].hex())
     if name.startswith('AssetsConverted'):print('decoded length',len(zlib.decompress(data)))
     f.seek(at)
