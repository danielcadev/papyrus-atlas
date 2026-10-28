"""Coordinate and topology helpers for the second frozen CT crop."""
from collections import Counter
import json
import os
from pathlib import Path
import struct
import numpy as np

ROOT=Path(__file__).resolve().parent
OFFSET_X=int(os.environ.get('SPLIT_VALIDATION_OFFSET_X','0'))
assert OFFSET_X in [0,32]
DEST=ROOT/'scrollfiesta-comparison'/('independent-central32' if OFFSET_X==0 else 'independent-xplus32')

def load_stage(mode,stage):
    files=list((DEST/f'{mode}-obj').glob(f'*/*{stage}/*_all.vmesh'))
    assert len(files)==1,(mode,stage,files)
    payload=files[0].read_bytes()
    magic,version,endian,flags,header,nv,nf,vo,uo,fo=struct.unpack('<8sIIIIQQQQQ',payload[:64])
    assert (magic,version,endian,flags,header)==(b'VESMESH1',1,0x01020304,0,64)
    assert vo==64 and uo==0 and fo==64+12*nv and len(payload)==fo+12*nf
    v=np.frombuffer(payload,dtype='<f4',count=nv*3,offset=vo).reshape(-1,3).astype(float)
    f=np.frombuffer(payload,dtype='<i4',count=nf*3,offset=fo).reshape(-1,3).copy()
    assert f.min()>=0 and f.max()<len(v)
    origin=json.loads((DEST/'frozen-input.json').read_text())['parent_world_origin_zyx']
    return (v-origin)[:,::-1],f,files[0]

def face_components(v,f):
    parent=np.arange(len(v))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return int(i)
    for a,b,c in f:parent[find(b)]=find(a);parent[find(c)]=find(a)
    return np.array([find(int(a)) for a in f[:,0]])

def boundary_indices(f):
    counts=Counter(tuple(sorted(e)) for a,b,c in f for e in [(a,b),(b,c),(c,a)])
    return np.array(sorted({i for e,count in counts.items() if count==1 for i in e}),dtype=int)

def areas(tri):
    return np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2

def point_to_triangles(tri,point):
    a,b,c=tri[:,0],tri[:,1],tri[:,2];u,v,w=b-a,c-a,point-a
    uu,uv,vv=(u*u).sum(1),(u*v).sum(1),(v*v).sum(1)
    wu,wv=(w*u).sum(1),(w*v).sum(1);denom=uu*vv-uv*uv
    safe=np.where(denom>1e-14,denom,1)
    s,r=(vv*wu-uv*wv)/safe,(uu*wv-uv*wu)/safe
    inside=(denom>1e-14)&(s>=0)&(r>=0)&(s+r<=1)
    dist=np.where(inside,np.linalg.norm(a+s[:,None]*u+r[:,None]*v-point,axis=1),np.inf)
    for l,h in [(a,b),(b,c),(c,a)]:
        e=h-l;t=np.clip(((point-l)*e).sum(1)/np.maximum((e*e).sum(1),1e-20),0,1)
        dist=np.minimum(dist,np.linalg.norm(l+t[:,None]*e-point,axis=1))
    return dist
