import pathlib,sys,struct,zlib,hashlib,json,shutil
sys.path.insert(0,str(pathlib.Path(__file__).parent/'python-deps'))
import zstandard
base=pathlib.Path(__file__).resolve().parents[1]
retail=pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets')
source=base/'AssetOriginals';target=base/'AssetsConverted'
source.mkdir(exist_ok=True);target.mkdir(exist_ok=True)
names=['swtor_main_global_1.tor','swtor_en-us_global_1.tor','swtor_main_art_misc_1.tor']
entry=struct.Struct('<QIIIQIH')
report=[]
for name in names:
 src=source/name
 if not src.exists(): shutil.copy2(retail/name,src)
 dst=target/name
 if dst.exists(): raise RuntimeError('Output already exists: '+str(dst))
 with src.open('rb') as f:
  head=bytearray(f.read(36)); table=struct.unpack_from('<Q',head,12)[0];entries=[];seen=set()
  while table:
   assert table not in seen;seen.add(table);f.seek(table);n,table=struct.unpack('<IQ',f.read(12));assert n<1000000
   entries.extend(e for e in (entry.unpack(f.read(34)) for _ in range(n)) if e[0])
  # Preserve the original index topology and metadata by copying the archive,
  # then append replacement payloads and update only offsets and packed sizes.
  shutil.copy2(src,dst)
  with dst.open('r+b') as out:
   table=struct.unpack_from('<Q',head,12)[0];converted=0;verified=0
   while table:
    f.seek(table);n,table=struct.unpack('<IQ',f.read(12))
    for _ in range(n):
     index=f.tell(); values=list(entry.unpack(f.read(34))); resume=f.tell()
     off,hs,cs,us,ha,crc,method=values
     if not off:continue
     f.seek(off);header=f.read(hs);data=f.read(cs);assert len(data)==cs
     if method==1 and data.startswith(bytes.fromhex('28b52ffd')):
      raw=zstandard.ZstdDecompressor().decompress(data,max_output_size=us);assert len(raw)==us
      packed=zlib.compress(raw,6);assert zlib.decompress(packed)==raw
      out.seek(0,2);values[0]=out.tell();values[2]=len(packed)
      out.write(header);out.write(packed);out.seek(index);out.write(entry.pack(*values))
      # Read back the written entry and payload, and compare all decoded bytes.
      out.seek(index);v=entry.unpack(out.read(34));out.seek(v[0]+v[1]);assert zlib.decompress(out.read(v[2]))==raw
      converted+=1;verified+=1
     elif method not in (0,1):raise RuntimeError('Unknown compression method')
     f.seek(resume)
  result=dict(archive=name,converted=converted,verified=verified,source_bytes=src.stat().st_size,output_bytes=dst.stat().st_size,source_sha256=hashlib.file_digest(src.open('rb'),'sha256').hexdigest(),output_sha256=hashlib.file_digest(dst.open('rb'),'sha256').hexdigest())
  report.append(result);print(json.dumps(result),flush=True)
(target/'conversion-report.json').write_text(json.dumps({'note':'Experimental: original archive version, per-entry checksums and metadata preserved; their semantics have not been validated for converted data. Retail files unchanged.','archives':report},indent=2))
