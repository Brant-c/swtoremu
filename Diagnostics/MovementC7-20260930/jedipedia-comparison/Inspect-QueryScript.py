import importlib.util,json,hashlib
from pathlib import Path
root=Path(r'D:\SWTORClassic\swtoremu');out=root/'Diagnostics/MovementC7-20260930/jedipedia-comparison'
spec=importlib.util.spec_from_file_location('refs',root/'Diagnostics/Inspect-V5ScriptGomRefs.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
p=Path(r'D:\SWTORClassic\assettest\resources\systemgenerated\compilednative\14988129110554817399');b=mod.script_payload(p);strings,offset=mod.string_table(b)
hits=[{'index':i,'name':s} for i,s in enumerate(strings) if any(k in s.lower() for k in ['collid','raysegment','obstruct','!ef','!hm'])]
print(json.dumps({'bytes':len(b),'body_offset':offset,'strings':len(strings),'hits':hits},indent=2))
(out/'sysBaseClient.payload.bin').write_bytes(b)
(out/'sysBaseClient.strings.json').write_text(json.dumps({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'body_offset':offset,'strings':strings},indent=2))
count,offset=mod.read_number(b,offset);names=[]
for i in range(count):
 value,offset=mod.read_number(b,offset);names.append(value)
assert count==414 and names[269]==0xda6fb8a1 and names[270]==0xea7c38e8
(out/'sysBaseClient.name-hashes.json').write_text(json.dumps({'count':count,'dictionary_end':offset,'names':[hex(n) for n in names]},indent=2))
print('Verified query name dictionary entries269/270:',hex(names[269]),hex(names[270]))
