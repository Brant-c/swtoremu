"""Bounded file-only search in the pinned April PE for known query names."""
import hashlib,json,struct
from pathlib import Path
out=Path(__file__).parent
p=Path(r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe')
b=p.read_bytes();sha=hashlib.sha256(b).hexdigest().upper()
assert sha=='2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe=struct.unpack_from('<I',b,60)[0];opt=pe+24;base=struct.unpack_from('<I',b,opt+28)[0]
sections=[]
for i in range(struct.unpack_from('<H',b,pe+6)[0]):
 s=opt+struct.unpack_from('<H',b,pe+20)[0]+i*40
 vs,rva,rs,ro=struct.unpack_from('<4I',b,s+8)
 sections.append((rva,rs,ro))
def va(off):
 for rva,rs,ro in sections:
  if ro<=off<ro+rs:return base+rva+off-ro
 return None
def find(raw):
 start=0;res=[]
 while True:
  off=b.find(raw,start)
  if off<0:break
  res.append(off);start=off+1
 return res
results=[]
for name in ['CollideRaySegment','CollideRaySegmentWithNormal','CollideBoundingBox','ciCollideInfoDebugger','RaySegmentIsObstructed']:
 for enc in ['ascii','utf-16le']:
  for off in find((name+'\0').encode(enc)):
   addr=va(off)
   refs=[] if addr is None else [va(x) for x in find(struct.pack('<I',addr))]
   results.append({'name':name,'encoding':enc,'file_offset':hex(off),'va':hex(addr) if addr else None,'references':[hex(x) for x in refs if x]})
hashes=[]
for name,key in [('CollideRaySegment',0xEA7C38E8),('RaySegmentIsObstructed',0xDA6FB8A1)]:
 refs=[{'file_offset':hex(x),'va':hex(va(x)) if va(x) else None,'context':b[max(0,x-16):x+24].hex()} for x in find(struct.pack('<I',key))]
 hashes.append({'name':name,'key':hex(key),'source':'Jedipedia sysBaseClient name dictionary entries270/269','references':refs})
(out/'native-query-names.json').write_text(json.dumps({'sha256':sha,'strings':results,'name_hashes':hashes},indent=2)+'\n')
for r in results:print(r['name'],r['encoding'],r['va'],r['references'])
for r in hashes:print(r['name'],r['key'],[v['va'] for v in r['references']])
