"""Verify bounded printed disassembly prefixes against the pinned April PE."""
from pathlib import Path
import hashlib,json,struct,re
out=Path(__file__).parent
b=Path(r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe').read_bytes()
assert hashlib.sha256(b).hexdigest().upper()=='2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe=struct.unpack_from('<I',b,60)[0];opt=pe+24;base=struct.unpack_from('<I',b,opt+28)[0];sections=[]
for i in range(struct.unpack_from('<H',b,pe+6)[0]):
 s=opt+struct.unpack_from('<H',b,pe+20)[0]+i*40
 _,rva,rs,ro=struct.unpack_from('<4I',b,s+8);sections.append((rva,rs,ro))
def offset(va):
 for rva,rs,ro in sections:
  if rva<=va-base<rva+rs:return ro+va-base-rva
 raise ValueError(hex(va))
vtable=0x10D98F4
def word(va):return struct.unpack_from('<I',b,offset(va))[0]
slots=[word(vtable+i*4) for i in range(10)]
col=word(vtable-4);descriptor=word(col+12);p=offset(descriptor)+8
identity={'vtable':hex(vtable),'slots':[hex(x) for x in slots],'rtti':b[p:b.index(b'\0',p)].decode('ascii')}
(out/'query-manager-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
ranges={'query-registration':(0xC191AC,0xC191E2),'query-signature':(0xC180D0,0xC18190),'query-wrapper':(0xC15380,0xC15560),'query-manager-initialization':(0x71AD60,0x71AEC0),'query-manager-factory':(0xD1F670,0xD1F6D0),'query-manager-constructor':(0xD1F4A0,0xD1F500),'query-world-slot':(slots[5],slots[5]+0x240)}
ranges.update({'query-result-init':(0xD023F0,0xD02480),'query-result-cleanup':(0xB5A5A0,0xB5A680),'query-scene-entry':(0xD1EA90,0xD1EB60)})
ranges.update({'query-filter-init':(0xD02750,0xD028A0),'query-result-modes':(0xD02040,0xD020E0),'query-result-materialize':(0xD02320,0xD023F0),'query-hit-point-materialize':(0xD02480,0xD02530)})
ranges.update({'query-result-reset':(0xD022E0,0xD02320),'query-broadphase':(0xD1E800,0xD1EA90)})
ranges.update({'query-positive-xz-traversal':(0xD17520,0xD17AA0)})
ranges.update({'query-collider-filter':(0xD134B0,0xD13800)})
ranges.update({'query-collider-dispatch':(0xD20020,0xD20300)})
ranges.update({'query-collider-vtable':(0xD1EF60,0xD1EFA0)})
ranges.update({'query-shape-tree-ray':(0xD20690,0xD20740),'query-shape-character-ray':(0xD27D80,0xD28000),'query-shape-heightfield-ray':(0xD4DAC0,0xD4DC50),'query-shape-box-ray':(0xD516D0,0xD51A00)})
ranges.update({'query-shape-tree-ray-detail':(0xD20960,0xD20A20),'query-shape-character-ray-detail':(0xD27F80,0xD281C0)})
ranges.update({'query-mesh-ray-dispatch':(0xD244B0,0xD24700)})
lines={k:[] for k in ranges};counts={k:0 for k in ranges};pattern=re.compile(r'^\s+([0-9A-F]{8}): ((?:[0-9A-F]{2} )+)\s*(.*)$')
with Path(r'D:\SWTORClassic\swtoremu\Diagnostics\swtor-disasm.txt').open(errors='replace') as f:
 for line in f:
  match=pattern.match(line)
  if not match:continue
  va=int(match[1],16)
  for key,(lo,hi) in ranges.items():
   if lo<=va<hi:
    raw=bytes.fromhex(match[2]);p=offset(va);assert b[p:p+len(raw)]==raw,hex(va)
    lines[key].append(line.rstrip());counts[key]+=1
for key,val in lines.items():
 assert val
 (out/(key+'.txt')).write_text('\n'.join(val)+'\n')
(out/'query-prefix-verification.json').write_text(json.dumps(counts,indent=2)+'\n')
print(json.dumps(counts))
print(json.dumps(identity))
