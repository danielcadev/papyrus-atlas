"""Fixed old-to-modern CT coherence check on the original selected 32^3 ROI.

No registration fitting. Predeclared diagnostic gate Pearson>=.6 and margin>=.1
over six +/-4-old-voxel coordinate-shift controls. Not an anatomical-error bound.
"""
from pathlib import Path
import json,sys,os,struct,itertools,shutil
from ink_guard import require_guard
from ink_io import digest,fetch
guard=require_guard();root=Path(__file__).resolve().parent
import numpy as np
from PIL import Image,ImageDraw
from inspect_cube import read_nrrd
os.environ['BLOSC_NTHREADS']='1';sys.path.insert(0,str(root/'ink-reading/codec-runtime-v1'))
import numcodecs
from numcodecs import blosc
blosc.set_nthreads(1)
case=root/'repaired-mesh-ink-v1';out=case/'ct-registration-v2';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'script-v1.py')
pilot=json.loads((case/'mesh-ct-pilot-v1/result.json').read_text())
projection=case/'public-ink3d-projection-v2';pp=json.loads((projection/'plan.json').read_text())
assert digest(case/'mesh-ct-pilot-v1/result.json')==pp['pilot_result_sha256']
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==pilot['source_ct_sha256']
ct,header=read_nrrd(source);old=ct[112:144,144:176,112:144].copy();assert old.shape==(32,32,32)
xyz=np.indices(old.shape).reshape(3,-1).T+np.array([112,144,112])
origin=np.array(pilot['cube_origin_world_zyx']);affine=np.array(pp['affine_oldXYZ_to_modernXYZ'])
shifts=[(0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)]
queries={};chunks=set()
base='https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/'
path,receipt=fetch(base+'0/.zarray',1024**2);metadata=json.loads(path.read_text());shutil.copyfile(path,out/'modern-L0-array.json')
assert metadata['shape']==[75784,32693,32693] and metadata['chunks']==[128,128,128]
assert metadata['dtype']=='|u1' and metadata['order']=='C' and metadata['filters'] is None
assert (metadata['compressor'] is None or metadata['compressor']['id']=='blosc') and metadata['dimension_separator']=='/'
for shift in shifts:
    # Native NRRD indices are ZYX despite the legacy variable/array filenames.
    points=(xyz+origin+np.array(shift))[:,::-1]@affine[:,:3].T+affine[:,3];zyx=points[:,::-1]
    lo=np.floor(zyx).astype(np.int64)
    assert (lo>=0).all() and (lo+1<np.array(metadata['shape'])).all()
    for corner in itertools.product((0,1),repeat=3):
        chunks.update(tuple(map(int,c)) for c in ((lo+corner)//128))
    queries[shift]=zyx
assert len(chunks)<=32,'Bounded CT registration refuses >32 decoded128^3 chunks'
plan=dict(guard=guard,purpose=__doc__,old_source_sha256=digest(source),projection_plan_sha256=digest(projection/'plan.json'),
    old_roi_source_native_zyx=[[112,144,112],[144,176,144]],affine_oldXYZ_to_modernXYZ=affine.tolist(),
    coordinate_shifts_old_voxels=shifts,model_or_ink_scores_used=False,fit_performed=False,
    modern_metadata_source=receipt,chunks_requested=[list(c) for c in sorted(chunks)],
    interpolation='Trilinear modern CT L0 on source integer centers; float32 before correlations',
    gate=dict(pearson_min=.6,margin_over_shift_controls_min=.1),
    limits='Old/new energy/resolution/intensity domains differ; passing is structural coherence, not subvoxel anatomy or error estimation. Controls are not independent datasets.')
(out/'plan.json').write_text(json.dumps(plan,indent=2))
codec=numcodecs.get_codec(metadata['compressor']) if metadata['compressor'] is not None else None
cache={};receipts=[]
for chunk in sorted(chunks):
    url=base+'0/'+'/'.join(map(str,chunk));path,rec=fetch(url,3*1024**2);payload=path.read_bytes()
    if codec is None:
        decoded=payload
    else:
        assert len(payload)>=16
        nbytes,blocksize,cbytes=struct.unpack_from('<III',payload,4)
        assert nbytes==128**3 and cbytes==len(payload) and blocksize<=nbytes
        decoded=codec.decode(payload)
    assert len(decoded)==128**3
    cache[chunk]=np.frombuffer(decoded,dtype=np.uint8).reshape(128,128,128);receipts.append(dict(chunk=list(chunk),source=rec))
    print(json.dumps(dict(event='ct_chunk',index=len(receipts),total=len(chunks),chunk=chunk)),flush=True)
def lookup(indices):
    result=np.empty(len(indices),np.uint8);seen=np.zeros(len(indices),bool)
    for chunk,data in cache.items():
        selected=np.all(indices//128==chunk,axis=1);q=(indices%128)[selected]
        result[selected]=data[tuple(q.T)];seen[selected]=True
    assert seen.all();return result
def correlation(a,b):
    a=a.astype(np.float64).ravel();b=b.astype(np.float64).ravel();a-=a.mean();b-=b.mean()
    return float(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))
scores={};resampled={}
np.save(out/'old-native-roi-xyz.npy',old,allow_pickle=False)
for shift,zyx in queries.items():
    lo=np.floor(zyx).astype(np.int64);fraction=zyx-lo;values=np.zeros(len(zyx),np.float64)
    for corner in itertools.product((0,1),repeat=3):
        corner=np.array(corner);weight=np.prod(np.where(corner,fraction,1-fraction),axis=1)
        values+=lookup(lo+corner)*weight
    values=values.reshape(old.shape).astype(np.float32);name='_'.join(map(str,shift))
    np.save(out/('modern-resampled-shift-'+name+'.npy'),values,allow_pickle=False)
    scores[name]=correlation(old,values);resampled[shift]=values
primary=scores['0_0_0'];best_control=max(v for k,v in scores.items() if k!='0_0_0');margin=primary-best_control
accepted=primary>=.6 and margin>=.1
canvas=Image.new('RGB',(840,635),'#202020');draw=ImageDraw.Draw(canvas)
draw.text((10,5),'OLD CT versus MODERN CT on fixed OLD grid; native cuts32x32, display8x; no fit.',fill='white')
for row,(name,volume) in enumerate([('OLD 7.91um source',old),('MODERN L0 resampled',resampled[(0,0,0)])]):
    for axis in range(3):
        view=np.take(volume,16,axis=axis);view=np.rint(np.clip(view,0,255)).astype(np.uint8)
        Image.fromarray(view).save(out/(name.split()[0].lower()+f'-axis{axis}-native.png'))
        enlarged=Image.fromarray(view).resize((256,256),Image.Resampling.NEAREST)
        canvas.paste(enlarged,(axis*280+10,row*300+60));draw.text((axis*280+10,row*300+35),name+f' axis{axis}',fill='white')
canvas.save(out/'fixed-affine-ct-comparison.png')
result=dict(status='completed',guard=guard,script_sha256=digest(Path(__file__)),plan_sha256=digest(out/'plan.json'),
    pearson_by_shift=scores,primary_pearson=primary,best_shift_control=best_control,margin=margin,
    diagnostic_structural_coherence_gate_passed=bool(accepted),anatomical_registration_error_voxels=None,
    chunks=receipts,all_requested_chunks_observed=True,fit_performed=False,
    interpretation='Passing corroborates structural CT correspondence for this ROI; failure rejects this diagnostic gate. Neither estimates anatomical registration error or certifies ink.',
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(status='completed',chunks=len(chunks),primary=primary,best_control=best_control,margin=margin,gate_passed=bool(accepted),output=str(out))),flush=True)
