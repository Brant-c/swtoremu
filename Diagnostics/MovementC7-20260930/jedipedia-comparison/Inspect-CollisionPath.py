"""Read only extracted BWAG v4 generated_collision meshes; no live memory.
Layout reference: https://github.com/SWTOR-Slicers/WikiPedia/wiki/GR2-File-Structure
This is geometry evidence, not proof of native collider registration/contact.
"""
import json, math, struct, hashlib
from pathlib import Path
OUT = Path(__file__).parent
ROOT = Path(r'D:\SWTORClassic\assettest\resources\art\static\area\all_all\arch\republic')
data = json.loads((OUT/'nearby-authored-objects.json').read_text())
stop = data['stop']
movement=json.loads((OUT/'movement-positions.json').read_text())
previous=movement[-3]['position']
heading=[stop[0]-previous[0],0,stop[2]-previous[2]]
length=math.sqrt(sum(v*v for v in heading))
heading=[v/length for v in heading]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def closest(p,a,b,c):
    ab=sub(b,a);ac=sub(c,a);ap=sub(p,a);d1=dot(ab,ap);d2=dot(ac,ap)
    if d1<=0 and d2<=0:return a
    bp=sub(p,b);d3=dot(ab,bp);d4=dot(ac,bp)
    if d3>=0 and d4<=d3:return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);return [a[j]+v*ab[j] for j in range(3)]
    cp=sub(p,c);d5=dot(ab,cp);d6=dot(ac,cp)
    if d6>=0 and d5<=d6:return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);return [a[j]+w*ac[j] for j in range(3)]
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));return [b[j]+w*(c[j]-b[j]) for j in range(3)]
    total=va+vb+vc
    if abs(total)<1e-20:return a
    v=vb/total;w=vc/total;return [a[j]+ab[j]*v+ac[j]*w for j in range(3)]
def ray(p,q,a,b,c):
    d=sub(q,p);e=sub(b,a);f=sub(c,a);h=cross(d,f);det=dot(e,h)
    if abs(det)<1e-10:return None
    t=sub(p,a);u=dot(t,h)/det
    if u < -1e-7 or u > 1+1e-7:return None
    j=cross(t,e);v=dot(d,j)/det
    if v < -1e-7 or u+v > 1+1e-7:return None
    s=dot(f,j)/det
    return s if 0<=s<=1 else None
def mesh(path):
    b=path.read_bytes()
    assert b[:4]==b'GAWB' and struct.unpack_from('<II',b,4)==(4,3)
    n=struct.unpack_from('<H',b,0x18)[0];off=struct.unpack_from('<I',b,0x54)[0]
    meshes=[]
    for i in range(n):
        nameoff,_,np,nb,flags,stride,nv,ni,vo,po,io,bo=struct.unpack_from('<If4H6I',b,off+40*i)
        assert 0<=nameoff<len(b)
        name=b[nameoff:b.index(b'\0',nameoff)].decode('ascii')
        if name!='generated_collision':continue
        assert stride==12 and nv<65536 and ni%3==0
        assert vo+nv*stride<=len(b) and io+ni*2<=len(b) and po+np*48<=len(b)
        verts=[struct.unpack_from('<3f',b,vo+j*stride) for j in range(nv)]
        assert all(math.isfinite(v) for p in verts for v in p)
        indices=struct.unpack_from('<'+'H'*ni,b,io)
        assert max(indices)<nv
        tris=[tuple(verts[k] for k in indices[j:j+3]) for j in range(0,ni,3)]
        pieces=[struct.unpack_from('<4i',b,po+j*48) for j in range(np)]
        assert sum(p[1] for p in pieces)==ni//3
        bounds=[[min(p[j] for p in verts) for j in range(3)],[max(p[j] for p in verts) for j in range(3)]]
        meshes.append({'name':name,'vertices':nv,'triangles':ni//3,'pieces':pieces,'bounds':bounds,'tris':tris})
    assert len(meshes)==1
    return b,meshes[0]
assert abs(ray([.2,.2,-1],[.2,.2,1],[0,0,0],[1,0,0],[0,1,0])-.5)<1e-8
assert ray([2,2,-1],[2,2,1],[0,0,0],[1,0,0],[0,1,0]) is None
assert max(abs(a-b) for a,b in zip(closest([.2,.2,1],[0,0,0],[1,0,0],[0,1,0]),[.2,.2,0]))<1e-8
assert closest([-1,-1,1],[0,0,0],[1,0,0],[0,1,0])==[0,0,0]
results=[]
for name,expected in [('all_arch_rep_jedi_retreat.gr2',9212),('all_arch_rep_jedi_retreat_interior_room.gr2',None)]:
    path=ROOT/name;b,m=mesh(path)
    if expected:assert m['triangles']==expected
    # Real-mesh positive control: cross a nondegenerate triangle at its centroid.
    for tri in m['tris']:
        normal=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]));n=math.sqrt(dot(normal,normal))
        if n<1e-6:continue
        centroid=[sum(p[j] for p in tri)/3 for j in range(3)]
        normal=[v/n*.01 for v in normal]
        hit=ray(sub(centroid,normal),[centroid[j]+normal[j] for j in range(3)],*tri)
        assert hit is not None and abs(hit-.5)<1e-6
        break
    else:raise AssertionError('No positive-control triangle')
    for obj in data['objects']:
        if not obj['asset'].endswith(name):continue
        def vec(k):return [float(v) for v in obj['properties'][k].strip('()').split(',')]
        pos=vec('Position');scale=vec('Scale');rot=vec('Rotation');assert abs(rot[0])+abs(rot[2])<.001
        item={'instance':obj['instance'],'room':obj['room'],'file':str(path),'sha256':hashlib.sha256(b).hexdigest(),'mesh':{k:v for k,v in m.items() if k!='tris'},'conventions':[]}
        for sign in [-1,1]:
            angle=math.radians(sign*rot[1]);c=math.cos(angle);s=math.sin(angle)
            def local(p):
                d=sub(p,pos)
                return [(c*d[0]-s*d[2])/scale[0],d[1]/scale[1],(s*d[0]+c*d[2])/scale[2]]
            tests=[]
            # World triangles used for distances, preserving authored scale.
            def world(p):
                x=p[0]*scale[0];z=p[2]*scale[2]
                return [pos[0]+c*x+s*z,pos[1]+p[1]*scale[1],pos[2]-s*x+c*z]
            worldtris=[tuple(world(p) for p in tri) for tri in m['tris']]
            # Use the last substantial captured approach direction in X/Z.
            # Heights are samples, not a measured player capsule.
            for height in [0,.03,.08,.13,.18]:
                p=[stop[j]-.3*heading[j] for j in range(3)];q=[stop[j]+.3*heading[j] for j in range(3)]
                p[1]+=height;q[1]+=height
                hits=[]
                sample=[stop[0],stop[1]+height,stop[2]];near=[]
                for idx,tri in enumerate(m['tris']):
                    t=ray(local(p),local(q),*tri)
                    if t is not None:
                        hit=[p[j]+t*(q[j]-p[j]) for j in range(3)]
                        hits.append({'triangle':idx,'t':t,'world':hit,'x_from_stop':hit[0]-stop[0]})
                    wt=worldtris[idx];nrm=cross(sub(wt[1],wt[0]),sub(wt[2],wt[0]));nlen=math.sqrt(dot(nrm,nrm))
                    if nlen<1e-10:continue
                    # Exclude horizontal floor/ceiling faces from the wall-near check.
                    if abs(nrm[1]/nlen)>.5:continue
                    nearest=closest(sample,*wt);dist=math.sqrt(dot(sub(sample,nearest),sub(sample,nearest)))
                    near.append({'triangle':idx,'distance_engine_units':dist,'world':nearest,'normal_y_abs':abs(nrm[1]/nlen)})
                tests.append({'height_engine_units':height,'start':p,'end':q,'hits':sorted(hits,key=lambda h:h['t']),'nearest_steep_faces':sorted(near,key=lambda n:n['distance_engine_units'])[:3]})
            item['conventions'].append({'angle_sign':sign,'tests':tests})
        results.append(item)
(OUT/'collision-path.json').write_text(json.dumps(results,indent=2)+'\n')
for r in results:
    print(r['instance'],r['mesh']['triangles'],[(x['angle_sign'],[len(t['hits']) for t in x['tests']]) for x in r['conventions']])
