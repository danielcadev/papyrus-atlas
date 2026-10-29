"""Old-CT structural selection and reciprocal bounded exterior patch matches."""
from pathlib import Path
import itertools,json,sys,time,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from inspect_cube import read_nrrd
out=root/'paris4-structural-matches-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
prior=root/'paris4-ink-benefit-v2/ct-registration-v3';baseplan=json.loads((prior/'plan.json').read_text())
A=np.array(baseplan['affine_oldXYZ_to_modernXYZ']);B=A[:,:3][::-1,::-1];O=np.array([1744,2256,4048]);low=np.array([84,116,84])
territories=[([z,y,x],[z+12,y+8,x+12]) for z,y,x in itertools.product((96,152),(124,188),(92,152))]
reserve=([88,148,140],[96,164,156]);protected=([107.5,139.5,107.5],[148,180,148])
shifts=((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4))
plan=dict(guard=guard,training_territories_native_zyx=territories,fresh_reserve_C_native_zyx=reserve,
    selection='Old CT only: Gaussian derivative sigma1/truncate2, tensor integration sigma1/truncate2, smallest eigenvalue strength.',
    patch_side=7,selection_min_eigenvalue=1.,selection_min_eigenvalue_ratio=.02,old_patch_std_min=8.,
    max_per_territory=2,max_candidates=16,nms_native_distance_min=5.,
    matching='Raw patch NCC; coarse integer shifts -2..2, bounded Powell fine shift +/-2; no prior optimized initializer.',
    local_fine_max_evaluations=256,local_fine_max_seconds=20,total_score_budget=9216,
    reliability=dict(pearson_min=.6,distinct_peak_margin_min=.1,distinct_peak_exclusion_radius=2.,
        six_shift_control_margin_min=.1,reciprocal_error_max=.5,interior_peak_required=True,
        direct_observed_modern_confirmation=True),
    model='Componentwise median translation only, if >=6 reliable points surround the entire repaired ROI in their spatial hull. No affine escalation.',
    admission=dict(pearson_min=.6,margin_min=.1,shift_controls_native_zyx=shifts,require_original_ROI_and_fresh_C=True),
    caveats='Same scans and previously cached modern intensities. Reciprocal/structural consistency is not independent anatomy. ROI and A/B previously inspected; C targets are newly withheld.',
    geometry_or_uv_modified=False,ink_used=False,letters_verified=0)
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
# Project all raw-modern support into nominal native coordinates. The cache
# adds <=1 grid cell, quadrature .375 and raw modern trilinear <=|B^-1|1.
projection=np.abs(np.linalg.inv(B)).sum(axis=1)
train_padding=6+1+.375+projection
reserve_padding=4+2+.375+projection
reserved_lo=np.array(reserve[0])-reserve_padding;reserved_hi=np.array(reserve[1])-1+reserve_padding
support=[]
for box in territories:
    lo=np.array(box[0])-train_padding;hi=np.array(box[1])-1+train_padding
    gap=np.maximum(reserved_lo-hi,lo-reserved_hi);assert gap.max()>0
    guardgap=np.maximum(np.array(protected[0])-hi,lo-np.array(protected[1]));assert guardgap.max()>0
    # Reverse old interpolation plus +/-6 controls is bounded by seven cells.
    oldlo=np.array(box[0])-7;oldhi=np.array(box[1])-1+7
    assert np.maximum(np.array(protected[0])-oldhi,oldlo-np.array(protected[1])).max()>0
    support.append(dict(training_box=box,projected_modern_lower=lo.tolist(),projected_modern_upper=hi.tolist(),
        separation_gap_from_reserve=float(gap.max()),separation_gap_from_guard=float(guardgap.max())))
(out/'support-proof-before-intensities.json').write_text(json.dumps(dict(passed=True,projection_padding=projection.tolist(),territories=support,
    reserve_projected_lower=reserved_lo.tolist(),reserve_projected_upper=reserved_hi.tolist(),scope='All local +/-2 searches, +/-4 controls, interpolation and footprint supports. Translation model only.'),indent=2)+'\n')
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==baseplan['source_ct_sha256']
old,_=read_nrrd(source)
cached=root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy'
assert digest(cached)==json.loads((root/'paris4-independent-controls-v1/input-receipt.json').read_text())['cached_grid_sha256']
footprint=np.load(cached)
(out/'input-receipt.json').write_text(json.dumps(dict(source_ct_sha256=digest(source),cached_footprint_sha256=digest(cached),catalogue_affine=A.tolist()),indent=2)+'\n')
# The old selection filter has total radius four; every candidate lies inside
# its fixed territory with patch radius three, so filter support remains far
# from the protected ROI and reserve.
crop=old[84:172,116:204,84:172].astype(np.float32)
grad=[gaussian_filter(crop,1,order=tuple(int(j==i) for j in range(3)),truncate=2) for i in range(3)]
tensor=np.empty(crop.shape+(3,3),dtype=np.float32)
for i in range(3):
    for j in range(i,3):tensor[...,i,j]=tensor[...,j,i]=gaussian_filter(grad[i]*grad[j],1,truncate=2)
eigen=np.linalg.eigvalsh(tensor);del tensor,grad,crop
np.save(out/'old-structure-eigenvalues.npy',eigen,allow_pickle=False)
patch=np.indices((7,)*3).reshape(3,-1).T-3
catalogue=[];selected=[]
for number,box in enumerate(territories):
    centers=np.indices(tuple(np.array(box[1])-box[0]-6)).reshape(3,-1).T+np.array(box[0])+3
    ranked=[]
    for p in centers:
        e=eigen[tuple(p-low)];ratio=float(e[0]/e[2]) if e[2]>0 else 0.;std=float(old[tuple((p+patch).T)].std())
        eligible=bool(e[0]>=1 and ratio>=.02 and std>=8)
        row=dict(territory=number,native_zyx=p.tolist(),eigenvalues=e.tolist(),eigenvalue_ratio=ratio,old_patch_std=std,eligible=eligible,selected=False)
        catalogue.append(row)
        if eligible:ranked.append(row)
    ranked.sort(key=lambda r:(-r['eigenvalues'][0],r['native_zyx']))
    chosen=[]
    for row in ranked:
        p=np.array(row['native_zyx'])
        if all(np.linalg.norm(p-q)>=5 for q in chosen):
            row['selected']=True;selected.append(row);chosen.append(p)
        if len(chosen)==2:break
(out/'old-only-selection-frozen.json').write_text(json.dumps(dict(candidates=catalogue,selected=selected,selected_before_cross_scan_queries=True),indent=2)+'\n')
print(json.dumps(dict(stage='old_structure_selection',eligible=sum(r['eligible'] for r in catalogue),selected=len(selected))),flush=True)
score_count=0
class Budget(Exception):pass
def corr(a,b):
    global score_count
    if score_count>=9216:raise Budget()
    score_count+=1;a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a-=a.mean();b-=b.mean()
    denominator=np.sqrt((a*a).sum()*(b*b).sum());return float((a*b).sum()/denominator) if denominator else -1.
def field(p):
    q=p-low;assert (q>=0).all() and np.all(q<np.array(footprint.shape)-1)
    return map_coordinates(footprint,q.T,order=1,prefilter=False)
coarse=np.array(list(itertools.product(range(-2,3),repeat=3)))
rawpath=prior/'observed-modern-ct-zyx-portable.npy';assert digest(rawpath)==json.loads((prior/'portable-array-receipt.json').read_text())['portable_sha256']
raw=np.load(rawpath,mmap_mode='r');rawstart=np.min([r['chunk'] for r in json.loads((prior/'ct-sources.json').read_text())['chunks']],axis=0)*128
def rawsample(p):
    q=((p+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-rawstart
    lo=np.floor(q).astype(int);f=q-lo;assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
    values=np.zeros(len(p))
    for corner in itertools.product((0,1),repeat=3):
        c=np.array(corner);values+=raw[tuple((lo+c).T)]*np.prod(np.where(c,f,1-f),axis=1)
    return values
def direct(p):
    result=np.zeros(len(p))
    for offset in itertools.product((-.375,-.125,.125,.375),repeat=3):
        for i in range(0,len(p),32768):result[i:i+32768]+=rawsample(p[i:i+32768]+offset)/64
    return result
matches=[]
for number,row in enumerate(selected):
    p=np.array(row['native_zyx']);points=p+patch;target=old[tuple(points.T)]
    scores=np.array([corr(target,field(points+s)) for s in coarse]);winner=int(np.argmax(scores));initial=coarse[winner].astype(float)
    best=(float(scores[winner]),initial.copy());count=0;begin=time.monotonic()
    def objective(s):
        global best,count
        if count>=256 or time.monotonic()-begin>20:raise Budget()
        count+=1;value=corr(target,field(points+s))
        if value>best[0]:best=(value,s.copy())
        return -value
    try:
        run=minimize(objective,initial,method='Powell',bounds=[(-2,2)]*3,options=dict(maxfev=256,xtol=1e-4,ftol=1e-6));converged=bool(run.success);status=str(run.message)
    except Budget:converged=False;status='bounded_match_budget'
    score,s=best;boundary=bool(np.any(abs(s)>=1.9999))
    competitors=scores[np.linalg.norm(coarse-s,axis=1)>=2]
    distinct_margin=score-float(competitors.max()) if len(competitors) else -1.
    controls={str(tuple(c)):corr(target,field(points+s+c)) for c in shifts[1:]}
    control_margin=score-max(controls.values())
    reasons=[]
    if not converged:reasons.append('local_fit_not_converged')
    if boundary:reasons.append('search_boundary')
    if score<.6:reasons.append('low_NCC')
    if distinct_margin<.1:reasons.append('ambiguous_distinct_peak')
    if control_margin<.1:reasons.append('six_shift_margin')
    item=dict(candidate=number,native_zyx=p.tolist(),shift_native_zyx=s.tolist(),cache_pearson=score,
        distinct_peak_margin=distinct_margin,six_shift_margin=control_margin,coarse_scores=scores.tolist(),fine_evaluations=count,status=status,at_search_boundary=boundary)
    if not reasons:
        moving=field(points+s)
        reverse_scores=np.array([corr(moving,map_coordinates(old.astype(np.float32),(points+d).T,order=1,prefilter=False)) for d in coarse])
        reverse_shift=coarse[int(np.argmax(reverse_scores))]
        item['reverse_shift_native_zyx']=reverse_shift.tolist();item['reciprocal_error']=float(np.linalg.norm(reverse_shift))
        if item['reciprocal_error']>.5:reasons.append('nonreciprocal')
        direct_values=direct(points+s);direct_score=corr(target,direct_values)
        direct_controls=[corr(target,direct(points+s+c)) for c in shifts[1:]]
        item['direct_pearson']=direct_score;item['direct_six_shift_margin']=direct_score-max(direct_controls)
        np.save(out/f'candidate-{number}-direct-modern.npy',direct_values.astype('<f4'),allow_pickle=False)
        if direct_score<.6 or item['direct_six_shift_margin']<.1:reasons.append('direct_CT_confirmation_failed')
    item['reliable']=not reasons;item['rejection_reasons']=reasons;matches.append(item)
    print(json.dumps(dict(stage='structural_match',candidate=number,reliable=not reasons,reasons=reasons,pearson=score,distinct_margin=distinct_margin)),flush=True)
(out/'matches.json').write_text(json.dumps(matches,indent=2)+'\n')
reliable=[r for r in matches if r['reliable']];model=None;reason='insufficient_reliable_structural_points'
if len(reliable)>=6:
    p=np.array([r['native_zyx'] for r in reliable],float);hull=ConvexHull(p)
    corners=np.array(list(itertools.product((112,143),(144,175),(112,143))))
    surrounds=bool(np.all(corners@hull.equations[:,:3].T+hull.equations[:,3]<=1e-9))
    if surrounds:
        s=np.median([r['shift_native_zyx'] for r in reliable],axis=0)
        model=dict(translation_native_zyx=s.tolist(),reliable_points=len(reliable),ROI_inside_spatial_hull=True,frozen_before_validation=True)
        reason='candidate_translation_frozen'
    else:reason='reliable_points_do_not_surround_full_ROI'
(out/'model-decision-before-validation.json').write_text(json.dumps(dict(reason=reason,model=model),indent=2)+'\n')
validation={}
if model is not None:
    s=np.array(model['translation_native_zyx'])
    for name,box in (('fresh_C',reserve),('original_ROI',([112,144,112],[144,176,144]))):
        start=np.array(box[0])-4;shape=tuple(np.array(box[1])-box[0]+8)
        p=np.indices(shape).reshape(3,-1).T+start
        values=direct(p+s).reshape(shape).astype('<f4');np.save(out/(name+'-modern.npy'),values,allow_pickle=False)
        target=old[tuple(slice(a,b) for a,b in zip(*box))];scores={}
        for c in shifts:scores[str(tuple(c))]=corr(target,values[tuple(slice(4+d,4+d+n) for d,n in zip(c,target.shape))])
        primary=scores[str((0,0,0))];margin=primary-max(v for k,v in scores.items() if k!=str((0,0,0)))
        validation[name]=dict(primary_pearson=primary,margin=margin,controls=scores,gate_passed=bool(primary>=.6 and margin>=.1))
result=dict(guard=guard,selected_candidates=len(selected),reliable_points=len(reliable),score_evaluations=score_count,
    model_decision=reason,model=model,validation=validation,registration_accepted=bool(model is not None and all(r['gate_passed'] for r in validation.values())),
    fresh_C_targets_not_queried=model is None,geometry_or_uv_modified=False,ink_used=False,letters_verified=0,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(completed=True,reliable=len(reliable),decision=reason,accepted=result['registration_accepted'])),flush=True)
