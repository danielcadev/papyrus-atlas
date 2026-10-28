"""Before/after sampled score-field coverage, without treating scores as ink truth."""
from pathlib import Path
import json,sys,struct,csv,shutil
from ink_guard import require_guard
from ink_io import digest,fetch
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'ink-reading/codec-runtime-v1'))
import numcodecs
from numcodecs import blosc
blosc.set_nthreads(1)
prior=root/'repaired-mesh-ink-v1';case=root/'paris4-registration-anchors-v1';out=case/'corrected-score-coverage-v1'
out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
pilot=prior/'mesh-ct-pilot-v1';projection=prior/'public-ink3d-projection-v2'
pr=json.loads((pilot/'result.json').read_text());pred=json.loads((projection/'result.json').read_text())
for base,record in ((pilot,pr),(projection,pred)):
    for relative,sha in record['artifacts'].items():assert digest(base/relative)==sha
metadata=json.loads((prior/'metadata-v1/ink3d-0-.zarray.json').read_text())
codec=numcodecs.get_codec(metadata['compressor']);cache={};extra_receipts=[]
axis=json.loads((case/'signed-axis-v1/result.json').read_text());assert axis['candidate_same_scan_gate_passed']
assert axis['chosen_by_training']['permutation_nrrd_to_global_zyx']==[0,1,2] and not any(axis['chosen_by_training']['flips'])
field_manifest=json.loads((prior/'metadata-v1/manifest.json').read_text())
field_base=field_manifest['records']['ink3d-0-.zarray']['source']['url'].removesuffix('/.zarray')
A=np.array(json.loads((projection/'plan.json').read_text())['affine_oldXYZ_to_modernXYZ'])
origin=np.array(pr['cube_origin_world_zyx'])
def corrected_triangles(label,phase):
    native=np.load(pilot/(label+'-'+phase)/'triangles-source-xyz.npy',allow_pickle=False)
    return ((native+origin)[:,:,::-1]@A[:,:3].T+A[:,3])

for row in pred['chunks']:
    assert row['observed'];path=Path(row['source']['path']);assert digest(path)==row['source']['sha256']
    payload=path.read_bytes();nbytes,blocksize,cbytes=struct.unpack_from('<III',payload,4)
    assert nbytes==256**3 and cbytes==len(payload) and blocksize<=nbytes
    decoded=codec.decode(payload);assert len(decoded)==nbytes
    cache[tuple(row['chunk'])]=np.frombuffer(decoded,np.uint8).reshape((256,)*3)
(out/'plan.json').write_text(json.dumps(dict(guard=guard,transform='Same-scan-verified native NRRD ZYX, converted to catalogue XYZ; nominal catalogue affine. No rejected residual fit is applied.',
    quadrature='n^2 equal-area triangular midpoint cells; n=ceil(longest modern L0 edge), all faces.',
    score_rule='Nearest floor(q+.5), on-surface only; no depth maximum.',
    voxel_coverage='Unique queried modern L0 indices, not continuous surface coverage.',
    score_thresholds='All integer thresholds 0 through 255; none defines confirmed ink.',
    limitations='Published uint8 scores are neither calibrated probabilities nor independent ink/letter truth.',
    pilot_sha256=digest(pilot/'result.json'),field_projection_sha256=digest(projection/'result.json')),indent=2))
def sample(points):
    indices=np.floor(points[:,::-1]+.5).astype(np.int64);chunks=indices//256
    requested={tuple(map(int,q)) for q in chunks}
    assert len(set(cache)|requested)<=8
    for key in sorted(requested-set(cache)):
        path,receipt=fetch(field_base+'/'+('/'.join(map(str,key))),20*1024**2)
        payload=path.read_bytes();nbytes,blocksize,cbytes=struct.unpack_from('<III',payload,4)
        assert nbytes==256**3 and cbytes==len(payload) and blocksize<=nbytes
        decoded=codec.decode(payload);assert len(decoded)==nbytes
        cache[key]=np.frombuffer(decoded,np.uint8).reshape((256,)*3);extra_receipts.append(dict(chunk=list(key),source=receipt))
    scores=np.zeros(len(points),np.uint8);seen=np.zeros(len(points),bool)
    for chunk,data in cache.items():
        mask=np.all(chunks==chunk,axis=1);q=(indices%256)[mask]
        scores[mask]=data[tuple(q.T)];seen[mask]=True
    assert seen.all(),'No implicit missing-data fill'
    return indices,scores
def quadrature(triangles):
    points=[];ids=[];counts=[]
    for i,t in enumerate(triangles):
        edge=max(np.linalg.norm(t[1]-t[0]),np.linalg.norm(t[2]-t[0]),np.linalg.norm(t[2]-t[1]))
        n=max(1,int(np.ceil(edge)));assert n<=128
        uv=[]
        for a in range(n):
            for b in range(n-a):
                uv.append(((a+1/3)/n,(b+1/3)/n))
                if a+b<n-1:uv.append(((a+2/3)/n,(b+2/3)/n))
        uv=np.asarray(uv);assert len(uv)==n*n
        points.append(t[0]+uv[:,0,None]*(t[1]-t[0])+uv[:,1,None]*(t[2]-t[0]))
        ids.extend([i]*len(uv));counts.append(len(uv))
    assert sum(counts)<=500000
    return np.concatenate(points),np.asarray(ids),np.asarray(counts)
summaries={};panels=[]
for label in ('graft','hole'):
    before=corrected_triangles(label,'before')
    after=corrected_triangles(label,'after')
    common=np.load(pilot/(label+'-common-after-indices.npy'),allow_pickle=False)
    added=np.load(pilot/(label+'-added-after-indices.npy'),allow_pickle=False)
    assert np.array_equal(after[common],before) and len(common)==len(before)
    points,faceids,counts=quadrature(after)
    before_points,_,_=quadrature(before)
    retained=np.isin(faceids,common);is_added=np.isin(faceids,added)
    assert np.array_equal(points[retained],before_points),'Common samples must remain bit-identical'
    indices,scores=sample(points);before_indices,before_scores=sample(before_points)
    assert np.array_equal(indices[retained],before_indices) and np.array_equal(scores[retained],before_scores)
    unique_after,unique_index=np.unique(indices,axis=0,return_index=True)
    unique_before=np.unique(before_indices,axis=0)
    shape=metadata['shape']
    def encode(q):return (q[:,0]*shape[1]+q[:,1])*shape[2]+q[:,2]
    new_mask=~np.isin(encode(unique_after),encode(unique_before));new_scores=scores[unique_index][new_mask]
    directory=out/label;directory.mkdir()
    for name,array in (('modern-triangles-before-xyz.npy',before),('modern-triangles-after-xyz.npy',after),('points-modern-xyz.npy',points),('face-id-after.npy',faceids),('raw-center-score.npy',scores),
        ('indices-modern-zyx.npy',indices),('new-unique-indices-modern-zyx.npy',unique_after[new_mask]),('new-unique-raw-score.npy',new_scores)):
        np.save(directory/name,array,allow_pickle=False)
    areas=np.load(pilot/(label+'-after')/'face-area-voxel2.npy',allow_pickle=False)*(pr['voxel_um']/1000)**2
    weights=areas[faceids]/counts[faceids]
    with (directory/'all-score-thresholds.csv').open('x') as stream:
        writer=csv.writer(stream);writer.writerow(['raw_score_threshold_not_ink_truth','new_unique_sampled_voxels_at_or_above'])
        writer.writerows((i,int(np.count_nonzero(new_scores>=i))) for i in range(256))
    summaries[label]=dict(before_faces=len(before),after_faces=len(after),added_faces=len(added),
        common_triangles_and_queries_bit_identical=True,after_quadrature_samples=len(points),
        before_unique_sampled_voxels=len(unique_before),after_unique_sampled_voxels=len(unique_after),
        new_unique_sampled_voxels=int(new_mask.sum()),new_unique_raw_min=int(new_scores.min()) if len(new_scores) else None,
        new_unique_raw_max=int(new_scores.max()) if len(new_scores) else None,
        new_unique_raw_ge128=int(np.count_nonzero(new_scores>=128)),threshold128_is_not_confirmed_ink=True,
        added_area_mm2=float(areas[added].sum()),added_center_area_weighted_mean=float(np.average(scores[is_added],weights=weights[is_added])))
    centroid_scores=sample(after.mean(1))[1]
    panels.append((label,before,after,common,added,centroid_scores))
# Render the same orthographic view and raw score scale in each ablation.
canvas=Image.new('RGB',(1100,990),'#151a20');draw=ImageDraw.Draw(canvas);font=ImageFont.load_default(size=16)
draw.text((20,12),'PAPYRUS ATLAS | Published score-field coverage before / after',font=font,fill='white')
draw.text((20,40),'Corrected NRRD axes. Cross-scan gate still rejected. No recovered letters claimed.',font=font,fill='#ffbf77')
for row,(label,before,after,common,added,scores) in enumerate(panels):
    center=after.reshape(-1,3).mean(0)
    camera=np.array([[.8660254,-.5,0],[.25,.4330127,-.8660254],[.4330127,.75,.5]])
    projected=(after-center)@camera.T;lower=projected[:,:,:2].min(axis=(0,1));upper=projected[:,:,:2].max(axis=(0,1))
    scale=min(475/max(upper[0]-lower[0],1e-6),330/max(upper[1]-lower[1],1e-6))
    for column,ids in enumerate((common,np.arange(len(after)))):
        ox=25+column*545;oy=105+row*420
        draw.text((ox,oy-25),f'{label.upper()} | '+('BEFORE' if column==0 else 'AFTER')+f' | {len(ids)} faces',font=font,fill='white')
        for i in sorted(ids,key=lambda i:float(projected[i,:,2].mean())):
            polygon=[(ox+int((p[0]-lower[0])*scale),oy+int((p[1]-lower[1])*scale)) for p in projected[i]]
            s=int(scores[i]);draw.polygon(polygon,fill=(s,s,s))
        if column:
            for i in added:
                polygon=[(ox+int((p[0]-lower[0])*scale),oy+int((p[1]-lower[1])*scale)) for p in projected[i]]
                draw.line(polygon+[polygon[0]],fill='#ff9b42',width=2)
draw.text((20,945),'Gray: published raw score 0..255. Orange: added geometry, never an ink label.',font=font,fill='white')
draw.text((20,968),'Orthographic geometry diagnostic; overlapping surfaces; not a flattened text image.',font=font,fill='white')
canvas.save(out/'before-after-score-coverage.png')
(out/'field-sources.json').write_text(json.dumps(dict(original_chunks=pred['chunks'],additional_chunks=extra_receipts),indent=2))
result=dict(guard=guard,summaries=summaries,same_scan_axis_bridge_validated=True,registration_validated=False,benefit_in_readable_letters_demonstrated=False,
    letters_verified=0,inference_executed_here=False,model_field='Preserved third-party public ink3D prediction',
    artifacts={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(summaries),flush=True)
