"""Bounded authored asset comparison; origins are not collision bounds."""
from pathlib import Path
import re, json, hashlib, math, struct
out=Path(__file__).resolve().parent/'jedipedia-comparison'
out.mkdir(exist_ok=True)
area=Path('D:/SWTORClassic/assettest/resources/world/areas/4611686019869492753')
mapping=dict(re.findall(r'^  (\d+)=(\\[^\r\n]+)',(area/'area.dat').read_text(),re.M))
log=(Path(__file__).resolve().parent/'live-20260930-180457/NexusToR.log').read_text()
moves=[]
for line in log.splitlines():
    if 'AREA-POLL CMsg61116AD5: component' not in line: continue
    b=bytes.fromhex(line.split('body=')[1].replace('-',' '))
    mask=struct.unpack_from('<I',b)[0]
    xyz=struct.unpack_from('<fff',b,20 if mask==0xC7 else 8)
    moves.append({'timestamp':line[:21],'mask':hex(mask),'position':xyz})
stop=moves[-1]['position']
rows=[]; identities=[]
for name in ['gnarls_retreat_int_c.dat','gnarls_retreat_int_d.dat','gnarls_new.dat']:
    path=area/name; raw=path.read_bytes(); text=raw.decode().replace('\r','')
    identities.append({'file':str(path),'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest().upper()})
    blocks=re.split(r'(?=^  \d+=)',text,flags=re.M)
    for block in blocks:
        match=re.match(r'  (\d+)=(\d+)',block)
        if not match: continue
        p=dict(re.findall(r'^    \.(\w+)=(.*)$',block,re.M))
        pos=p.get('Position','')
        try: xyz=tuple(float(x) for x in pos.strip('()').split(','))
        except ValueError: continue
        distance=math.dist(xyz,stop)
        asset=mapping.get(match[2],match[2])
        if distance>5 and 'jedi_retreat' not in asset: continue
        keys=['Position','Rotation','Scale','ParentInstance','Collidable','IgnoreForPlayerCollision',
              'PhysicsType','PhysicsShape','PhysicsCollisionGroup','PortalTarget','TriggerType',
              'TriggerParam','TriggerDimensions','ExistsOnServer','Script','Visible','Hidden']
        rows.append({'room':name,'instance':match[1],'asset_id':match[2],'asset':asset,
                     'origin_distance_to_stop':distance,'properties':{k:p[k] for k in keys if k in p}})
rows.sort(key=lambda x:x['origin_distance_to_stop'])
(out/'nearby-authored-objects.json').write_text(json.dumps({'stop':stop,'limit':'Origins within5 engine units or retreat shell names; not mesh bounds or proof of live contacts','objects':rows},indent=2)+'\n')
(out/'source-identities.json').write_text(json.dumps(identities,indent=2)+'\n')
(out/'movement-positions.json').write_text(json.dumps(moves,indent=2)+'\n')
print('Stop:',stop,'; authored candidates:',len(rows))
for r in rows[:22]: print(r['room'],r['instance'],round(r['origin_distance_to_stop'],3),r['asset'],r['properties'].get('Collidable'),r['properties'].get('PortalTarget',''))
