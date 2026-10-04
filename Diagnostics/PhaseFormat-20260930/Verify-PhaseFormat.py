"""Validate April native style dispatch and old/new phase-clear field selection."""
from pathlib import Path
import importlib.util,sys,struct,hashlib,json
root=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('decoder',root/'Diagnostics/Decode-Style7Replication.py')
d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
pe_data=(root/'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
assert hashlib.sha256(pe_data).hexdigest().upper()=='2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe=struct.unpack_from('<I',pe_data,60)[0];opt=pe+24;base=struct.unpack_from('<I',pe_data,opt+28)[0]
def native(va,n):
 for i in range(struct.unpack_from('<H',pe_data,pe+6)[0]):
  s=opt+struct.unpack_from('<H',pe_data,pe+20)[0]+i*40
  _,rva,size,off=struct.unpack_from('<4I',pe_data,s+8)
  if base+rva<=va<base+rva+size:return pe_data[off+va-base-rva:off+va-base-rva+n]
 raise ValueError(hex(va))
assert native(0x5ac1cb,19)==bytes.fromhex('83 C0 F9 83 F8 03 0F 87 8F 03 00 00 FF 24 85 5C C6 5A 00')
assert struct.unpack('<4I',native(0x5ac65c,16))==(0x5ac358,0x5ac1de,0x5ac45f,0x5ac45f)
assert native(0x5ac3d3,9)==bytes.fromhex('6A 01 8B FB E8 D4 4A 00 00')
assert native(0x5ac27c,7)==bytes.fromhex('6A 02 E8 2D 4C 00 00')
# 005B0EB0 reads the requested number of MSB-first bits, already recovered.
assert native(0x5b0eb0,3)==bytes.fromhex('55 8B EC')
schema=d.read_schema()[0][26];names=d.name_table();reports=[]
for node in ['4000010E218A839B','4000010E218A1234']:
 for handle in [8,19]:
  name=f'clear-{node}-{handle}.bin'
  old=(out/('before-'+name)).read_bytes();new=(root/'Diagnostics/PhaseTransitionAudit-20260930'/name).read_bytes()
  delta=[(i,a,b) for i,(a,b) in enumerate(zip(old,new)) if a!=b]
  assert len(old)==len(new)==120 and len(delta)==1 and delta[0][1:]==(7,8)
  selections=[]
  for blob in [old,new]:
   r=d.Reader(blob,16);assert r.byte()==3 and r.packed()==2
   rec=d.read_object_record(blob,r)
   states,_=d.field_states(blob,rec['body_start']+rec['inner_size'],rec['value_end']-rec['body_start']-rec['inner_size'],215,style=rec['style'])
   present=[i for i,v in enumerate(states) if v!=2];selections.append(present)
  assert selections==[[51],[25]]
  reports.append({'node':node,'handle':handle,'changed_byte_offset':delta[0][0],'old_style7_fields':selections[0],'old_field51_name':names.get(schema.fields[51].definition),'new_style8_fields':selections[1],'new_field25_id':hex(schema.fields[25].definition),'new_sha256':hashlib.sha256(new).hexdigest().upper()})
# Independent small bit patterns prevent a shared, two-bit-only decoder from
# passing this regression merely because the generated mask looks familiar.
assert d.field_states(bytes([0x80]),0,1,2,style=7)[0]==[1,2]
assert d.field_states(bytes([0x80]),0,1,2,style=8)[0]==[0,2]
(out/'verification.json').write_text(json.dumps(reports,indent=2))
print('PASS native switch7/8 and bit widths; old phase mask targets field51, corrected style8 targets25; four fixture pairs differ by one byte only.')
print(json.dumps(reports[0],indent=2))
