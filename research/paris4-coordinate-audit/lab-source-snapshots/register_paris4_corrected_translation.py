"""Exterior CT-only translation after independently validated axis correction."""
from pathlib import Path
import itertools,json,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
from inspect_cube import read_nrrd
root=Path(__file__).resolve().parent;case=root/'paris4-registration-anchors-v1'
out=case/'corrected-translation-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
axis=json.loads((case/'signed-axis-v1/result.json').read_text());assert axis['candidate_same_scan_gate_passed']
assert axis['chosen_by_training']['permutation_nrrd_to_global_zyx']==[0,1,2] and not any(axis['chosen_by_training']['flips'])
prior=root/'paris4-ink-benefit-v2/ct-registration-v3'
record=json.loads((prior/'result.json').read_text())
for name,sha in record['artifacts'].items():assert digest(prior/name)==sha
repair=json.loads((prior/'portable-array-receipt.json').read_text())
portable=prior/'observed-modern-ct-zyx-portable.npy';assert digest(portable)==repair['portable_sha256']
volume=np.load(portable,mmap_mode='r');sources=json.loads((prior/'ct-sources.json').read_text())
start=np.min([r['chunk'] for r in sources['chunks']],axis=0)*128
plan0=json.loads((prior/'plan.json').read_text());A=np.array(plan0['affine_oldXYZ_to_modernXYZ'])
origin=np.array([1744,2256,4048]);source=root/'data/01744_02256_04048_volume.nrrd'
assert digest(source)==plan0['source_ct_sha256'];old,_=read_nrrd(source)
training=np.concatenate([np.indices((8,)*3).reshape(3,-1).T+np.array([96,128,96])+np.array(c)*56
    for c in itertools.product((0,1),repeat=3)])
target=old[tuple(training.T)]
coarse=np.load(prior/'modern-point-resampled-exterior-xyz.npy',allow_pickle=False).transpose(2,1,0)
low=np.array([84,116,84]);offsets=list(itertools.product(range(-4,5),repeat=3))
(out/'plan.json').write_text(json.dumps(dict(guard=guard,axis_evidence_sha256=digest(case/'signed-axis-v1/result.json'),
    training='Same eight exterior 8^3 blocks, outside repaired ROI and four-voxel guard band.',
    coarse_shifts_native_zyx=offsets,fine_rule='9^3 shifts at 0.25 native-voxel spacing within +/-1 of coarse winner.',
    fit_objective='CT-only Pearson on point samples; no ink or repaired ROI in fit.',
    validation='Same 64-point voxel footprint; Pearson>=.6, margin>=.1 over six +/-4-voxel controls.',
    no_boundary_fit_admission=True,source_geometry_modified=False),indent=2))
def corr(a,b):
    a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a-=a.mean();b-=b.mean()
    return float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)))
coarse_scores=[]
for shift in offsets:
    q=training+shift-low;coarse_scores.append((corr(target,coarse[tuple(q.T)]),shift))
coarse_scores.sort(reverse=True);initial=np.array(coarse_scores[0][1],float)
def sample(native):
    # Native NRRD indices are ZYX; catalogue input is XYZ.
    q=((native+origin)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);frac=q-lo;assert (lo>=0).all() and np.all(lo+1<np.array(volume.shape))
    values=np.zeros(len(q))
    for corner in itertools.product((0,1),repeat=3):
        corner=np.array(corner);indices=lo+corner
        values+=volume[tuple(indices.T)]*np.prod(np.where(corner,frac,1-frac),axis=1)
    return values
fine=[]
for delta in itertools.product(np.arange(-1,1.001,.25),repeat=3):
    shift=initial+delta;fine.append((corr(target,sample(training+shift)),shift.tolist()))
fine.sort(reverse=True);score,chosen=fine[0];chosen=np.array(chosen)
boundary=bool(np.any(np.abs(initial)==4) or np.any(np.abs(chosen-initial)>=.99999))
fit=dict(coarse_best_native_zyx=initial.tolist(),chosen_shift_native_zyx=chosen.tolist(),training_pearson=score,
    at_search_boundary=boundary,coarse_scores=[dict(pearson=s,shift=list(t)) for s,t in coarse_scores],
    fine_scores=[dict(pearson=s,shift=t) for s,t in fine],frozen_before_validation=True)
(out/'fit-frozen-before-validation.json').write_text(json.dumps(fit,indent=2))
grid=np.indices((40,)*3).reshape(3,-1).T+np.array([108,140,108])+chosen
total=np.zeros(len(grid))
for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):total+=sample(grid+offset)
averaged=(total/64).reshape((40,)*3).astype('<f4')
np.save(out/'modern-footprint-corrected-fitted-native-zyx.npy',averaged,allow_pickle=False)
validation={};target=old[112:144,144:176,112:144]
for shift in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
    validation['_'.join(map(str,shift))]=corr(target,averaged[tuple(slice(4+i,36+i) for i in shift)])
primary=validation['0_0_0'];control=max(v for k,v in validation.items() if k!='0_0_0')
result=dict(guard=guard,chosen_shift_native_zyx=chosen.tolist(),training_pearson=score,at_search_boundary=boundary,
    primary_pearson=primary,best_shift_control=control,margin=primary-control,
    pearson_by_control_native_zyx=validation,
    diagnostic_structural_coherence_gate_passed=bool(primary>=.6 and primary-control>=.1 and not boundary),
    anatomical_registration_error_voxels=None,source_geometry_modified=False,ink_used=False,letters_verified=0,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
