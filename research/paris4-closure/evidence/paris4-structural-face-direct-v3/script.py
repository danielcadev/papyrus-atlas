"""Direct observed-CT structural matching on the immutable old-only candidate set."""
from pathlib import Path
import itertools,json,sys,time,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from inspect_cube import read_nrrd
previous=root/'paris4-structural-face-selection-v1';prevresult=json.loads((previous/'result.json').read_text())
for name,sha in prevresult['artifacts'].items():assert digest(previous/name)==sha
selection=json.loads((previous/'old-only-selection-frozen.json').read_text());selected=selection['selected']
plan0=json.loads((previous/'plan.json').read_text())
out=root/'paris4-structural-face-direct-v3';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
plan=dict(plan0);plan.update(matching='All matching NCCs use direct64-midpoint observed modern CT, not interpolated footprint cache.',
    reused_old_only_selection_sha256=digest(previous/'old-only-selection-frozen.json'),
    selection_not_repeated=True,coarse_grid=[-2,-1,0,1,2],local_fine_max_evaluations=256,
    local_fine_max_seconds=40,total_score_budget=9216,
    reverse_check='Coarse reverse then bounded continuous refinement; norm<=.5, converged, interior. Reverse distant-grid competitor and six-control margins>=.1.',reverse_fine_max_evaluations=192,reverse_fine_max_seconds=20,
    provenance='New12 old-only conditioned face candidates; all corner-pilot failures remain preserved. Fresh C still not evaluated unless training-only model prerequisites pass.')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
shutil.copyfile(previous/'old-only-selection-frozen.json',out/'old-only-selection-frozen.json')
shutil.copyfile(previous/'support-proof-before-intensities.json',out/'support-proof-reused.json')
prior=root/'paris4-ink-benefit-v2/ct-registration-v3';baseplan=json.loads((prior/'plan.json').read_text())
A=np.array(baseplan['affine_oldXYZ_to_modernXYZ']);O=np.array([1744,2256,4048])
source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==baseplan['source_ct_sha256']
old,_=read_nrrd(source);oldfloat=old.astype(np.float32)
rawpath=prior/'observed-modern-ct-zyx-portable.npy';assert digest(rawpath)==json.loads((prior/'portable-array-receipt.json').read_text())['portable_sha256']
raw=np.load(rawpath,mmap_mode='r');rawstart=np.min([r['chunk'] for r in json.loads((prior/'ct-sources.json').read_text())['chunks']],axis=0)*128
(out/'input-receipt.json').write_text(json.dumps(dict(old_ct_sha256=digest(source),modern_CT_sha256=digest(rawpath),
    source_candidate_count=len(selected),same_candidates_as_previous=True,catalogue_affine=A.tolist(),raw_start_modern_zyx=rawstart.tolist()),indent=2)+'\n')
coarse=np.array(list(itertools.product(range(-2,3),repeat=3)),float)
patch=np.indices((7,)*3).reshape(3,-1).T-3
offsets=np.array(list(itertools.product((-.375,-.125,.125,.375),repeat=3)))
shifts=np.array(((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)))
count_total=0
class Budget(Exception):pass
def corr(a,b):
    global count_total
    if count_total>=9216:raise Budget()
    count_total+=1
    # Copy before centering: diagnostic witness arrays must remain raw CT.
    a=np.array(a,dtype=float,copy=True).ravel();b=np.array(b,dtype=float,copy=True).ravel()
    a-=a.mean();b-=b.mean();norm=np.sqrt(a@a*(b@b))
    return float(a@b/norm) if norm else -1.
def direct(p):
    result=np.empty(len(p))
    for i in range(0,len(p),512):
        expanded=(p[i:i+512,None,:]+offsets[None,:,:]).reshape(-1,3)
        q=((expanded+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-rawstart
        lo=np.floor(q).astype(int);f=q-lo;assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
        values=np.zeros(len(q))
        for corner in itertools.product((0,1),repeat=3):
            c=np.array(corner);values+=raw[tuple((lo+c).T)]*np.prod(np.where(c,f,1-f),axis=1)
        result[i:i+512]=values.reshape(-1,64).mean(axis=1)
    return result
matches=[]
for number,row in enumerate(selected):
    p=np.array(row['native_zyx']);points=p+patch;target=old[tuple(points.T)]
    scores=np.array([corr(target,direct(points+s)) for s in coarse]);winner=int(np.argmax(scores))
    initial=coarse[winner];best=(float(scores[winner]),initial.copy());calls=0;begin=time.monotonic()
    def objective(s):
        global calls,best
        if calls>=256 or time.monotonic()-begin>40:raise Budget()
        calls+=1;score=corr(target,direct(points+s))
        if score>best[0]:best=(score,s.copy())
        return -score
    try:
        run=minimize(objective,initial,method='Powell',bounds=[(-2,2)]*3,options=dict(maxfev=256,xtol=1e-4,ftol=1e-6));converged=bool(run.success);status=str(run.message)
    except Budget:converged=False;status='bounded_match_budget'
    score,s=best;boundary=bool(np.any(abs(s)>=1.9999));distinct=scores[np.linalg.norm(coarse-s,axis=1)>=2]
    distinct_margin=score-float(distinct.max()) if len(distinct) else -1.
    six={str(tuple(c)):corr(target,direct(points+s+c)) for c in shifts[1:]};margin=score-max(six.values())
    reasons=[]
    if not converged:reasons.append('local_fit_not_converged')
    if boundary:reasons.append('search_boundary')
    if score<.6:reasons.append('low_direct_NCC')
    if distinct_margin<.1:reasons.append('ambiguous_direct_peak')
    if margin<.1:reasons.append('direct_six_shift_margin')
    item=dict(candidate=number,native_zyx=p.tolist(),shift_native_zyx=s.tolist(),direct_pearson=score,
        distinct_peak_margin=distinct_margin,six_shift_margin=margin,controls=six,
        coarse_scores=scores.tolist(),fine_evaluations=calls,status=status,converged=converged,at_search_boundary=boundary)
    if not reasons:
        moving=direct(points+s);np.save(out/f'candidate-{number}-raw-modern.npy',moving,allow_pickle=False)
        np.save(out/f'candidate-{number}-old-target.npy',target,allow_pickle=False)
        reverse=np.array([corr(moving,map_coordinates(oldfloat,(points+d).T,order=1,prefilter=False)) for d in coarse])
        rindex=int(np.argmax(reverse));d=coarse[rindex].copy();rbest=(float(reverse[rindex]),d.copy());rcalls=0;rbegin=time.monotonic()
        def reverse_objective(d):
            global rcalls,rbest
            if rcalls>=192 or time.monotonic()-rbegin>20:raise Budget()
            rcalls+=1;value=corr(moving,map_coordinates(oldfloat,(points+d).T,order=1,prefilter=False))
            if value>rbest[0]:rbest=(value,d.copy())
            return -value
        try:
            rrun=minimize(reverse_objective,d,method='Powell',bounds=[(-2,2)]*3,options=dict(maxfev=192,xtol=1e-4,ftol=1e-6));rconverged=bool(rrun.success);rstatus=str(rrun.message)
        except Budget:rconverged=False;rstatus='bounded_reverse_budget'
        rscore,d=rbest
        rdistinct=reverse[np.linalg.norm(coarse-d,axis=1)>=2]
        rmargin=rscore-float(rdistinct.max()) if len(rdistinct) else -1.
        rcontrols=[corr(moving,map_coordinates(oldfloat,(points+d+c).T,order=1,prefilter=False)) for c in shifts[1:]]
        if not rconverged:reasons.append('reverse_fit_not_converged')
        if np.any(abs(d)>=1.9999):reasons.append('reverse_search_boundary')
        item.update(reverse_fine_evaluations=rcalls,reverse_status=rstatus,reverse_converged=rconverged)
        item.update(reverse_scores=reverse.tolist(),reverse_shift_native_zyx=d.tolist(),reciprocal_error=float(np.linalg.norm(d)),
            reverse_distinct_peak_margin=rmargin,reverse_six_shift_margin=rscore-max(rcontrols))
        if np.linalg.norm(d)>.5:reasons.append('nonreciprocal')
        if rmargin<.1:reasons.append('ambiguous_reverse_peak')
        if item['reverse_six_shift_margin']<.1:reasons.append('reverse_six_shift_margin')
    item['reliable']=not reasons;item['rejection_reasons']=reasons;matches.append(item)
    print(json.dumps(dict(stage='direct_structural_match',candidate=number,reliable=not reasons,pearson=score,
        distinct_margin=distinct_margin,shift=s.tolist(),reasons=reasons,total_score_evaluations=count_total)),flush=True)
    # Per-candidate checkpoint permits recovery after a timeout without overwriting.
    (out/f'match-{number:02d}.json').write_text(json.dumps(item,indent=2)+'\n')
(out/'matches.json').write_text(json.dumps(matches,indent=2)+'\n')
reliable=[r for r in matches if r['reliable']];model=None;decision='insufficient_reliable_structural_points'
if len(reliable)>=6:
    p=np.array([r['native_zyx'] for r in reliable],float)
    if np.linalg.matrix_rank(p-p.mean(axis=0))==3:
        hull=ConvexHull(p);corners=np.array(list(itertools.product((112,143),(144,175),(112,143))))
        if np.all(corners@hull.equations[:,:3].T+hull.equations[:,3]<=1e-9):
            s=np.median([r['shift_native_zyx'] for r in reliable],axis=0)
            model=dict(translation_native_zyx=s.tolist(),reliable_points=len(reliable),ROI_inside_spatial_hull=True,frozen_before_validation=True);decision='candidate_translation_frozen'
        else:decision='reliable_points_do_not_surround_full_ROI'
    else:decision='degenerate_correspondence_geometry'
(out/'model-decision-before-validation.json').write_text(json.dumps(dict(model=model,reason=decision),indent=2)+'\n')
validation={}
if model is not None:
    s=np.array(model['translation_native_zyx'])
    for name,box in (('fresh_C',plan0['fresh_reserve_C_native_zyx']),('original_ROI',([112,144,112],[144,176,144]))):
        low=np.array(box[0])-4;shape=tuple(np.array(box[1])-box[0]+8);p=np.indices(shape).reshape(3,-1).T+low
        values=direct(p+s).reshape(shape).astype('<f4');np.save(out/(name+'-modern.npy'),values,allow_pickle=False)
        target=old[tuple(slice(a,b) for a,b in zip(*box))];scores={}
        for c in shifts:scores[str(tuple(c))]=corr(target,values[tuple(slice(4+d,4+d+n) for d,n in zip(c,target.shape))])
        primary=scores[str(tuple(shifts[0]))];margin=primary-max(v for k,v in scores.items() if k!=str(tuple(shifts[0])))
        validation[name]=dict(primary_pearson=primary,margin=margin,controls=scores,gate_passed=bool(primary>=.6 and margin>=.1))
result=dict(guard=guard,selected_candidates=len(selected),reliable_points=len(reliable),score_evaluations=count_total,
    model_decision=decision,model=model,validation=validation,registration_accepted=bool(model is not None and all(r['gate_passed'] for r in validation.values())),
    fresh_C_targets_not_evaluated=model is None,geometry_or_uv_modified=False,ink_used=False,letters_verified=0,
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(completed=True,reliable=len(reliable),decision=decision,accepted=result['registration_accepted'])),flush=True)
