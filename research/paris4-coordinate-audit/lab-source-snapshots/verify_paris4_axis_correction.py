"""Independent replay of source axes, direct CT footprints and corrected score queries."""
from pathlib import Path
import itertools,json,sys,struct
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
root=Path(__file__).resolve().parent;case=root/'paris4-registration-anchors-v1'
previous=root/'paris4-ink-benefit-v2';manifest=json.loads((previous/'evidence-manifest-v1.json').read_text())
for relative,item in manifest['files'].items():assert digest(previous/relative)==item['sha256']
axis=json.loads((case/'signed-axis-v1/result.json').read_text())
portable=json.loads((case/'portable-axis-replay-v1/result.json').read_text())
assert portable['passed'] and portable['best']['permutation']==[0,1,2] and not any(portable['best']['flips'])
assert abs(portable['best']['validation_pearson']-axis['chosen_by_training']['validation_pearson'])<1e-12
target=np.load(root/'repaired-mesh-ink-v1/ct-registration-v2/old-native-roi-xyz.npy',allow_pickle=False)
checks=[]
for name,array in (('corrected-ct-v1','corrected-modern-footprint-native-zyx.npy'),
    ('corrected-translation-v1','modern-footprint-corrected-fitted-native-zyx.npy'),
    ('corrected-footprint-fit-v1','modern-footprint-corrected-affine-native-zyx.npy')):
    folder=case/name;r=json.loads((folder/'result.json').read_text())
    for relative,sha in r['artifacts'].items():assert digest(folder/relative)==sha
    volume=np.load(folder/array,allow_pickle=False);values={}
    for shift in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
        key='_'.join(map(str,shift));q=volume[tuple(slice(4+i,36+i) for i in shift)]
        a=target.astype(float).ravel();b=q.astype(float).ravel();a-=a.mean();b-=b.mean()
        value=float((a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()))
        assert abs(value-r['pearson_by_control_native_zyx'][key])<1e-12;values[key]=value
    p=values['0_0_0'];margin=p-max(v for k,v in values.items() if k!='0_0_0')
    assert not r['diagnostic_structural_coherence_gate_passed'] and margin<.1
    checks.append(dict(trial=name,primary=p,margin=margin,gates_replayed=True))
# Directly recompute four CT cell footprints from observed modern chunks. This
# checks the transpose shortcut against the actual canonical query equation.
oldroot=root/'repaired-mesh-ink-v1';pp=json.loads((oldroot/'public-ink3d-projection-v2/plan.json').read_text())
A=np.array(pp['affine_oldXYZ_to_modernXYZ']);O=np.array([1744,2256,4048])
rawbase=previous/'ct-registration-v3';repair=json.loads((rawbase/'portable-array-receipt.json').read_text())
rawpath=rawbase/'observed-modern-ct-zyx-portable.npy';assert digest(rawpath)==repair['portable_sha256']
raw=np.load(rawpath,mmap_mode='r');sources=json.loads((rawbase/'ct-sources.json').read_text())
start=np.min([r['chunk'] for r in sources['chunks']],axis=0)*128
selected=np.array([[0,0,0],[7,9,11],[16,16,16],[31,31,31]])
native=selected+np.array([112,144,112]);means=np.zeros(4)
for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):
    q=((native+offset+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);f=q-lo;assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
    for corner in itertools.product((0,1),repeat=3):
        corner=np.array(corner);ix=lo+corner
        means+=raw[tuple(ix.T)]*np.prod(np.where(corner,f,1-f),axis=1)/64
nominal=np.load(case/'corrected-ct-v1/corrected-modern-footprint-native-zyx.npy',allow_pickle=False)
assert np.array_equal(means.astype('<f4'),nominal[tuple((selected+4).T)])
checks.append(dict(direct_canonical_CT_footprints_replayed=4,voxel_midpoints_each=64))
del raw
sys.path.insert(0,str(root/'ink-reading/codec-runtime-v1'))
import numcodecs
from numcodecs import blosc
blosc.set_nthreads(1)
folder=case/'corrected-score-coverage-v1';r=json.loads((folder/'result.json').read_text())
for relative,sha in r['artifacts'].items():assert digest(folder/relative)==sha
metadata=json.loads((oldroot/'metadata-v1/ink3d-0-.zarray.json').read_text())
codec=numcodecs.get_codec(metadata['compressor']);source_records=json.loads((folder/'field-sources.json').read_text());cache={}
for row in source_records['original_chunks']+source_records['additional_chunks']:
    spec=row['source'];path=Path(spec['path']);assert digest(path)==spec['sha256']
    payload=path.read_bytes();assert struct.unpack_from('<I',payload,4)[0]==256**3
    cache[tuple(row['chunk'])]=np.frombuffer(codec.decode(payload),np.uint8).reshape((256,)*3)
for label in ('graft','hole'):
    d=folder/label;triangles=np.load(d/'modern-triangles-after-xyz.npy',allow_pickle=False)
    source=np.load(oldroot/'mesh-ct-pilot-v1'/(label+'-after')/'triangles-source-xyz.npy',allow_pickle=False)
    expected=(source[:,:,::-1]+O[::-1])@A[:,:3].T+A[:,3]
    assert np.array_equal(triangles,expected)
    points=np.load(d/'points-modern-xyz.npy',allow_pickle=False);indices=np.load(d/'indices-modern-zyx.npy',allow_pickle=False)
    ids=np.load(d/'face-id-after.npy',allow_pickle=False);scores=np.load(d/'raw-center-score.npy',allow_pickle=False)
    assert np.array_equal(np.floor(points[:,::-1]+.5).astype(np.int64),indices)
    replay=np.zeros(len(indices),np.uint8);seen=np.zeros(len(indices),bool)
    for key,data in cache.items():
        select=np.all(indices//256==key,axis=1);q=(indices%256)[select]
        replay[select]=data[tuple(q.T)];seen[select]=True
    assert seen.all() and np.array_equal(replay,scores)
    common=np.load(oldroot/'mesh-ct-pilot-v1'/(label+'-common-after-indices.npy'),allow_pickle=False)
    before=np.load(d/'modern-triangles-before-xyz.npy',allow_pickle=False);assert np.array_equal(triangles[common],before)
    def encode(q):return (q[:,0]*metadata['shape'][1]+q[:,1])*metadata['shape'][2]+q[:,2]
    allq,first=np.unique(indices,axis=0,return_index=True);oldq=np.unique(indices[np.isin(ids,common)],axis=0)
    new=~np.isin(encode(allq),encode(oldq));new_values=scores[first][new]
    assert np.array_equal(allq[new],np.load(d/'new-unique-indices-modern-zyx.npy',allow_pickle=False))
    assert np.array_equal(new_values,np.load(d/'new-unique-raw-score.npy',allow_pickle=False))
    assert len(new_values)==r['summaries'][label]['new_unique_sampled_voxels']
    assert np.count_nonzero(new_values>=128)==0
    checks.append(dict(group=label,corrected_transform_and_all_scores_replayed=True,new_positions=len(new_values),raw_max=int(new_values.max())))
result=dict(guard=guard,passed=True,previous_phase_files_unchanged=len(manifest['files']),
    same_scan_axis_bridge_validated=True,cross_scan_registration_gate_passed=False,
    ink_or_letter_recovery_demonstrated=False,checks=checks)
with (case/'verification-v1.json').open('x') as stream:stream.write(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
