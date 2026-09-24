import pathlib,struct,zlib
p=pathlib.Path('AssetsConverted/swtor_main_global_1.tor')
with p.open('rb') as f:
 h=f.read(36);t=struct.unpack_from('<Q',h,12)[0];entries={}
 while t:
  f.seek(t);n,t=struct.unpack('<IQ',f.read(12))
  for i in range(n):
   e=struct.unpack('<QIIIQIH',f.read(34))
   if e[0]:entries[e[4]]=e
 e=entries[0xe4b96113c75a71e6];f.seek(e[0]+e[1]);data=f.read(e[2]);data=zlib.decompress(data) if e[6] else data
 print('Metadata bytes',len(data),'records',len(data)//32,'remainder',len(data)%32)
 found=False
 for i in range(0,len(data),32):
  ph,sh=struct.unpack_from('<II',data,i+16)
  if (ph<<32)|sh==0x6107069db7c70d58: print('GOM metadata record',i//32,'archive',data[i+24]);found=True
 print('GOM present in metadata',found)
 e=entries[0x6107069db7c70d58];f.seek(e[0]+e[1]);gom=zlib.decompress(f.read(e[2]));pos=0;blocks=0;chunks=0
 while pos<len(gom):
  magic,version=struct.unpack_from('<II',gom,pos);pos+=8;assert magic==0x424c4244 and version in [1,2];chunks+=1
  while True:
   length=struct.unpack_from('<I',gom,pos)[0];pos+=4
   if length==0:break
   assert length>=4 and pos+length-4<=len(gom);pos+=length-4;pos=(pos+7)&~7;blocks+=1
 print('Legacy GOM framing valid:',chunks,'chunks,',blocks,'definitions; bytes',pos)
