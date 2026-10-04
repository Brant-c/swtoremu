import json, math, struct, hashlib
from pathlib import Path
out=Path(r'D:\SWTORClassic\swtoremu\Diagnostics\MovementC7-20260930\jedipedia-comparison')
root=Path(r'D:\SWTORClassic\assettest\resources\art\static\area\all_all\arch\republic')
objects=json.loads((out/'nearby-authored-objects.json').read_text())
stop=objects['stop']; results=[]
for name in ['all_arch_rep_jedi_retreat.gr2','all_arch_rep_jedi_retreat_interior_room.gr2']:
 p=root/name;b=p.read_bytes();assert b[:4]==b'GAWB' and struct.unpack_from('<I',b,4)[0]==4
 raw=struct.unpack_from('<8f',b,0x30);lo=raw[:3];hi=raw[4:7]
 for o in objects['objects']:
  if not o['asset'].endswith(name):continue
  def vec(k):return [float(v) for v in o['properties'][k].strip('()').split(',')]
  pos=vec('Position');scale=vec('Scale');rot=vec('Rotation');assert abs(rot[0])<.001 and abs(rot[2])<.001
  d=[stop[i]-pos[i] for i in range(3)]
  item={'file':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'instance':o['instance'],'room':o['room'],'header_model_bounds_engine_units':[lo,hi],'model_bounds_metres_reader_conversion':[[v*10 for v in lo],[v*10 for v in hi]],'authored_position':pos,'authored_y_rotation':rot[1],'stop':stop,'rotation_conventions':[]}
  for sign in [-1,1]:
   a=math.radians(sign*rot[1]);c=math.cos(a);s=math.sin(a)
   q=[(c*d[0]-s*d[2])/scale[0],d[1]/scale[1],(s*d[0]+c*d[2])/scale[2]]
   item['rotation_conventions'].append({'angle_sign':sign,'stop_local':q,'point_inside_model_AABB':all(lo[i]<=q[i]<=hi[i] for i in range(3))})
  results.append(item)
(out/'shell-model-bounds.json').write_text(json.dumps(results,indent=2)+'\n')
for r in results:print(r['instance'], [(x['angle_sign'],x['point_inside_model_AABB']) for x in r['rotation_conventions']])
