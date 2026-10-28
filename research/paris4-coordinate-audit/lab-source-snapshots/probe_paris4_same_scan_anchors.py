"""Check NRRD/global-frame anchors against the same historical CT export."""
from pathlib import Path
import itertools,json,shutil,urllib.request,hashlib
from ink_guard import require_guard
from ink_io import digest,fetch
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
from inspect_cube import read_nrrd
root=Path(__file__).resolve().parent;case=root/'paris4-registration-anchors-v1'
case.mkdir(exist_ok=False);shutil.copyfile(__file__,case/'script.py')
prior=root/'repaired-mesh-ink-v1';pilot=json.loads((prior/'mesh-ct-pilot-v1/result.json').read_text())
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==pilot['source_ct_sha256']
old,header=read_nrrd(source)
base='https://data.aws.ash2txt.org/samples/PHercParis4/volumes/20230205180739-7.910um-54keV-masked.zarr/0/'
url=base+'.zarray'
with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=30) as response:
    payload=response.read(1024**2+1);assert len(payload)<=1024**2
    metadata_receipt=dict(url=url,status=response.status,etag=response.headers.get('ETag'),sha256=hashlib.sha256(payload).hexdigest())
(case/'old-ct-L0-array.json').write_bytes(payload);meta=json.loads(payload)
assert meta['dtype']=='|u1' and meta['chunks']==[128]*3 and meta['compressor'] is None
assert meta['order']=='C' and meta['filters'] is None and meta['dimension_separator']=='/'
points=np.indices((16,)*3).reshape(3,-1).T*4+96
values=old[tuple(points.T)]
# Offsets are motivated by recorded volume-length differences, not by ink outcomes.
offsets=[0,-118,118,-111,111,-7,7]
variants=[];chunks=set();origin=np.array([1744,2256,4048])
for convention in ('named-origin-is-ZYX','header-origin-is-XYZ'):
    for zshift in offsets:
        zyx=(points[:,::-1]+origin if convention=='named-origin-is-ZYX' else (points+origin)[:,::-1])
        zyx=zyx+np.array([zshift,0,0])
        assert (zyx>=0).all() and (zyx<np.array(meta['shape'])).all()
        variants.append((convention,zshift,zyx))
        chunks.update(tuple(map(int,q)) for q in zyx//128)
assert len(chunks)<=64
plan=dict(guard=guard,source_ct_sha256=digest(source),metadata_source=metadata_receipt,
    grid='16^3 NRRD indices, stride4, origin96 in each native NRRD axis; includes no ink selection.',
    z_offsets_from_recorded_length_differences=offsets,coordinate_conventions=['named-origin-is-ZYX','header-origin-is-XYZ'],
    tests_are_same_scan_CT_only=True,chunks_requested=[list(q) for q in sorted(chunks)],
    gates_unchanged=True,acceptance='No registration admission from this exploratory anchor check alone.')
(case/'plan.json').write_text(json.dumps(plan,indent=2))
cache={};receipts=[]
for q in sorted(chunks):
    path,receipt=fetch(base+'/'.join(map(str,q)),3*1024**2)
    assert path.stat().st_size==128**3
    cache[q]=np.frombuffer(path.read_bytes(),np.uint8).reshape((128,)*3);receipts.append(dict(chunk=list(q),source=receipt))
def corr(a,b):
    a=a.astype(float);b=b.astype(float);a-=a.mean();b-=b.mean();den=np.linalg.norm(a)*np.linalg.norm(b)
    return None if den==0 else float(a@b/den)
rows=[]
np.save(case/'nrrd-anchor-indices-xyz.npy',points,allow_pickle=False)
np.save(case/'nrrd-anchor-values.npy',values,allow_pickle=False)
for convention,zshift,zyx in variants:
    result=np.zeros(len(points),np.uint8);seen=np.zeros(len(points),bool)
    for q,data in cache.items():
        selected=np.all(zyx//128==q,axis=1);local=(zyx%128)[selected]
        result[selected]=data[tuple(local.T)];seen[selected]=True
    assert seen.all()
    name=convention+'-z'+str(zshift)
    np.save(case/(name+'.npy'),result,allow_pickle=False)
    positive=result>0
    rows.append(dict(convention=convention,zshift=zshift,pearson=corr(values,result),
        positive_fraction=float(positive.mean()),pearson_export_positive=corr(values[positive],result[positive]) if positive.sum()>8 else None,
        exact_equal_fraction=float(np.mean(values==result)),values_file=name+'.npy'))
record=dict(guard=guard,rows=rows,chunks=receipts,metadata_shape=meta['shape'],
    source_geometry_modified=False,ink_used=False,registration_admitted=False,
    artifacts={p.name:digest(p) for p in case.iterdir() if p.is_file()})
(case/'result.json').write_text(json.dumps(record,indent=2));print(json.dumps(rows),flush=True)
