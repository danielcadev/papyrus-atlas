"""Fit exterior CT central differences; retain the original raw CT admission gate."""
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
case=root/'paris4-registration-anchors-v1';out=root/'paris4-exterior-gradient-v1'
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
# A closer exterior shell; the repaired ROI plus four voxels is excluded.
points=np.indices((29,)*3).reshape(3,-1).T*2+np.array([100,132,100])
inside=np.all((points>=np.array([108,140,108])) & (points<np.array([148,180,148])),axis=1)
points=points[~inside]
reserve=((points[:,0]-100)//2+(points[:,1]-132)//2+(points[:,2]-100)//2)%2==1
training=points[~reserve];reserved=points[reserve]
np.save(out/'training-native-zyx.npy',training,allow_pickle=False)
np.save(out/'reserved-exterior-native-zyx.npy',reserved,allow_pickle=False)
assert not np.any(np.all((training>=np.array([108,140,108])) & (training<np.array([148,180,148])),axis=1))
directions=np.eye(3,dtype=int)
def old_gradient(points):
    return np.concatenate([old[tuple((points+d).T)].astype(float)-old[tuple((points-d).T)].astype(float) for d in directions])
target=old_gradient(training);target-=target.mean();target/=np.linalg.norm(target)
offsets=list(itertools.product((-.375,-.125,.125,.375),repeat=3))
(out/'plan.json').write_text(json.dumps(dict(guard=guard,axis_evidence_sha256=digest(case/'signed-axis-v1/result.json'),
    source_ct_sha256=digest(source),fit_samples='Even-parity samples of a 2-voxel exterior collar grid; repair ROI and four-voxel guard band excluded.', reserved_samples='Odd-parity exterior samples, never used by optimizer; spatially interleaved and not an independent scan.', training_count=len(training), reserved_count=len(reserved),
    matched_footprint='Both use the same 4^3 midpoint cell quadrature. Fit uses trilinear interpolation of the integer footprint grid; validation computes quadrature directly.',
    footprint_grid_origin_native_zyx=low.tolist(),footprint_grid_shape=shape,
    residual_translation_bounds=[-4,4],residual_linear_entry_bounds=[-.01,.01],
    max_fit_evaluations=2048,max_fit_seconds=120,fit_objective='Pearson of concatenated three-axis central CT differences on exterior training points only; raw ROI validation is unchanged.',
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
cached=case/'corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy'
footprint=np.load(cached);assert footprint.shape==shape
(out/'cached-grid-receipt.json').write_text(json.dumps(dict(path=str(cached.relative_to(root)),sha256=digest(cached)),indent=2))
initial=np.array(json.loads((case/'corrected-footprint-fit-v1/fit-frozen-before-validation.json').read_text())['parameters'])
begin=time.monotonic();evaluations=0;best=None
class Budget(Exception):pass
def transform(points,x):return (points-center)@(np.eye(3)+x[3:].reshape(3,3)).T+center+x[:3]
def objective(x):
    global evaluations,best
    if evaluations>=2048 or time.monotonic()-begin>120:raise Budget()
    evaluations+=1;q=transform(training,x)-low
    if np.any(q<0) or np.any(q>np.array(shape)-1):return 2.
    values=np.concatenate([
        map_coordinates(footprint,(transform(training+d,x)-low).T,order=1,prefilter=False)-
        map_coordinates(footprint,(transform(training-d,x)-low).T,order=1,prefilter=False)
        for d in directions]).astype(float)
    values-=values.mean();norm=np.linalg.norm(values)
    score=float(target@values/norm) if norm else -1.
    if best is None or score>best[0]:best=(score,x.copy())
    return -score
try:
    run=minimize(objective,initial,method='Powell',bounds=[(-4,4)]*3+[(-.01,.01)]*9,
        options=dict(maxfev=2048,xtol=1e-4,ftol=1e-6));status=str(run.message)
except Budget:status='bounded_fit_budget'
score,x=best
boundary=bool(np.any(abs(x[:3])>=3.9999) or np.any(abs(x[3:])>=.009999))
fit=dict(parameters=x.tolist(),training_pearson=score,evaluations=evaluations,status=status,
    at_parameter_boundary=boundary,residual_determinant=float(np.linalg.det(np.eye(3)+x[3:].reshape(3,3))),frozen_before_validation=True)
(out/'fit-frozen-before-validation.json').write_text(json.dumps(fit,indent=2))
# Evaluate reserved exterior data only after freezing the fitted parameters.
reference=old_gradient(reserved)
def extcorr(params):
    values=np.concatenate([
        map_coordinates(footprint,(transform(reserved+d,params)-low).T,order=1,prefilter=False)-
        map_coordinates(footprint,(transform(reserved-d,params)-low).T,order=1,prefilter=False)
        for d in directions])
    return float(np.corrcoef(reference,values)[0,1])
fit['reserved_exterior_gradient_pearson']=extcorr(x)
fit['reserved_exterior_initial_gradient_pearson']=extcorr(initial)
print(json.dumps(dict(stage='fit_frozen',fit=fit)),flush=True)
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
