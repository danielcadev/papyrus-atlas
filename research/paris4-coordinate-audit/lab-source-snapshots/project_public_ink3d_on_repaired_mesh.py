"""Project a PUBLISHED volumetric ink score on two saved mesh ablations.

This is not the local 2D detector, nor a transcription. Protocol fixed before
reading scores: L0 nearest, face centroid, eleven offsets -5..5 along recomputed
modern-space face normal, symmetric max. Raw uint8 scores, no probability claim.
"""
from pathlib import Path
import json,sys,os,struct,shutil,urllib.error,csv
from ink_guard import require_guard
from ink_io import digest,fetch
guard=require_guard();root=Path(__file__).resolve().parent
import numpy as np
from PIL import Image,ImageDraw
os.environ['BLOSC_NTHREADS']='1'
sys.path.insert(0,str(root/'ink-reading/codec-runtime-v1'))
import numcodecs
from numcodecs import blosc
blosc.set_nthreads(1)
case=root/'repaired-mesh-ink-v1';pilot=case/'mesh-ct-pilot-v1'
out=case/'public-ink3d-projection-v2';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'script-v1.py')
pr=json.loads((pilot/'result.json').read_text());assert pr['status']=='completed'
meta=case/'metadata-v1';mm=json.loads((meta/'manifest.json').read_text())
metadata_path=meta/'ink3d-0-.zarray.json';attrs_path=meta/'ink3d-.zattrs.json'
assert digest(metadata_path)==mm['artifacts'][metadata_path.name] and digest(attrs_path)==mm['artifacts'][attrs_path.name]
metadata=json.loads(metadata_path.read_text());attrs=json.loads(attrs_path.read_text())
assert metadata['shape']==[75784,32693,32693] and metadata['chunks']==[256,256,256]
assert metadata['dtype']=='|u1' and metadata['order']=='C' and metadata['filters'] is None
assert metadata['dimension_separator']=='/' and metadata['zarr_format']==2
assert metadata['compressor']['id']=='blosc' and metadata['fill_value']==0
assert [a['name'] for a in attrs['multiscales'][0]['axes']]==['z','y','x']
assert attrs['multiscales'][0]['datasets'][0]=={'coordinateTransformations':[{'scale':[1.,1.,1.],'type':'scale'}],'path':'0'}
provenance=root/'native/paris4-axis-provenance-01.json';catalog=root/'native/catalog-paris4.json'
transforms=json.loads(provenance.read_text());assert digest(catalog)==transforms['catalogue_sha256']
matrices=[t['matrix'] for row in transforms['volume_transforms'] if row['from_volume_id']=='20230205180739'
          for t in row['transforms'] if t['to_volume_id']=='20260411134726']
assert len(matrices)==1;affine=np.array(matrices[0],np.float64)
homogeneous=np.vstack((affine,[0,0,0,1]));inverse=np.linalg.inv(homogeneous)
origin_zyx=np.array(pr['cube_origin_world_zyx'])
offsets=np.arange(-5,6,dtype=np.float64)
prepared={};all_chunks=set();roundtrips=[]
for name in pr['meshes']:
    path=pilot/name/'triangles-source-xyz.npy'
    assert digest(path)==pr['artifacts'][str(path.relative_to(pilot))]
    # The historical filename says XYZ, but same-scan anchors establish native
    # NRRD ZYX indices. Convert to catalogue XYZ only after adding the ZYX origin.
    native_zyx=np.load(path,allow_pickle=False)
    old=(native_zyx+origin_zyx)[:,:,::-1]
    modern=old@affine[:,:3].T+affine[:,3]
    restored=modern@inverse[:3,:3].T+inverse[:3,3]
    error=float(np.max(np.abs(restored-old)));assert error<1e-8;roundtrips.append(error)
    cross=np.cross(modern[:,1]-modern[:,0],modern[:,2]-modern[:,0]);normal=cross/np.linalg.norm(cross,axis=1)[:,None]
    centroid=modern.mean(axis=1)
    xyz=centroid[:,None,:]+normal[:,None,:]*offsets[None,:,None]
    zyx=np.floor(xyz[:,:,::-1]+.5).astype(np.int64)
    assert (zyx>=0).all() and (zyx<np.array(metadata['shape'])).all()
    chunks=zyx//256;unique={tuple(map(int,c)) for c in chunks.reshape(-1,3)};all_chunks.update(unique)
    prepared[name]=(modern,xyz,zyx,chunks)
assert len(all_chunks)<=8,'Bounded projection refuses more than 8 decoded chunks'
url=mm['records']['ink3d-0-.zarray']['source']['url'].removesuffix('/.zarray')
plan=dict(guard=guard,purpose=__doc__,pilot_result_sha256=digest(pilot/'result.json'),
    metadata_sha256=digest(metadata_path),attrs_sha256=digest(attrs_path),provenance_sha256=digest(provenance),
    catalogue_sha256=digest(catalog),affine_oldXYZ_to_modernXYZ=affine.tolist(),level=0,voxel_um=2.4,
    nearest_rule='floor(positive_coordinate+.5)',normal_offsets_level0=offsets.tolist(),normal_offsets_um=(offsets*2.4).tolist(),
    chunks_requested=[list(c) for c in sorted(all_chunks)],max_decoded_bytes=8*256**3,
    score_encoding='Raw uint8; exact probability quantization is not certified for this artifact',
    inference_executed_here=False,anatomical_registration_error_voxels=None,
    missing_policy='404 chunk is recorded as unobserved, never accepted as observed zero ink; no other HTTP failure is substituted')
(out/'plan.json').write_text(json.dumps(plan,indent=2))
codec=numcodecs.get_codec(metadata['compressor']);cache={};receipts=[]
for chunk in sorted(all_chunks):
    address=url+'/'+('/'.join(map(str,chunk)))
    try:
        path,receipt=fetch(address,20*1024**2);payload=path.read_bytes()
        assert len(payload)>=16
        nbytes,blocksize,cbytes=struct.unpack_from('<III',payload,4)
        assert nbytes==256**3 and cbytes==len(payload) and blocksize<=nbytes
        decoded=codec.decode(payload);assert len(decoded)==256**3
        cache[chunk]=np.frombuffer(decoded,dtype=np.uint8).reshape(256,256,256)
        receipts.append(dict(chunk=list(chunk),source=receipt,observed=True,decoded_bytes=len(decoded)))
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        cache[chunk]=None;receipts.append(dict(chunk=list(chunk),url=address,status=404,observed=False))
    print(json.dumps(dict(event='public_chunk',chunk=chunk,observed=cache[chunk] is not None)),flush=True)
summaries={};arrays={}
for name,(modern,xyz,zyx,chunks) in prepared.items():
    scores=np.zeros(zyx.shape[:2],np.uint8);valid=np.zeros_like(scores,dtype=bool)
    for chunk,data in cache.items():
        selected=np.all(chunks==chunk,axis=2)
        if data is not None:
            q=(zyx%256)[selected];scores[selected]=data[tuple(q.T)];valid[selected]=True
    complete=valid.all(axis=1);maximum=scores.max(axis=1);argmax=scores.argmax(axis=1)
    directory=out/name;directory.mkdir()
    for filename,array in [('modern-triangles-xyz.npy',modern),('sample-points-modern-xyz.npy',xyz),
        ('sample-nearest-indices-modern-zyx.npy',zyx),('raw-score-11-by-face.npy',scores.T),
        ('observed-11-by-face.npy',valid.T),('raw-max-score-by-face.npy',maximum),
        ('argmax-offset-index-by-face.npy',argmax),('face-completely-observed.npy',complete)]:
        np.save(directory/filename,array,allow_pickle=False)
    arrays[name]=(scores,valid,maximum,complete)
    summaries[name]=dict(faces=len(scores),completely_observed_faces=int(complete.sum()),
        observed_raw_score_min=int(scores[valid].min()) if valid.any() else None,
        observed_raw_score_max=int(scores[valid].max()) if valid.any() else None)
comparisons={}
for label in ('graft','hole'):
    common=np.load(pilot/(label+'-common-after-indices.npy'),allow_pickle=False)
    added=np.load(pilot/(label+'-added-after-indices.npy'),allow_pickle=False)
    before=arrays[label+'-before'];after=arrays[label+'-after']
    assert before[0].tobytes()==after[0][common].tobytes() and before[1].tobytes()==after[1][common].tobytes()
    areas=np.load(pilot/(label+'-after')/'face-area-voxel2.npy',allow_pickle=False)*(pr['voxel_um']/1000)**2
    observed_added=added[after[3][added]];values=after[2][observed_added]
    comparisons[label]=dict(common_faces=len(common),common_all11_scores_and_observation_bitwise=True,
        added_faces=len(added),observed_added_faces=len(observed_added),
        added_raw_max_score_min=int(values.min()) if len(values) else None,
        added_raw_max_score_max=int(values.max()) if len(values) else None,
        added_faces_with_nonzero_raw_score=int((values>0).sum()),
        added_area_weighted_raw_max_score=float(np.average(values,weights=areas[observed_added])) if len(values) else None,
        warning='Centroid quadrature only. Nonzero score is not verified ink, a stroke, a letter or an accuracy gain.')
    with (out/(label+'-added-face-scores.csv')).open('x') as stream:
        writer=csv.writer(stream);writer.writerow(['after_face_index','area_mm2','all11_observed','raw_max_uint8','argmax_offset_L0'])
        for i in added:writer.writerow([int(i),float(areas[i]),bool(after[3][i]),int(after[2][i]),float(offsets[int(after[0][i].argmax())])])
    # Same projected view/scale and raw score palette before/after, no UV claim.
    canvas=Image.new('RGB',(1500,930),'#101020');draw=ImageDraw.Draw(canvas)
    draw.text((10,5),label+': PUBLISHED ink3D raw uint8, max11 at centroids. Orange outline=new geometry. NOT letters.',fill='white')
    reference=prepared[label+'-after'][0].reshape(-1,3)
    for row,mode in enumerate(('before','after')):
        modern=prepared[label+'-'+mode][0];rawmax=arrays[label+'-'+mode][2];complete=arrays[label+'-'+mode][3]
        addedset=set(added.tolist()) if mode=='after' else set()
        for col,axes in enumerate(((0,1),(0,2),(1,2))):
            low=reference[:,axes].min(axis=0);scale=350/np.ptp(reference[:,axes],axis=0).max()
            projected=(modern[:,:,axes]-low)*scale+np.array([col*500+60,row*450+80])
            axis=({0,1,2}-set(axes)).pop()
            for i in np.argsort(modern[:,:,axis].mean(axis=1)):
                color=(int(rawmax[i]),)*3 if complete[i] else (70,0,80)
                points=[tuple(p) for p in projected[i]];draw.polygon(points,fill=color)
                if i in addedset:draw.line(points+[points[0]],fill=(255,140,30),width=1)
            draw.text((col*500+15,row*450+45),mode+' '+'XYZ'[axes[0]]+'XYZ'[axes[1]],fill='white')
            bar=.1*1000/2.4*scale;draw.line([(col*500+25,row*450+435),(col*500+25+bar,row*450+435)],fill='white',width=3)
            draw.text((col*500+25,row*450+415),'0.1 mm projected',fill='white')
    canvas.save(out/(label+'-published-ink3d-before-after.png'))
result=dict(status='completed',guard=guard,script_sha256=digest(Path(__file__)),plan_sha256=digest(out/'plan.json'),
    inference_executed_here=False,source='Published 20260428123845-v3-78k-fullsup volumetric uint8 ink score',
    chunks=receipts,affine_numerical_roundtrip_max_old_voxels=max(roundtrips),
    anatomical_registration_error_voxels=None,all_requested_chunks_observed=all(data is not None for data in cache.values()),
    summaries=summaries,comparisons=comparisons,
    limitations=['Published prediction, not locally executed detector or ground truth.',
        'Training overlap unknown for this ROI; Paris4 contributes to training. Raw scores are not calibrated probabilities.',
        'Affine consistency is algebraic, not an anatomical registration certificate.',
        'Per-face centroid/max sampling can miss small features and depends on triangulation. No continuous ink coverage is certified.',
        'Orange outlines mark geometric changes, not detected ink. No letter/word identified.'],
    artifacts={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(status='completed',chunks=len(receipts),all_chunks_observed=result['all_requested_chunks_observed'],comparisons=comparisons,output=str(out))),flush=True)
