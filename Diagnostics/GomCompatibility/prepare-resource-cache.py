"""Extract observed startup resources; do not alter archives or invent data."""
import pathlib, subprocess, sys, struct, zlib, json, hashlib
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'python-deps'))
import zstandard
root=pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets')
names=set()
for log in [here/'trace-field-isolation-confirm.txt',here/'trace-resource-bridge.txt']:
 if log.exists():
  for line in log.read_text(errors='replace').splitlines():
   if line.startswith('REQUEST PATH: /'):
    name=line[len('REQUEST PATH: '):].strip()
    if '..' not in name and '\\' not in name and ':' not in name:names.add(name)
names.update('/systemgenerated/buckets/%d.bkt'%i for i in range(997))
names.add('/world/livecontent/systemgenerated/3758002374/area.dat')
names.add('/art/defaultassets/missing_material_d.tex')
names.add('/art/defaultassets/missing_material_d.dds')
hashed=subprocess.run([str(here/'HashPaths.exe')],input='\n'.join(sorted(names))+'\n',text=True,capture_output=True,check=True).stdout
wanted={int(line.split('\t')[0],16):line.split('\t')[1] for line in hashed.splitlines()}
cache=here/'ResourceCache';cache.mkdir(exist_ok=True)
report=[];seen=set()
for archive in sorted(root.glob('*.tor')):
 with archive.open('rb') as f:
  head=f.read(36)
  if head[:4]!=b'MYP\0':continue
  table=struct.unpack_from('<Q',head,12)[0];visited=set()
  while table:
   assert table not in visited;visited.add(table)
   f.seek(table);count,table=struct.unpack('<IQ',f.read(12));assert count<1000000
   entries=[struct.unpack('<QIIIQIH',f.read(34)) for _ in range(count)]
   for offset,meta,packed,size,h,crc,method in entries:
    if h not in wanted or h in seen or not offset:continue
    name=wanted[h];f.seek(offset+meta);data=f.read(packed);assert len(data)==packed
    if method==0:raw=data;codec='stored'
    elif method==1 and data.startswith(bytes.fromhex('28b52ffd')):raw=zstandard.ZstdDecompressor().decompress(data,max_output_size=size);codec='zstandard'
    elif method==1:raw=zlib.decompress(data);codec='zlib'
    else:raise ValueError('Unsupported compression '+str(method))
    assert len(raw)==size
    target=cache/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    report.append(dict(path=name,archive=archive.name,codec=codec,size=size,sha256=hashlib.sha256(raw).hexdigest()));seen.add(h)
(here/'resource-cache.json').write_text(json.dumps(dict(extracted=report,missing=[name for h,name in wanted.items() if h not in seen]),indent=2))
print('Extracted',len(report),'resources;',sum(r['size'] for r in report),'bytes;',len(wanted)-len(seen),'not found')
