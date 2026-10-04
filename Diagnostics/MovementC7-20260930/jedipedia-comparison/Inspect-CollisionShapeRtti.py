"""Find collision/shape RTTI vtables in the pinned local client, offline."""
from pathlib import Path
import struct, re, json, hashlib
out=Path(__file__).resolve().parent
b=Path(r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe').read_bytes()
assert hashlib.sha256(b).hexdigest().upper()=='2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe=struct.unpack_from('<I',b,60)[0];opt=pe+24;base=struct.unpack_from('<I',b,opt+28)[0]
sections=[]
for i in range(struct.unpack_from('<H',b,pe+6)[0]):
 s=opt+struct.unpack_from('<H',b,pe+20)[0]+i*40
 _,rva,rs,ro=struct.unpack_from('<4I',b,s+8);sections.append((rva,rs,ro))
def va(p):
 for rva,rs,ro in sections:
  if ro<=p<ro+rs:return base+rva+p-ro
 raise ValueError(hex(p))
def off(a):
 for rva,rs,ro in sections:
  if base+rva<=a<base+rva+rs:return ro+a-base-rva
 raise ValueError(hex(a))
def refs(a):
 raw=struct.pack('<I',a);return [m.start() for m in re.finditer(re.escape(raw),b)]
results=[]
for m in re.finditer(rb'\.\?AV[^\x00]{1,180}\x00',b):
 name=m.group()[:-1].decode('ascii',errors='replace')
 if not any(k in name.lower() for k in ['collision','collide']):continue
 desc=va(m.start()-8);tables=[]
 for ref in refs(desc):
  col=ref-12
  if col<0:continue
  sig,offset,cd,td,ch=struct.unpack_from('<5I',b,col)
  if sig!=0 or td!=desc:continue
  try: off(ch)
  except ValueError:continue
  for ptr in refs(va(col)):
   try:
    slots=struct.unpack_from('<24I',b,ptr+4)
    if not all(0x400000<=x<0x1060000 for x in slots[:8]):continue
    end=next((i for i,x in enumerate(slots) if not 0x400000<=x<0x1060000),len(slots))
    slots=slots[:end]
    tables.append({'vtable':hex(va(ptr+4)),'object_offset':offset,'slots':[hex(x) for x in slots]})
   except (ValueError,struct.error):continue
 results.append({'name':name,'descriptor':hex(desc),'vtables':tables})
(out/'collision-shape-rtti.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
