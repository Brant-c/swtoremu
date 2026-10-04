"""Locate candidate phase method registration hashes in the pinned PE."""
import hashlib,struct,json
from pathlib import Path
p=Path(r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\swtor-emu.exe'); b=p.read_bytes()
assert hashlib.sha256(b).hexdigest().upper()=='2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe=struct.unpack_from('<I',b,60)[0];opt=pe+24;base=struct.unpack_from('<I',b,opt+28)[0];sections=[]
for i in range(struct.unpack_from('<H',b,pe+6)[0]):
 s=opt+struct.unpack_from('<H',b,pe+20)[0]+i*40
 _,rva,size,raw=struct.unpack_from('<4I',b,s+8);sections.append((rva,size,raw))
def address(p):
 for rva,size,raw in sections:
  if raw<=p<raw+size:return hex(base+rva+p-raw)
 return None
results=[]
# Use observed name dictionary entries, rather than assuming hash normalization.
for name,h in {'GetPhaseInfo':0x9073beca,'GetPhase':0xa172bd52,'GetPhasedInstance':0x88b3771d,'OnPhasedInstanceUpdated':0xf44ec2d1}.items():
 raw=struct.pack('<I',h);cursor=0;refs=[]
 while True:
  pos=b.find(raw,cursor)
  if pos<0:break
  refs.append({'va':address(pos),'context':b[max(0,pos-8):pos+24].hex()});cursor=pos+1
 results.append({'name':name,'reader_dictionary_hash':hex(h),'references':refs})
Path(__file__).with_name('phase-binding-candidates.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
