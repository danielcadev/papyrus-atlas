"""Replay cold CT fits, strengthen support certificates and audit nominal controls."""
from pathlib import Path
import itertools,json,sys,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from inspect_cube import read_nrrd
out=root/'paris4-independent-validation-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
prior=root/'paris4-ink-benefit-v2/ct-registration-v3'
baseplan=json.loads((prior/'plan.json').read_text());A=np.array(baseplan['affine_oldXYZ_to_modernXYZ']);B=A[:,:3][::-1,::-1]
O=np.array([1744,2256,4048]);center=np.array([128,160,128]);gridlow=np.array([84,116,84])
rawpath=prior/'observed-modern-ct-zyx-portable.npy'
assert digest(rawpath)==json.loads((prior/'portable-array-receipt.json').read_text())['portable_sha256']
raw=np.load(rawpath,mmap_mode='r');start=np.min([r['chunk'] for r in json.loads((prior/'ct-sources.json').read_text())['chunks']],axis=0)*128
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==baseplan['source_ct_sha256']
old,_=read_nrrd(source)
cache=root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy';footprint=np.load(cache)
shifts=((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4))
def corr(a,b):
    a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a-=a.mean();b-=b.mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))
def transform(p,x):return (p-center)@(np.eye(3)+x[3:].reshape(3,3)).T+center+x[:3]
def sample(p):
    q=((p+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);frac=q-lo
    assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
    result=np.zeros(len(p))
    for corner in itertools.product((0,1),repeat=3):
        c=np.array(corner);result+=raw[tuple((lo+c).T)]*np.prod(np.where(c,frac,1-frac),axis=1)
    return result
def direct(p,x):
    total=np.zeros(len(p))
    for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):
        for i in range(0,len(p),32768):total[i:i+32768]+=sample(transform(p[i:i+32768]+offset,x))/64
    return total.astype('<f4')
def metrics(target,volume):
    scores={}
    for s in shifts:scores['_'.join(map(str,s))]=corr(target,volume[tuple(slice(4+d,4+d+n) for d,n in zip(s,target.shape))])
    p=scores['0_0_0'];margin=p-max(v for k,v in scores.items() if k!='0_0_0')
    return dict(primary_pearson=p,margin=margin,controls_native_zyx=scores,gate_passed=bool(p>=.6 and margin>=.1))
checks=[];nominal=[];supports=[]
for number in (1,2):
    case=root/f'paris4-independent-controls-v{number}'
    r=json.loads((case/'result.json').read_text());plan=json.loads((case/'plan.json').read_text())
    for relative,sha in r['artifacts'].items():assert digest(case/relative)==sha
    assert digest(cache)==json.loads((case/'input-receipt.json').read_text())['cached_grid_sha256']
    fit=json.loads((case/'global-fit-frozen-before-validation.json').read_text());x=np.array(fit['parameters'])
    assert fit['initializer_parameters']==[0.]*12 and fit['frozen_before_reserve_and_ROI'] and fit['evaluations']<=2048
    assert np.array_equal(x,r['global_fit']['parameters'])
    training=np.load(case/'training-native-zyx.npy');reserved=np.load(case/'reserved-native-zyx.npy')
    assert reserved[:,0].max()<96 and training[:,0].min()>=120
    oldguard=plan['target_guard_box_native_zyx']
    proof=json.loads((case/'support-separation-before-fit.json').read_text())
    # Stronger continuous guard: include whole old voxel cells and the declared
    # continuous half-open box. The original source only compared integer centers.
    protected_low=np.array(oldguard[0])-.5;protected_high=np.array(oldguard[1],float)
    projected=np.abs(np.linalg.inv(B)).sum(axis=1);guard_margins=[]
    for box,support in zip(plan['training_blocks_native_zyx'],proof['training_swept_modern_support']):
        lo=np.array(box[0],float);hi=np.array(box[1],float)-1
        corners=np.array(list(itertools.product(*zip(lo,hi))))
        radius=2+.01*np.abs(corners-center).sum(axis=1).max()+1.375+.01125
        assert abs(radius-support['native_radius'])<1e-12
        native_lo=lo-radius-projected;native_hi=hi+radius+projected
        gap=np.maximum(protected_low-native_hi,native_lo-protected_high)
        assert gap.max()>0;guard_margins.append(float(gap.max()))
        # Recompute conservative canonical interval enclosure independently.
        expandedlo=lo-radius;expandedhi=hi+radius
        transformedlo=np.minimum(B*expandedlo,B*expandedhi).sum(axis=1)+B@O+A[:,3][::-1]-1
        transformedhi=np.maximum(B*expandedlo,B*expandedhi).sum(axis=1)+B@O+A[:,3][::-1]+1
        assert np.allclose(transformedlo,support['lower'],atol=1e-8,rtol=0)
        assert np.allclose(transformedhi,support['upper'],atol=1e-8,rtol=0)
        reserve_support=proof['reserved_controls_swept_modern_support']
        assert np.any(transformedhi<reserve_support['lower']) or np.any(np.array(reserve_support['upper'])<transformedlo)
    supports.append(dict(trial=case.name,stronger_continuous_guard_passed=True,strict_native_separation_gaps_voxels=guard_margins,
        note='Supersedes the source guardhigh-1 center-only inequality without changing frozen source or any sample.'))
    values=map_coordinates(footprint,(transform(training,x)-gridlow).T,order=1,prefilter=False)
    target=old[tuple(training.T)]
    objective=corr(target,values) if number==1 else float(np.mean([corr(a,b) for a,b in zip(np.split(target,5),np.split(values,5))]))
    assert abs(objective-fit['training_pearson'])<1e-12
    boundary=bool(np.any(abs(x[:3])>=1.99999) or np.any(abs(x[3:])>=.00999))
    assert boundary==fit['at_parameter_boundary'] and boundary
    for name in ('new_reserved_control','original_repaired_ROI'):
        volume=np.load(case/(name+'-modern-footprint.npy'));target=np.load(case/(name+'-old-target.npy'))
        replay=metrics(target,volume);record=r['validation'][name]
        assert abs(replay['margin']-record['margin'])<1e-12
        assert replay['gate_passed']==record['gate_passed'] and not replay['gate_passed']
        for key,value in replay['controls_native_zyx'].items():assert abs(value-record['controls_native_zyx'][key])<1e-12
        box=plan['reserve_box_native_zyx'] if name=='new_reserved_control' else ([112,144,112],[144,176,144])
        low=np.array(box[0])-4
        selected=np.array([[0,0,0],[3,5,7],np.array(volume.shape)//2,np.array(volume.shape)-1])
        assert np.array_equal(direct(selected+low,x),volume[tuple(selected.T)])
        checks.append(dict(trial=case.name,group=name,primary_pearson=replay['primary_pearson'],margin=replay['margin'],gate_passed=False,
            direct_observed_CT_footprints_replayed=4,old_target_std=float(target.std()),modern_center_std=float(volume[tuple(slice(4,4+n) for n in target.shape)].std())))
    assert not r['registration_accepted']
    # Read-only nominal baseline on each new control. This is diagnostic, never
    # used to refit or to select a transform. Every failure remains reported.
    box=plan['reserve_box_native_zyx'];low=np.array(box[0])-4;shape=tuple(np.array(box[1])-box[0]+8)
    p=np.indices(shape).reshape(3,-1).T+low
    volume=direct(p,np.zeros(12)).reshape(shape);np.save(out/f'control-{number}-nominal-modern-footprint.npy',volume,allow_pickle=False)
    target=old[tuple(slice(a,b) for a,b in zip(*box))]
    baseline=metrics(target,volume);baseline['control_box_native_zyx']=box;baseline['model']='Catalogue affine plus zero residual, diagnostic only.'
    nominal.append(baseline)
# Evaluate the first, now-inspected reserve under the second frozen model too.
first=root/'paris4-independent-controls-v1';second=root/'paris4-independent-controls-v2'
box=json.loads((first/'plan.json').read_text())['reserve_box_native_zyx'];lo=np.array(box[0])-4;shape=tuple(np.array(box[1])-box[0]+8)
p=np.indices(shape).reshape(3,-1).T+lo;x=np.array(json.loads((second/'global-fit-frozen-before-validation.json').read_text())['parameters'])
volume=direct(p,x).reshape(shape);np.save(out/'prior-control-A-under-second-fit.npy',volume,allow_pickle=False)
target=np.load(first/'new_reserved_control-old-target.npy');development=metrics(target,volume)
previous=root/'paris4-exterior-registration-v2';manifest=json.loads((previous/'evidence-manifest-v1.json').read_text())
for rel,row in manifest['files'].items():assert digest(previous/rel)==row['sha256']
result=dict(guard=guard,passed=True,checks=checks,stronger_continuous_support_checks=supports,
    nominal_reserved_controls=nominal,previously_inspected_A_under_second_fit=development,
    previous_sealed_files_unchanged=len(manifest['files']),registration_accepted=False,ink_used=False,letters_verified=0,
    caveat='Same-scan controls; CT similarities do not establish anatomical landmarks, a deformation field, statistical independence or error bounds.')
(out/'verification-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
