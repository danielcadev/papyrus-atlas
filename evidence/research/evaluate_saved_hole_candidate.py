"""Combine the certified saved 17-face proposal with v4's other valid fills.

No remeshing or source changes. Reports material-coverage cues separately from
exact source preservation; annotations are post-hoc, never candidate inputs.
"""
from pathlib import Path
from collections import Counter
import json,struct,subprocess,itertools,hashlib
import numpy as np
from guard import start_guard
from independent_split_common import areas,point_to_triangles
from inspect_cube import read_nrrd
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';d=b/'hole-recovery-v5'
out=d/'saved-evaluation-02';assert not out.exists();out.mkdir()
def read(path):
    payload=path.read_bytes();h=struct.unpack('<8sIIIIQQQQQ',payload[:64]);assert h[:5]==(b'VESMESH1',1,0x01020304,0,64)
    return np.frombuffer(payload,dtype='<f4',count=h[5]*3,offset=h[7]).reshape(-1,3),np.frombuffer(payload,dtype='<i4',count=h[6]*3,offset=h[9]).reshape(-1,3)
def stage(folder,name):
    files=list(folder.glob(f'*/*{name}/*_all.vmesh'));assert len(files)==1;return files[0]
oldroot=b/'fresh-yplus32-v2';v4=b/'holefill-repair-v4/y32-obj'
source=stage(v4,'step7_cc_bpa');v4path=stage(v4,'step11_kibble');oldpath=stage(oldroot/'corrected-obj','step11_kibble')
sv,sf=read(source);v,f=read(v4path);cv,cf=read(d/'candidate-boundary-only-01.vmesh');ov,of=read(oldpath)
assert np.array_equal(sv,v) and np.array_equal(sv,cv)
assert np.array_equal(cf[:len(sf)],sf)
# Pipeline dumps concatenate per-component source/fill blocks; final faces
# need not retain the combined step7 order even when every face survives.
cyclic=lambda t:min(tuple(t),tuple(t[1:])+tuple(t[:1]),tuple(t[2:])+tuple(t[:2]))
assert not Counter(map(cyclic,sf))-Counter(map(cyclic,f))
assert len(cf)-len(sf)==17 and len(f)-len(sf)==4
faces=np.concatenate([f,cf[len(sf):]])
candidate=out/'combined.vmesh'
with candidate.open('xb') as stream:
    stream.write(struct.pack('<8sIIIIQQQQQ',b'VESMESH1',1,0x01020304,0,64,len(v),len(faces),64,0,64+len(v)*12))
    stream.write(v.astype('<f4',copy=False).tobytes());stream.write(faces.astype('<i4',copy=False).tobytes())
subprocess.run(['python3',str(p/'exact_patch_intersections.py'),'--source',str(v4path),'--candidate',str(candidate),'--output',str(out/'strict.json')],check=True)
subprocess.run([str(b/'build/saved_geometry_audit.independent'),str(candidate),str(out/'native.json'),str(out/'native-pairs.csv'),'1808','2320','4112'],check=True)
audit=json.loads((out/'native.json').read_text());assert audit['conflicts']==0
local=(v-[1808,2320,4112])[:,::-1];tri=local[faces]
oldtri=((ov-[1808,2320,4112])[:,::-1])[of]
key=lambda t:tuple(sorted(map(tuple,t)))
beforekeys={key(t) for t in local[f]}
removed=np.array([t for t in oldtri if key(t) not in beforekeys])
def sample(triangles):
    samples=[];weights=[]
    for t,a in zip(triangles,areas(triangles)):
        n=max(1,int(np.ceil(max(np.linalg.norm(t[1]-t[0]),np.linalg.norm(t[2]-t[0]),np.linalg.norm(t[2]-t[1]))/.75)))
        uv=[]
        for i in range(n):
            for j in range(n-i):
                uv.append(((i+1/3)/n,(j+1/3)/n))
                if i+j<n-1:uv.append(((i+2/3)/n,(j+2/3)/n))
        uv=np.asarray(uv);samples.append(t[0]+uv[:,0,None]*(t[1]-t[0])+uv[:,1,None]*(t[2]-t[0]));weights.append(np.full(n*n,a/(n*n)))
    return np.concatenate(samples),np.concatenate(weights)
samples,weights=sample(tri);assert len(samples)<=1000000
labels,_=read_nrrd(p/'data/01744_02256_04048_mask.nrrd')
frozen=json.loads((oldroot/'frozen-input.json').read_text());lo,hi=np.array(frozen['active_roi_source_xyz'])
prediction=np.load(oldroot/'prediction.npy')>0;rounded=np.rint(samples).astype(int)
covered=set();supported=np.zeros(len(samples),dtype=bool)
for delta in itertools.product((-1,0,1),repeat=3):
    q=rounded+delta;close=np.linalg.norm(q-samples,axis=1)<=1
    good=close&((q>=0)&(q<128)).all(1);ix=np.flatnonzero(good);supported[ix]|=prediction[tuple(q[ix,::-1].T)]
    ref=q+64;good=close&((ref>=lo)&(ref<hi)).all(1);ref=ref[good];ref=ref[labels[tuple(ref.T)]>0]
    covered.update(np.ravel_multi_index(ref.T,labels.shape))
coverage_ids=Counter(map(int,labels[np.unravel_index(np.array(sorted(covered),dtype=int),labels.shape)]))
probes=json.loads((oldroot/'frozen-source-probes.json').read_text())
boundary=np.array([float(point_to_triangles(tri,q).min()) for q in probes['boundary_parent_xyz']])
oldfill_samples,_=sample(removed)
oldfill_distance=np.array([float(point_to_triangles(tri,q).min()) for q in oldfill_samples])
new_samples,_=sample(local[cf[len(sf):]])
new_to_old=np.array([float(point_to_triangles(oldtri,q).min()) for q in new_samples])
stats=lambda a:dict(count=len(a),median=float(np.median(a)),p95=float(np.percentile(a,95)),max=float(a.max()),farther_than_quarter=int((a>.25).sum()),farther_than1=int((a>1).sum()))
result=dict(candidate=str(candidate),sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
    source_faces=len(sf),all_source_indices_and_coordinates_exact=True,other_v4_fill_faces_preserved=4,
    new_full_fill_faces=17,vertices=len(v),faces=len(faces),area_voxel2=float(areas(tri).sum()),
    reference_coverage_radius1=len(covered),reference_coverage_by_id=dict(coverage_ids),
    ct_otsu_supported_area_radius1=float(weights[supported].sum()),samples=len(samples),
    source_boundary=stats(boundary),old_rejected_fill_sample_distance_to_candidate=stats(oldfill_distance),
    new_fill_sample_distance_to_v2_surface=stats(new_to_old),native_audit=audit,
    strict_certificate=json.loads((out/'strict.json').read_text())['checks'],
    limitations=['Only saved float32 geometry; production replay still required',
                 'Exact source retention is proved; finite sample fidelity does not prove all old generated geometry is preserved',
                 'CT support and reference proximity do not certify anatomical identity or fibers'])
(out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
