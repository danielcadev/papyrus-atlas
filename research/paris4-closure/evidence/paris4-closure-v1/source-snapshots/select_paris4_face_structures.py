"""Select old-only spatially conditioned exterior face features, preserving C."""
from pathlib import Path
import json,itertools,sys,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
from inspect_cube import read_nrrd
root=Path(__file__).resolve().parent;previous=root/'paris4-structural-matches-v1'
out=root/'paris4-structural-face-selection-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
plan=json.loads((previous/'plan.json').read_text())
territories=[([92,148,112],[100,164,124]),([156,148,112],[164,164,124]),
    ([112,124,112],[144,132,144]),([112,188,112],[144,196,144]),
    ([112,148,92],[144,176,100]),([112,148,156],[144,176,164])]
plan.update(training_territories_native_zyx=territories,max_candidates=12,max_per_territory=2,
    ranking='Old-only eigenvalue-ratio descending, then smallest eigenvalue, then coordinates; favor conditioning over absolute brightness.',
    input_eigenvalue_array_reused=True,model='Median translation if >=6 accepted direct reciprocal points surround full original ROI; no affine escalation.',
    reserve_wording='Global old-crop filters previously read C bytes. C is excluded from all finite selection supports and matching objectives, and its admission gate has not been evaluated.',
    matching='Selection only. Exact direct matcher has its own frozen plan.')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
receipt=json.loads((previous/'input-receipt.json').read_text());A=np.array(receipt['catalogue_affine']);B=A[:,:3][::-1,::-1]
projection=np.abs(np.linalg.inv(B)).sum(axis=1)
reserve=plan['fresh_reserve_C_native_zyx'];guardlo=np.array([107.5,139.5,107.5]);guardhi=np.array([148,180,148])
rlo=np.array(reserve[0])-6-.375-projection;rhi=np.array(reserve[1])-1+6+.375+projection
proof=[]
for box in territories:
    lo=np.array(box[0])-6-.375-projection;hi=np.array(box[1])-1+6+.375+projection
    rgap=np.maximum(rlo-hi,lo-rhi);ggap=np.maximum(guardlo-hi,lo-guardhi)
    assert rgap.max()>0 and ggap.max()>0
    oldlo=np.array(box[0])-7;oldhi=np.array(box[1])-1+7
    assert np.maximum(guardlo-oldhi,oldlo-guardhi).max()>0
    assert np.maximum(rlo-oldhi,oldlo-rhi).max()>0
    proof.append(dict(territory=box,projected_modern_lower=lo.tolist(),projected_modern_upper=hi.tolist(),
        separation_gap_from_C=float(rgap.max()),separation_gap_from_guard=float(ggap.max()),old_reverse_support_passed=True))
(out/'support-proof-before-intensities.json').write_text(json.dumps(dict(passed=True,projection_padding=projection.tolist(),territories=proof,
    scope='All direct matching shifts +/-2, six +/-4 controls, midpoint quadrature, modern raw interpolation and reverse old interpolation.'),indent=2)+'\n')
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==receipt['source_ct_sha256']
old,_=read_nrrd(source)
eigenpath=previous/'old-structure-eigenvalues.npy';assert digest(eigenpath)==json.loads((previous/'result.json').read_text())['artifacts'][eigenpath.name]
eigen=np.load(eigenpath,mmap_mode='r');patch=np.indices((7,)*3).reshape(3,-1).T-3;low=np.array([84,116,84])
catalogue=[];selected=[]
for number,box in enumerate(territories):
    centers=np.indices(tuple(np.array(box[1])-box[0]-6)).reshape(3,-1).T+np.array(box[0])+3;ranked=[]
    for p in centers:
        e=eigen[tuple(p-low)];ratio=float(e[0]/e[2]) if e[2]>0 else 0.;std=float(old[tuple((p+patch).T)].std())
        eligible=bool(e[0]>=1 and ratio>=.02 and std>=8)
        row=dict(territory=number,native_zyx=p.tolist(),eigenvalues=e.tolist(),eigenvalue_ratio=ratio,old_patch_std=std,eligible=eligible,selected=False)
        catalogue.append(row)
        if eligible:ranked.append(row)
    ranked.sort(key=lambda r:(-r['eigenvalue_ratio'],-r['eigenvalues'][0],r['native_zyx']))
    chosen=[]
    for row in ranked:
        p=np.array(row['native_zyx'])
        if all(np.linalg.norm(p-q)>=5 for q in chosen):row['selected']=True;selected.append(row);chosen.append(p)
        if len(chosen)==2:break
(out/'old-only-selection-frozen.json').write_text(json.dumps(dict(candidates=catalogue,selected=selected,selected_before_cross_scan_queries=True),indent=2)+'\n')
result=dict(guard=guard,selected=len(selected),eligible=sum(r['eligible'] for r in catalogue),
    old_eigen_array_sha256=digest(eigenpath),old_ct_sha256=digest(source),fresh_C_excluded_from_selection=True,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(selected=len(selected),eligible=result['eligible'],support_passed=True)),flush=True)
