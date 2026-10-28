"""Test signed local axis conventions against same-scan CT, not ink."""
from pathlib import Path
import itertools,json,shutil
from ink_guard import require_guard
from ink_io import digest,fetch
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
root=Path(__file__).resolve().parent;prior=root/'paris4-registration-anchors-v1'
out=prior/'signed-axis-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
previous=json.loads((prior/'result.json').read_text())
for name,sha in previous['artifacts'].items():assert digest(prior/name)==sha
points=np.load(prior/'nrrd-anchor-indices-xyz.npy',allow_pickle=False)
values=np.load(prior/'nrrd-anchor-values.npy',allow_pickle=False)
training=((points[:,0]-96)//4)%2==0;validation=~training
origin=np.array([1744,2256,4048]);variants=[];chunks=set()
for permutation in itertools.permutations(range(3)):
    for flips in itertools.product((False,True),repeat=3):
        q=points[:,permutation].copy()
        for axis,flip in enumerate(flips):
            if flip:q[:,axis]=255-q[:,axis]
        q+=origin
        variants.append((permutation,flips,q));chunks.update(tuple(map(int,p)) for p in q//128)
assert len(chunks)<=16
(out/'plan.json').write_text(json.dumps(dict(guard=guard,tests='48 signed local axis conventions at fixed named ZYX origin; no scan translation or ink fit.',
    training='Alternating first native-NRRD index planes; remaining planes reserved for convention validation.',
    source_anchor_result_sha256=digest(prior/'result.json'),
    candidate_same_scan_gate=dict(validation_pearson_min=.95,margin_over_runner_up_min=.1),
    original_cross_scan_gate_unchanged=True),indent=2))
base='https://data.aws.ash2txt.org/samples/PHercParis4/volumes/20230205180739-7.910um-54keV-masked.zarr/0/'
cache={};receipts=[]
for key in sorted(chunks):
    path,receipt=fetch(base+'/'.join(map(str,key)),3*1024**2);assert path.stat().st_size==128**3
    cache[key]=np.frombuffer(path.read_bytes(),np.uint8).reshape((128,)*3);receipts.append(dict(chunk=list(key),source=receipt))
def corr(a,b):
    a=a.astype(float);b=b.astype(float);a-=a.mean();b-=b.mean();d=np.linalg.norm(a)*np.linalg.norm(b)
    return -1. if d==0 else float(a@b/d)
rows=[];arrays=[]
for permutation,flips,indices in variants:
    observed=np.zeros(len(points),bool);sample=np.zeros(len(points),np.uint8)
    for key,data in cache.items():
        selected=np.all(indices//128==key,axis=1);q=(indices%128)[selected]
        sample[selected]=data[tuple(q.T)];observed[selected]=True
    assert observed.all();arrays.append(sample)
    rows.append(dict(permutation_nrrd_to_global_zyx=list(permutation),flips=list(flips),
        train_pearson=corr(values[training],sample[training]),validation_pearson=corr(values[validation],sample[validation])))
order=sorted(range(len(rows)),key=lambda i:-rows[i]['train_pearson']);chosen=rows[order[0]]
np.save(out/'all-variant-anchor-values.npy',np.asarray(arrays),allow_pickle=False)
margin=chosen['validation_pearson']-max(rows[i]['validation_pearson'] for i in order[1:])
result=dict(guard=guard,rows=rows,chosen_by_training=chosen,validation_margin=margin,
    candidate_same_scan_gate_passed=bool(chosen['validation_pearson']>=.95 and margin>=.1),
    chunks=receipts,ink_used=False,registration_admitted=False,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(chosen=chosen,margin=margin,gate=result['candidate_same_scan_gate_passed'])),flush=True)
