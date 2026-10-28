"""Independently replay exterior-fit controls and selected direct CT footprints."""
from pathlib import Path
import itertools,json,sys
from ink_guard import require_guard
from ink_io import digest
from inspect_cube import read_nrrd
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
out=root/'paris4-exterior-registration-v1';out.mkdir(exist_ok=False)
previous=root/'paris4-registration-anchors-v1'
manifest=json.loads((previous/'evidence-manifest-v1.json').read_text())
for relative,row in manifest['files'].items():assert digest(previous/relative)==row['sha256']
rawbase=root/'paris4-ink-benefit-v2/ct-registration-v3'
plan=json.loads((rawbase/'plan.json').read_text());A=np.array(plan['affine_oldXYZ_to_modernXYZ'])
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==plan['source_ct_sha256']
old,_=read_nrrd(source);target=old[112:144,144:176,112:144]
np.save(out/'old-native-validation-zyx.npy',target,allow_pickle=False)
rawpath=rawbase/'observed-modern-ct-zyx-portable.npy'
assert digest(rawpath)==json.loads((rawbase/'portable-array-receipt.json').read_text())['portable_sha256']
raw=np.load(rawpath,mmap_mode='r')
start=np.min([x['chunk'] for x in json.loads((rawbase/'ct-sources.json').read_text())['chunks']],axis=0)*128
O=np.array([1744,2256,4048]);center=np.array([128,160,128]);low=np.array([84,116,84])
cache=previous/'corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy';grid=np.load(cache)
shifts=((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4))
def corr(a,b):
    a=a.astype(float).ravel();b=b.astype(float).ravel();a-=a.mean();b-=b.mean()
    return float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))
checks=[]
for folder,gradient in (('paris4-exterior-collar-v1',False),('paris4-exterior-gradient-v1',True)):
    base=root/folder;r=json.loads((base/'result.json').read_text())
    for name,sha in r['artifacts'].items():assert digest(base/name)==sha
    assert digest(cache)==json.loads((base/'cached-grid-receipt.json').read_text())['sha256']
    frozen=json.loads((base/'fit-frozen-before-validation.json').read_text())
    x=np.array(frozen['parameters']);assert np.array_equal(x,r['fit']['parameters'])
    assert abs(x[:3]).max()<3.9999 and abs(x[3:]).max()<.009999
    assert frozen['evaluations']<=2048 and frozen['frozen_before_validation']
    training=np.load(base/'training-native-zyx.npy');reserved=np.load(base/'reserved-exterior-native-zyx.npy')
    trainset=set(map(tuple,training));reservedset=set(map(tuple,reserved));assert not trainset & reservedset
    for points in (training,reserved):
        for d in ([np.zeros(3,dtype=int)] if not gradient else np.r_[np.eye(3,dtype=int),-np.eye(3,dtype=int)]):
            p=points+d
            assert not np.any(np.all((p>=np.array([108,140,108])) & (p<np.array([148,180,148])),axis=1))
    def transform(points):return (points-center)@(np.eye(3)+x[3:].reshape(3,3)).T+center+x[:3]
    for label,points in (('training',training),('reserved',reserved)):
        directions=np.eye(3,dtype=int)
        if gradient:
            a=np.concatenate([old[tuple((points+d).T)].astype(float)-old[tuple((points-d).T)].astype(float) for d in directions])
            b=np.concatenate([map_coordinates(grid,(transform(points+d)-low).T,order=1,prefilter=False)-map_coordinates(grid,(transform(points-d)-low).T,order=1,prefilter=False) for d in directions])
        else:
            a=old[tuple(points.T)];b=map_coordinates(grid,(transform(points)-low).T,order=1,prefilter=False)
        key='training_pearson' if label=='training' else ('reserved_exterior_gradient_pearson' if gradient else 'reserved_exterior_pearson')
        assert abs(corr(a,b)-r['fit'][key])<1e-12
    volume=np.load(base/'modern-footprint-corrected-affine-native-zyx.npy');values={}
    for shift in shifts:
        key='_'.join(map(str,shift));value=corr(target,volume[tuple(slice(4+i,36+i) for i in shift)])
        assert abs(value-r['pearson_by_control_native_zyx'][key])<1e-12;values[key]=value
    primary=values['0_0_0'];margin=primary-max(v for k,v in values.items() if k!='0_0_0')
    assert abs(margin-r['margin'])<1e-12
    assert (primary>=.6 and margin>=.1)==r['diagnostic_structural_coherence_gate_passed']
    # Four independent direct observed-byte footprints, including ROI extremes.
    selected=np.array([[0,0,0],[7,9,11],[16,16,16],[39,39,39]])
    points=selected+np.array([108,140,108]);means=np.zeros(len(points))
    for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):
        q=((transform(points+offset)+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
        lo=np.floor(q).astype(int);f=q-lo
        assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
        for corner in itertools.product((0,1),repeat=3):
            c=np.array(corner);means+=raw[tuple((lo+c).T)]*np.prod(np.where(c,f,1-f),axis=1)/64
    assert np.array_equal(means.astype('<f4'),volume[tuple(selected.T)])
    checks.append(dict(trial=folder,training_count=len(training),reserved_count=len(reserved),
        primary_pearson=primary,margin=margin,gate_passed=bool(primary>=.6 and margin>=.1),
        independent_direct_footprints_replayed=4,fit_and_reserved_objectives_replayed=True))
# Diagnostic autocorrelation is not a replacement admission test or error bound.
old40=old[108:148,140:180,108:148]
selfcontrols={'_'.join(map(str,s)):corr(target,old40[tuple(slice(4+i,36+i) for i in s)]) for s in shifts[1:]}
result=dict(guard=guard,passed=True,previous_sealed_files_unchanged=len(manifest['files']),
    checks=checks,old_CT_shift_autocorrelation=selfcontrols,
    old_CT_self_control_margin=1-max(selfcontrols.values()),
    thresholds_unchanged=dict(pearson_min=.6,margin_min=.1),geometry_or_uv_modified=False,
    ink_used=False,letters_verified=0,registration_accepted=False)
(out/'verification-v1.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
