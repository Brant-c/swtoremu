import importlib.util,sys,json,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit_decoder',out.parent/'Decode-Style7Replication.py')
d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
s=d.read_schema()[0][26];assert len(s.fields)==215 and s.fields[25].definition==0x40000002641F28CC
captured=bytes.fromhex('CF4000010E218A839C');reports=[]
for node in [0x4000010E218A839B,0x4000010E218A1234]:
 label=f'{node:016X}'
 for number in [2,4]:
  b=(out/f'crt{number}-{label}.bin').read_bytes();r=d.Reader(b,16)
  flags=r.byte();count=r.packed();records=[d.read_object_record(b,r) for _ in range(count)]
  player=[x for x in records if x['node']==node];assert len(player)==1
  assert player[0]['structure_id']==26 and captured not in b
  if number==4:
   rec=player[0];assert b[rec['body_start']:rec['body_start']+6]==bytes.fromhex('CC1AC6F6DC1F')
 for handle in [8,19]:
  b=(out/f'clear-{label}-{handle}.bin').read_bytes();r=d.Reader(b,16)
  assert int.from_bytes(b[6:8],'little')==handle
  assert r.byte()==3 and r.packed()==2
  rec=d.read_object_record(b,r);assert rec['node']==node and captured not in b
  assert rec['flags']==9 and rec['style']==8 and rec['structure_id']==26 and rec['inner_size']==1
  assert b[rec['body_start']]==0
  states,_=d.field_states(b,rec['body_start']+1,54,215,style=rec['style'])
  assert states[25]==1 and all(x==2 for i,x in enumerate(states) if i!=25)
  d.read_object_record(b,r);assert r.packed()==1 and r.packed()==0x1AC6F6DC1F and r.pos==len(b)
  reports.append({'player':hex(node),'handle':handle,'sha256':hashlib.sha256(b).hexdigest().upper(),'bytes':len(b)})
assert hashlib.sha256((out/'default.bin').read_bytes()).hexdigest().upper()=='2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF'
(out/'selected-identity-verification.json').write_text(json.dumps(reports,indent=2))
print('PASS: startup CRT2/CRT4 and exit use same selected node; field25 only; retained removal; both handles; alternate character; default byte-identical.')
