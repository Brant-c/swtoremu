exec(open('Diagnostics/Inspect-Assets.py').read().split('for name in')[0])
p=root/'swtor_main_art_misc_1.tor'
with p.open('rb') as f:
 h=f.read(36); f.seek(struct.unpack_from('<Q',h,12)[0]); n,next_=struct.unpack('<IQ',f.read(12))
 for i in range(3):
  e=struct.unpack('<QIIIQIH',f.read(34)); pos=f.tell(); off,hs,cs,us,ha,crc,method=e;f.seek(off); header=f.read(hs);data=f.read(cs);raw=zstandard.ZstdDecompressor().decompress(data) if method else data
  print(e,'header',header.hex(),'crc',hex(crc),'packedCRC',hex(zlib.crc32(data)),'rawCRC',hex(zlib.crc32(raw)),'packedAdler',hex(zlib.adler32(data)),'rawAdler',hex(zlib.adler32(raw)),'withheader',hex(zlib.adler32(header+data)),'headerCRC',hex(zlib.crc32(header)),'headerAdler',hex(zlib.adler32(header)),'combinedCRC',hex(zlib.crc32(header+data)));f.seek(pos)

