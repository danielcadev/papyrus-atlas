"""CT-only residual registration with matched voxel-footprint fitting and validation."""
from pathlib import Path
import itertools,json,sys,time,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
from inspect_cube import read_nrrd
case=root/'paris4-registration-anchors-v1';out=case/'corrected-footprint-fit-v1'
out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
axis=json.loads((case/'signed-axis-v1/result.json').read_text());assert axis['candidate_same_scan_gate_passed']
assert axis['chosen_by_training']['permutation_nrrd_to_global_zyx']==[0,1,2] and not any(axis['chosen_by_training']['flips'])
prior=root/'paris4-ink-benefit-v2/ct-registration-v3'
plan0=json.loads((prior/'plan.json').read_text());A=np.array(plan0['affine_oldXYZ_to_modernXYZ'])
portable=prior/'observed-modern-ct-zyx-portable.npy';receipt=json.loads((prior/'portable-array-receipt.json').read_text())
assert digest(portable)==receipt['portable_sha256']
volume=np.load(portable,mmap_mode='r');sources=json.loads((prior/'ct-sources.json').read_text())
start=np.min([r['chunk'] for r in sources['chunks']],axis=0)*128
origin=np.array([1744,2256,4048]);source=root/'data/01744_02256_04048_volume.nrrd'
assert digest(source)==plan0['source_ct_sha256'];old,_=read_nrrd(source)
low=np.array([84,116,84]);shape=(88,)*3;center=np.array([128,160,128])
training=np.concatenate([np.indices((8,)*3).reshape(3,-1).T+np.array([96,128,96])+np.array(c)*56
    for c in itertools.product((0,1),repeat=3)])
target=old[tuple(training.T)].astype(float);target-=target.mean();target/=np.linalg.norm(target)
offsets=list(itertools.product((-.375,-.125,.125,.375),repeat=3))
(out/'plan.json').write_text(json.dumps(dict(guard=guard,axis_evidence_sha256=digest(case/'signed-axis-v1/result.json'),
    source_ct_sha256=digest(source),fit_samples='Same exterior 8*8^3 CT blocks; repaired ROI excluded.',
    matched_footprint='Both use the same 4^3 midpoint cell quadrature. Fit uses trilinear interpolation of the integer footprint grid; validation computes quadrature directly.',
    footprint_grid_origin_native_zyx=low.tolist(),footprint_grid_shape=shape,
    residual_translation_bounds=[-4,4],residual_linear_entry_bounds=[-.01,.01],
    max_fit_evaluations=1024,max_fit_seconds=90,fit_objective='Exterior CT Pearson only.',
    validation_gate=dict(pearson_min=.6,margin_over_six_shift_controls_min=.1,no_parameter_boundary=True),
    ink_used=False,source_geometry_modified=False),indent=2))
def sample(native):
    q=((native+origin)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);frac=q-lo
    assert (lo>=0).all() and np.all(lo+1<np.array(volume.shape))
    values=np.zeros(len(q))
    for corner in itertools.product((0,1),repeat=3):
        corner=np.array(corner);indices=lo+corner
        values+=volume[tuple(indices.T)]*np.prod(np.where(corner,frac,1-frac),axis=1)
    return values
grid=np.indices(shape).reshape(3,-1).T+low;total=np.zeros(len(grid))
for i,offset in enumerate(offsets):
    for j in range(0,len(grid),32768):total[j:j+32768]+=sample(grid[j:j+32768]+offset)
    if i%8==7:print(json.dumps(dict(stage='matched_footprint_grid',completed_offsets=i+1,total_offsets=64)),flush=True)
footprint=(total/64).reshape(shape).astype('<f4');del grid,total
np.save(out/'modern-footprint-grid-native-zyx.npy',footprint,allow_pickle=False)
initial=json.loads((case/'corrected-translation-v1/result.json').read_text())['chosen_shift_native_zyx']
begin=time.monotonic();evaluations=0;best=None
class Budget(Exception):pass
def transform(points,x):return (points-center)@(np.eye(3)+x[3:].reshape(3,3)).T+center+x[:3]
def objective(x):
    global evaluations,best
    if evaluations>=1024 or time.monotonic()-begin>90:raise Budget()
    evaluations+=1;q=transform(training,x)-low
    if np.any(q<0) or np.any(q>np.array(shape)-1):return 2.
    values=map_coordinates(footprint,q.T,order=1,prefilter=False,mode='nearest').astype(float)
    values-=values.mean();norm=np.linalg.norm(values)
    score=float(target@values/norm) if norm else -1.
    if best is None or score>best[0]:best=(score,x.copy())
    return -score
try:
    run=minimize(objective,np.r_[initial,np.zeros(9)],method='Powell',bounds=[(-4,4)]*3+[(-.01,.01)]*9,
        options=dict(maxfev=1024,xtol=1e-4,ftol=1e-6));status=str(run.message)
except Budget:status='bounded_fit_budget'
score,x=best
boundary=bool(np.any(abs(x[:3])>=3.9999) or np.any(abs(x[3:])>=.009999))
fit=dict(parameters=x.tolist(),training_pearson=score,evaluations=evaluations,status=status,
    at_parameter_boundary=boundary,residual_determinant=float(np.linalg.det(np.eye(3)+x[3:].reshape(3,3))),frozen_before_validation=True)
(out/'fit-frozen-before-validation.json').write_text(json.dumps(fit,indent=2))
grid=np.indices((40,)*3).reshape(3,-1).T+np.array([108,140,108]);total=np.zeros(len(grid))
for offset in offsets:
    for j in range(0,len(grid),32768):total[j:j+32768]+=sample(transform(grid[j:j+32768]+offset,x))
averaged=(total/64).reshape((40,)*3).astype('<f4')
np.save(out/'modern-footprint-corrected-affine-native-zyx.npy',averaged,allow_pickle=False)
def corr(a,b):return float(np.corrcoef(a.ravel(),b.ravel())[0,1])
validation={};heldout=old[112:144,144:176,112:144]
for shift in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
    validation['_'.join(map(str,shift))]=corr(heldout,averaged[tuple(slice(4+i,36+i) for i in shift)])
primary=validation['0_0_0'];control=max(v for k,v in validation.items() if k!='0_0_0')
result=dict(guard=guard,fit=fit,primary_pearson=primary,best_shift_control=control,margin=primary-control,
    pearson_by_control_native_zyx=validation,diagnostic_structural_coherence_gate_passed=bool(primary>=.6 and primary-control>=.1 and not boundary),
    ink_used=False,letters_verified=0,source_geometry_modified=False,anatomical_registration_error_voxels=None,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
