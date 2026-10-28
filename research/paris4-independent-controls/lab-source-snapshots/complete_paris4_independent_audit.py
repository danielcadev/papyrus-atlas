"""Complete support and local-fit replay without repeating prior experiments."""
from pathlib import Path
import itertools,json,sys
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;out=root/'paris4-independent-validation-v1'
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from inspect_cube import read_nrrd
base=root/'paris4-independent-controls-v1';plan=json.loads((base/'plan.json').read_text())
A=np.array(plan['catalogue_affine_oldXYZ_to_modernXYZ']);B=A[:,:3][::-1,::-1];O=np.array([1744,2256,4048]);center=np.array([128,160,128])
cache=root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy'
assert digest(cache)==json.loads((base/'input-receipt.json').read_text())['cached_grid_sha256']
footprint=np.load(cache);old,_=read_nrrd(root/'data/01744_02256_04048_volume.nrrd')
def corr(a,b):
    a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a-=a.mean();b-=b.mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))
local=json.loads((base/'local-training-displacements.json').read_text());local_checks=[]
for row,box in zip(local,plan['training_blocks_native_zyx']):
    p=np.indices(tuple(np.array(box[1])-box[0])).reshape(3,-1).T+box[0]
    values=map_coordinates(footprint,(p+row['parameters']-[84,116,84]).T,order=1,prefilter=False)
    score=corr(old[tuple(p.T)],values);assert abs(score-row['training_pearson'])<1e-12
    assert row['evaluations']<=256 and not row['at_parameter_boundary'] and row['converged']
    local_checks.append(dict(block=row['block'],training_pearson=score,diagnostic_only=True))
proof_checks=[]
for n in (1,2):
    case=root/f'paris4-independent-controls-v{n}';p=json.loads((case/'plan.json').read_text())
    box=p['reserve_box_native_zyx'];lo=np.array(box[0],float)-4;hi=np.array(box[1],float)-1+4
    corners=np.array(list(itertools.product(*zip(lo,hi))))
    radius=2+.01*np.abs(corners-center).sum(axis=1).max()+.375+.01125
    expandedlo=lo-radius;expandedhi=hi+radius
    lower=np.minimum(B*expandedlo,B*expandedhi).sum(axis=1)+B@O+A[:,3][::-1]-1
    upper=np.maximum(B*expandedlo,B*expandedhi).sum(axis=1)+B@O+A[:,3][::-1]+1
    proof=json.loads((case/'support-separation-before-fit.json').read_text());reserved=proof['reserved_controls_swept_modern_support']
    assert np.allclose(lower,reserved['lower'],atol=1e-8,rtol=0) and np.allclose(upper,reserved['upper'],atol=1e-8,rtol=0)
    gaps=[]
    for training in proof['training_swept_modern_support']:
        gap=np.maximum(lower-np.array(training['upper']),np.array(training['lower'])-upper)
        assert gap.max()>0;gaps.append(float(gap.max()))
    proof_checks.append(dict(trial=case.name,reserved_support_recomputed=True,
        strict_modern_separation_gaps_voxels=gaps,all_parameters_and_controls_covered=True))
result=dict(guard=guard,passed=True,local_objectives_replayed=local_checks,
    independent_reserved_support_replay=proof_checks,no_additional_optimization=True,
    original_verification_sha256=digest(out/'verification-v1.json'))
(out/'verification-supplement-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
