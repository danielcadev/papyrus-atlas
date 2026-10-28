"""Cold-start CT registration with spatially disjoint newly withheld controls."""
from pathlib import Path
import itertools,json,sys,time,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
from inspect_cube import read_nrrd
out=root/'paris4-independent-controls-v1';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'script.py')
prior=root/'paris4-ink-benefit-v2/ct-registration-v3'
baseplan=json.loads((prior/'plan.json').read_text());A=np.array(baseplan['affine_oldXYZ_to_modernXYZ'])
B=A[:,:3][::-1,::-1];O=np.array([1744,2256,4048]);center=np.array([128,160,128]);gridlow=np.array([84,116,84])
# Fixed geometrical design; no intensities or previous fitted parameters choose it.
blocks=[([120,124,116],[136,132,132]),([120,188,116],[136,196,132]),
        ([120,152,92],[136,168,100]),([120,152,156],[136,168,164]),
        ([156,152,116],[164,168,132])]
reserve_box=([88,148,116],[96,164,132]);guard_box=([108,140,108],[148,180,148])
shifts=[(0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)]
plan=dict(guard=guard,training_blocks_native_zyx=blocks,reserve_box_native_zyx=reserve_box,
    target_guard_box_native_zyx=guard_box,initializer='Catalogue affine plus exactly zero residual; no prior optimized parameters.',
    residual_translation_bounds=[-2,2],residual_linear_entry_bounds=[-.01,.01],
    local_translation_fit=dict(max_evaluations_each=256,max_seconds_each=30,role='Training-only spatial diagnostic, never used to initialize or select global fit.'),
    global_affine_fit=dict(max_evaluations=2048,max_seconds=120,objective='Concatenated training CT Pearson; fixed cold start.'),
    footprint='64 midpoint quadrature; cached-grid linear interpolation for fitting, direct observed CT interpolation for validation.',
    validation=dict(pearson_min=.6,margin_min=.1,shifts_native_zyx=shifts,require_both_reserve_and_original_ROI=True,no_parameter_boundary=True),
    independence='Newly withheld old/native targets in the same scans, not an independent scan, blind anatomy or letters. Prior nominal cache generation is intensity-only, not optimization.',
    original_ROI_previously_inspected=True,ink_used=False,geometry_or_uv_modified=False,
    source_ct_sha256=baseplan['source_ct_sha256'],catalogue_affine_oldXYZ_to_modernXYZ=A.tolist())
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def corners(box):return np.array(list(itertools.product(*zip(np.array(box[0]),np.array(box[1])-1))),float)
def swept(box,cache):
    p=corners(box);radius=2+.01*np.abs(p-center).sum(axis=1).max()
    # Conservative interval hull over every allowed residual parameter.
    # Cache interpolation adds <=1 native grid cell; midpoint quadrature <=.375.
    native_padding=radius+.375+(1 if cache else 0)+.01125
    q=(p+O)@B.T+A[:,3][::-1]
    modern_padding=np.abs(B).sum(axis=1)*native_padding+1
    return dict(lower=(q.min(axis=0)-modern_padding).tolist(),upper=(q.max(axis=0)+modern_padding).tolist(),native_radius=native_padding)
def disjoint(a,b):return bool(np.any(np.array(a['upper'])<b['lower']) or np.any(np.array(b['upper'])<a['lower']))
# Include all six controls before proving separation from every training support.
reserve_expanded=(np.array(reserve_box[0])-4,np.array(reserve_box[1])+4)
reserved_support=swept(reserve_expanded,False)
supports=[swept(box,True) for box in blocks]
assert all(disjoint(s,reserved_support) for s in supports)
# A native-coordinate projection bounds every moving modern raw interpolation
# support point too, rather than checking training centers alone.
projected_raw_padding=np.abs(np.linalg.inv(B)).sum(axis=1)
for box,support in zip(blocks,supports):
    pad=support['native_radius']+projected_raw_padding
    lower=np.array(box[0])-pad;upper=np.array(box[1])-1+pad
    assert np.any(upper<np.array(guard_box[0])) or np.any(np.array(guard_box[1])-1<lower)
# Reserve and its controls are outside the old/native repaired guard band.
assert np.array(reserve_expanded[1])[0]<=guard_box[0][0]
support_proof=dict(passed=True,training_swept_modern_support=supports,reserved_controls_swept_modern_support=reserved_support,
    includes_all_allowed_parameters=True,includes_cache_and_quadrature_and_raw_interpolation=True,
    old_guard_projection_padding=projected_raw_padding.tolist())
(out/'support-separation-before-fit.json').write_text(json.dumps(support_proof,indent=2)+'\n')
def points(box):return np.indices(tuple(np.array(box[1])-box[0])).reshape(3,-1).T+box[0]
training_blocks=[points(b) for b in blocks];training=np.concatenate(training_blocks)
reserved=points(reserve_box)
np.save(out/'training-native-zyx.npy',training,allow_pickle=False)
np.save(out/'reserved-native-zyx.npy',reserved,allow_pickle=False)
# Previous verified phase is read-only; validate its sealed bytes before reuse.
prev=root/'paris4-exterior-registration-v2';manifest=json.loads((prev/'evidence-manifest-v1.json').read_text())
for rel,row in manifest['files'].items():assert digest(prev/rel)==row['sha256']
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==plan['source_ct_sha256']
old,_=read_nrrd(source)
cached=root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy'
cache_receipt=json.loads((root/'paris4-exterior-collar-v1/cached-grid-receipt.json').read_text());assert digest(cached)==cache_receipt['sha256']
footprint=np.load(cached,allow_pickle=False)
(out/'input-receipt.json').write_text(json.dumps(dict(cached_grid_sha256=digest(cached),source_ct_sha256=digest(source),
    previous_sealed_files_unchanged=len(manifest['files']),previous_manifest_sha256=digest(prev/'evidence-manifest-v1.json')),indent=2)+'\n')
def transform(p,x):return (p-center)@(np.eye(3)+x[3:].reshape(3,3)).T+center+x[:3]
def corr(a,b):
    a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a-=a.mean();b-=b.mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))
def fit(p,affine):
    target=old[tuple(p.T)].astype(float);target-=target.mean();target/=np.linalg.norm(target)
    count=0;best=None;begin=time.monotonic();maximum=2048 if affine else 256;seconds=120 if affine else 30
    def objective(v):
        nonlocal count,best
        if count>=maximum or time.monotonic()-begin>seconds:raise TimeoutError()
        count+=1;x=v if affine else np.r_[v,np.zeros(9)]
        q=transform(p,x)-gridlow
        assert (q>=0).all() and np.all(q<np.array(footprint.shape)-1)
        values=map_coordinates(footprint,q.T,order=1,prefilter=False).astype(float);values-=values.mean()
        norm=np.linalg.norm(values);score=float(target@values/norm) if norm else -1.
        if best is None or score>best[0]:best=(score,np.array(v))
        return -score
    bounds=[(-2,2)]*3+([(-.01,.01)]*9 if affine else [])
    try:
        run=minimize(objective,np.zeros(len(bounds)),method='Powell',bounds=bounds,
            options=dict(maxfev=maximum,xtol=1e-4,ftol=1e-6));status=str(run.message);success=bool(run.success)
    except TimeoutError:status='bounded_fit_budget';success=False
    score,v=best
    boundary=any(abs(v[i])>=limit-1e-5 for i,limit in enumerate([2]*3+([.01]*9 if affine else [])))
    return dict(parameters=v.tolist(),training_pearson=score,evaluations=count,status=status,converged=success,
        at_parameter_boundary=boundary,elapsed_seconds=time.monotonic()-begin)
local=[]
for i,p in enumerate(training_blocks):
    row=fit(p,False);row['block']=i;row['center_native_zyx']=p.mean(axis=0).tolist();local.append(row)
    print(json.dumps(dict(stage='local_training_diagnostic',result=row)),flush=True)
(out/'local-training-displacements.json').write_text(json.dumps(local,indent=2)+'\n')
fitted=fit(training,True)
fitted['initializer_parameters']=[0.]*12;fitted['frozen_before_reserve_and_ROI']=True
(out/'global-fit-frozen-before-validation.json').write_text(json.dumps(fitted,indent=2)+'\n')
print(json.dumps(dict(stage='global_fit_frozen',fit=fitted)),flush=True)
x=np.array(fitted['parameters'])
portable=prior/'observed-modern-ct-zyx-portable.npy'
assert digest(portable)==json.loads((prior/'portable-array-receipt.json').read_text())['portable_sha256']
volume=np.load(portable,mmap_mode='r');sources=json.loads((prior/'ct-sources.json').read_text())
start=np.min([r['chunk'] for r in sources['chunks']],axis=0)*128
(out/'modern-input-receipt.json').write_text(json.dumps(dict(sha256=digest(portable),origin_modern_zyx=start.tolist(),shape=list(volume.shape)),indent=2)+'\n')
def sample(native):
    q=((native+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);f=q-lo
    assert (lo>=0).all() and np.all(lo+1<np.array(volume.shape))
    v=np.zeros(len(q))
    for c in itertools.product((0,1),repeat=3):
        c=np.array(c);v+=volume[tuple((lo+c).T)]*np.prod(np.where(c,f,1-f),axis=1)
    return v
validation={}
for name,box in (('new_reserved_control',reserve_box),('original_repaired_ROI',([112,144,112],[144,176,144]))):
    low=np.array(box[0])-4;shape=tuple(np.array(box[1])-box[0]+8)
    p=np.indices(shape).reshape(3,-1).T+low;total=np.zeros(len(p))
    for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):
        for j in range(0,len(p),32768):total[j:j+32768]+=sample(transform(p[j:j+32768]+offset,x))/64
    averaged=total.reshape(shape).astype('<f4');np.save(out/(name+'-modern-footprint.npy'),averaged,allow_pickle=False)
    target=old[tuple(slice(a,b) for a,b in zip(*box))];np.save(out/(name+'-old-target.npy'),target,allow_pickle=False)
    scores={}
    for s in shifts:
        key='_'.join(map(str,s));slices=tuple(slice(4+d,4+d+n) for d,n in zip(s,target.shape))
        scores[key]=corr(target,averaged[slices])
    primary=scores['0_0_0'];control=max(v for k,v in scores.items() if k!='0_0_0');margin=primary-control
    validation[name]=dict(primary_pearson=primary,best_shift_control=control,margin=margin,
        controls_native_zyx=scores,gate_passed=bool(primary>=.6 and margin>=.1),
        previously_inspected=name=='original_repaired_ROI')
    print(json.dumps(dict(stage='validation',group=name,result=validation[name])),flush=True)
accepted=all(r['gate_passed'] for r in validation.values()) and not fitted['at_parameter_boundary'] and fitted['converged']
result=dict(guard=guard,validation=validation,global_fit=fitted,registration_accepted=accepted,
    anatomical_error_bound_voxels=None,geometry_or_uv_modified=False,ink_used=False,letters_verified=0,
    independently_withheld_within_same_scans=True,not_independent_scan_or_anatomical_truth=True,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(completed=True,accepted=accepted)),flush=True)
