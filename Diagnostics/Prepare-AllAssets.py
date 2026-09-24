import pathlib,sys,struct,zlib,hashlib,json,shutil,time
sys.path.insert(0,str(pathlib.Path(__file__).parent/'python-deps'))
import zstandard
base=pathlib.Path(__file__).resolve().parents[1]
retail=pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets')
source=base/'AssetOriginals';target=base/'AssetsConverted'
source.mkdir(exist_ok=True);target.mkdir(exist_ok=True)
report_path=target/'conversion-report.json'
report=json.loads(report_path.read_text())
completed={r['archive']:r for r in report['archives']}
entry=struct.Struct('<QIIIQIH'); decoder=zstandard.ZstdDecompressor()
for number,original in enumerate(sorted(retail.glob('*.tor')),1):
 name=original.name;src=source/name;dst=target/name
 if name in completed:
  assert dst.exists() and dst.stat().st_size==completed[name]['output_bytes'];continue
 print(f'[{number}/101] Copying and converting {name}',flush=True)
 if not src.exists():
  temp=src.with_suffix('.copying');shutil.copy2(original,temp);temp.rename(src)
 tmp=dst.with_suffix('.partial')
 if tmp.exists() or dst.exists():raise RuntimeError('Unfinished or untracked output: '+name)
 with src.open('rb') as f,tmp.open('w+b') as out:
  header=bytearray(f.read(36));assert header[:4]==b'MYP\0'
  table=struct.unpack_from('<Q',header,12)[0];blocks=[];seen=set()
  while table:
   assert table not in seen;seen.add(table);f.seek(table);n,table=struct.unpack('<IQ',f.read(12));assert n<1000000
   rows=[list(entry.unpack(f.read(34))) for _ in range(n)];blocks.append(rows)
  offsets=[];cursor=512
  for rows in blocks:offsets.append(cursor);cursor+=12+34*len(rows)
  struct.pack_into('<Q',header,12,offsets[0] if offsets else 0)
  out.write(header);out.seek(cursor);out.write(b'\0');converted=verified=0
  for bi,rows in enumerate(blocks):
   for values in rows:
    off,hs,cs,us,ha,crc,method=values
    if not off:continue
    assert hs<1048576 and cs<1073741824 and us<1073741824
    f.seek(off);meta=f.read(hs);data=f.read(cs);assert len(data)==cs
    if method==1:
     raw=decoder.decompress(data,max_output_size=us) if data.startswith(bytes.fromhex('28b52ffd')) else zlib.decompress(data)
     assert len(raw)==us
     packed=zlib.compress(raw,1)
     converted+=1
    elif method==0:raw=data;packed=data;assert len(raw)==us
    else:raise RuntimeError('Unsupported compression: '+str(method))
    values[0]=out.tell();values[2]=len(packed);out.write(meta);out.write(packed)
    end=out.tell();out.seek(values[0]+hs);check=out.read(len(packed))
    assert (zlib.decompress(check) if method else check)==raw
    verified+=1;out.seek(end)
   end=out.tell();out.seek(offsets[bi]);out.write(struct.pack('<IQ',len(rows),offsets[bi+1] if bi+1<len(blocks) else 0))
   for values in rows:out.write(entry.pack(*values))
   out.seek(end)
 tmp.rename(dst)
 with src.open('rb') as f:sh=hashlib.file_digest(f,'sha256').hexdigest()
 with dst.open('rb') as f:dh=hashlib.file_digest(f,'sha256').hexdigest()
 row=dict(archive=name,converted=converted,verified=verified,source_bytes=src.stat().st_size,output_bytes=dst.stat().st_size,source_sha256=sh,output_sha256=dh)
 report['archives'].append(row);report_path.write_text(json.dumps(report,indent=2));print(f'Finished {name}: {verified} payloads verified',flush=True)
print('ALL ARCHIVES COMPLETE',flush=True)
