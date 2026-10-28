"""Compare new geometry to frozen v2; preserve every historical artifact."""
from pathlib import Path
import json,struct,itertools,subprocess,hashlib
import numpy as np
from guard import start_guard
from independent_split_common import areas,point_to_triangles
from inspect_cube import read_nrrd
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';d=b/'holefill-repair-v4'
old=b/'fresh-yplus32-v2'
def read(folder,stage):
    paths=list(folder.glob(f'*/*{stage}/*_all.vmesh'));assert len(paths)==1,paths
    path=paths[0];data=path.read_bytes();h=struct.unpack('<8sIIIIQQQQQ',data[:64])
    v=np.frombuffer(data,dtype='<f4',count=h[5]*3,offset=h[7]).reshape(-1,3)
    f=np.frombuffer(data,dtype='<i4',count=h[6]*3,offset=h[9]).reshape(-1,3)
    return (v-[1808,2320,4112])[:,::-1],f,path
def keys(v,f):return {tuple(sorted(map(tuple,t))) for t in v[f]}
v,f,path=read(d/'y32-obj','step11_kibble');ov,of,op=read(old/'corrected-obj','step11_kibble')
pre_v,pre_f,pre=read(d/'y32-obj','step7_cc_bpa')
_,_,oldpre=read(old/'corrected-obj','step7_cc_bpa')
assert pre.read_bytes()==oldpre.read_bytes()
log=(p/'native/hf-full-y32-v4-01.log').read_text()
assert 'Status: OK' in log and 'boundary recovery: 27 faces' in log
assert 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in log
newkeys,oldkeys,prekeys=keys(v,f),keys(ov,of),keys(pre_v,pre_f)
assert prekeys<=newkeys,'All pre-fill source geometry must remain'
audit=d/'y32-audit.json';assert not audit.exists()
subprocess.run([str(b/'build/saved_geometry_audit.independent'),str(path),str(audit),str(d/'y32-pairs.csv'),'1808','2320','4112'],check=True)
tri=v[f];samples=[]
for t in tri:
    n=max(1,int(np.ceil(max(np.linalg.norm(t[1]-t[0]),np.linalg.norm(t[2]-t[0]),np.linalg.norm(t[2]-t[1]))/.75)))
    uv=[]
    for i in range(n):
        for j in range(n-i):
            uv.append(((i+1/3)/n,(j+1/3)/n))
            if i+j<n-1:uv.append(((i+2/3)/n,(j+2/3)/n))
    uv=np.asarray(uv);samples.append(t[0]+uv[:,0,None]*(t[1]-t[0])+uv[:,1,None]*(t[2]-t[0]))
samples=np.concatenate(samples);assert len(samples)<1000000
labels,_=read_nrrd(p/'data/01744_02256_04048_mask.nrrd')
frozen=json.loads((old/'frozen-input.json').read_text());lo,hi=np.array(frozen['active_roi_source_xyz'])
covered=set();rounded=np.rint(samples).astype(int)
for delta in itertools.product((-1,0,1),repeat=3):
    q=rounded+delta;close=np.linalg.norm(q-samples,axis=1)<=1;ref=q+64
    good=close&((ref>=lo)&(ref<hi)).all(1)
    ref=ref[good];ref=ref[labels[tuple(ref.T)]>0]
    covered.update(np.ravel_multi_index(ref.T,labels.shape))
probes=json.loads((old/'frozen-source-probes.json').read_text())
dist=np.array([float(point_to_triangles(tri,q).min()) for q in probes['boundary_parent_xyz']])
np.save(d/'y32-boundary-distances.npy',dist)
result=dict(pre_fill_byte_identical=True,all_source_geometry_preserved=True,boundary_graft_faces=27,
    final_faces_before=len(of),final_faces_after=len(f),vertices_before=len(ov),vertices_after=len(v),
    unique_faces_removed=len(oldkeys-newkeys),unique_faces_added=len(newkeys-oldkeys),
    area_voxel2=float(areas(tri).sum()),reference_coverage_radius1=len(covered),
    boundary_max=float(dist.max()),boundary_farther_than1=int((dist>1).sum()),
    geometry_audit=json.loads(audit.read_text()),guard_changes=0,
    binary_sha256=hashlib.sha256((b/'build/cube_mesh.holefill-v4').read_bytes()).hexdigest(),
    limitation='One uncertifiable 19-vertex fill stays open in chart mode; no source face removed. Same cube/scroll, no halo/seam validation.')
out=d/'y32-comparison.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
