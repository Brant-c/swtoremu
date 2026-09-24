import struct,zlib,collections,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent/'python-deps'))
import zstandard
root=pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets')
for name in ['swtor_main_global_1.tor','swtor_main_art_misc_1.tor']:
 with (root/name).open('rb') as f:
  head=f.read(36); print(name,'header',head.hex()); table=struct.unpack_from('<Q',head,12)[0]; methods=collections.Counter()
  while table:
   f.seek(table); count,table=struct.unpack('<IQ',f.read(12))
   for i in range(count):
    offset,header,packed,size,hash_,crc,method=struct.unpack('<QIIIQIH',f.read(34))
    if not offset: continue
    methods[method]+=1
    if offset+header in [253646832,197040300,15449930]:
     pos=f.tell(); f.seek(offset+header); data=f.read(packed); print('target',hex(hash_), 'method',method,'sizes',packed,size,'prefix',data[:16].hex())
     try:
      decoded=zlib.decompress(data) if method else data
      print('decoded',len(decoded),'prefix',repr(decoded[:100]))
     except Exception as e: print('zlib decode error',e)
     if data.startswith(bytes.fromhex('28b52ffd')):
      decoded=zstandard.ZstdDecompressor().decompress(data,max_output_size=size)
      print('Zstandard decoded bytes',len(decoded),'expected',size,'match',len(decoded)==size,'prefix',repr(decoded[:40]))
     f.seek(pos)
  print('compression methods',dict(methods))
