"""Independent raw CT, support, reliability and legacy-witness audit."""
from pathlib import Path
import json,itertools,sys,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native/local-uv-deps'))
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
from inspect_cube import read_nrrd
out=root/'paris4-structural-audit-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
base=root/'paris4-ink-benefit-v2/ct-registration-v3';plan=json.loads((base/'plan.json').read_text());A=np.array(plan['affine_oldXYZ_to_modernXYZ']);B=A[:,:3][::-1,::-1]
O=np.array([1744,2256,4048]);source=root/'data/01744_02256_04048_volume.nrrd';assert digest(source)==plan['source_ct_sha256']
old,_=read_nrrd(source);oldfloat=old.astype(np.float32)
rawpath=base/'observed-modern-ct-zyx-portable.npy';assert digest(rawpath)==json.loads((base/'portable-array-receipt.json').read_text())['portable_sha256']
raw=np.load(rawpath,mmap_mode='r');start=np.min([r['chunk'] for r in json.loads((base/'ct-sources.json').read_text())['chunks']],axis=0)*128
cached=np.load(root/'paris4-registration-anchors-v1/corrected-footprint-fit-v1/modern-footprint-grid-native-zyx.npy')
patch=np.indices((7,)*3).reshape(3,-1).T-3;offsets=np.array(list(itertools.product((-.375,-.125,.125,.375),repeat=3)))
coarse=np.array(list(itertools.product(range(-2,3),repeat=3)),float)
controls=np.array([(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)])
def corr(a,b):
    a=np.array(a,dtype=float,copy=True).ravel();b=np.array(b,dtype=float,copy=True).ravel();a-=a.mean();b-=b.mean()
    return float(a@b/np.sqrt(a@a*(b@b)))
def sample(p):
    q=((p+O)[:,::-1]@A[:,:3].T+A[:,3])[:,::-1]-start
    lo=np.floor(q).astype(int);f=q-lo;assert (lo>=0).all() and np.all(lo+1<np.array(raw.shape))
    values=np.zeros(len(p))
    for c in itertools.product((0,1),repeat=3):
        c=np.array(c);values+=raw[tuple((lo+c).T)]*np.prod(np.where(c,f,1-f),axis=1)
    return values
# Two distinct implementations exercise vector layout against scalar-offset
# accumulation. Both preserve the exact predeclared midpoint coordinates.
def direct(p):return sample((p[:,None,:]+offsets[None,:,:]).reshape(-1,3)).reshape(-1,64).mean(axis=1)
def scalar_offsets(p):
    v=np.zeros(len(p))
    for offset in offsets:v+=sample(p+offset)/64
    return v
projection=np.abs(np.linalg.inv(B)).sum(axis=1);protected_lo=np.array([107.5,139.5,107.5]);protected_hi=np.array([148,180,148])
Clo=np.array([87.5,147.5,139.5]);Chi=np.array([95.5,163.5,155.5])
selection_checks=[];case_checks=[];legacy=[];continuous=[]
folders=('paris4-structural-matches-v1','paris4-structural-direct-v2','paris4-structural-face-direct-v3')
for folder in folders:
    case=root/folder;r=json.loads((case/'result.json').read_text())
    for relative,sha in r['artifacts'].items():assert digest(case/relative)==sha
    selected=json.loads((case/'old-only-selection-frozen.json').read_text())['selected']
    matches=json.loads((case/'matches.json').read_text());assert len(matches)==len(selected)
    for row in selected:
        p=np.array(row['native_zyx']);lo=p-4-.5;hi=p+4+.5
        assert np.maximum(protected_lo-hi,lo-protected_hi).max()>0
        assert np.maximum(Clo-hi,lo-Chi).max()>0
        assert row['eigenvalues'][0]>=1 and row['eigenvalue_ratio']>=.02 and row['old_patch_std']>=8
        assert abs(float(old[tuple((p+patch).T)].std())-row['old_patch_std'])<1e-12
        # Every reverse query and interpolation node remains inside old CT.
        assert (p+patch-7>=0).all() and np.all(p+patch+7<np.array(old.shape))
    selection_checks.append(dict(case=folder,selected=len(selected),all_selected_filter_support_excludes_C_and_guard=True,
        caveat='The original global filter did read C/ROI input bytes; only selected outputs have disjoint finite dependencies.'))
    for row in matches:
        number=row['candidate'];p=np.array(row['native_zyx'])+patch;s=np.array(row['shift_native_zyx']);target=old[tuple(p.T)]
        values=direct(p+s);score=corr(target,values)
        if folder=='paris4-structural-matches-v1':
            cachevalues=map_coordinates(cached,(p+s-[84,116,84]).T,order=1,prefilter=False)
            assert abs(corr(target,cachevalues)-row['cache_pearson'])<1e-11
            witness=case/f'candidate-{number}-direct-modern.npy'
            if witness.exists():
                rawvalues=scalar_offsets(p+s)
                np.save(out/f'pilot-candidate-{number}-corrected-raw-modern.npy',rawvalues,allow_pickle=False)
                centered=(rawvalues-rawvalues.mean()).astype('<f4');saved=np.load(witness)
                error=float(np.max(abs(centered-saved)));assert error<4e-5
                assert abs(score-row['direct_pearson'])<1e-11
                legacy.append(dict(candidate=number,saved_witness_was_mean_centered=True,centered_replay_max_abs_error=error,
                    corrected_raw_witness_sha256=digest(out/f'pilot-candidate-{number}-corrected-raw-modern.npy')))
            continue
        assert abs(score-row['direct_pearson'])<1e-11
        competitors=np.array(row['coarse_scores'])[np.linalg.norm(coarse-s,axis=1)>=2]
        distinct=score-float(competitors.max());assert abs(distinct-row['distinct_peak_margin'])<1e-11
        rival_indices=np.where(np.linalg.norm(coarse-s,axis=1)>=2)[0]
        rival_index=rival_indices[int(np.argmax(competitors))]
        assert abs(corr(target,direct(p+coarse[rival_index]))-row['coarse_scores'][rival_index])<1e-11
        control_values=[corr(target,direct(p+s+c)) for c in controls]
        assert np.max(abs(np.array(control_values)-list(row['controls'].values())))<1e-11
        margin=score-max(control_values);assert abs(margin-row['six_shift_margin'])<1e-11
        reasons=[]
        if not row['converged']:reasons.append('local_fit_not_converged')
        if np.any(abs(s)>=1.9999):reasons.append('search_boundary')
        if score<.6:reasons.append('low_direct_NCC')
        if distinct<.1:reasons.append('ambiguous_direct_peak')
        if margin<.1:reasons.append('direct_six_shift_margin')
        if not reasons:
            saved=np.load(case/f'candidate-{number}-raw-modern.npy');assert np.max(abs(saved-values))<1e-10
            reverse=np.array([corr(values,map_coordinates(oldfloat,(p+d).T,order=1,prefilter=False)) for d in coarse])
            assert np.max(abs(reverse-row['reverse_scores']))<1e-10
            if folder=='paris4-structural-direct-v2':
                d=coarse[int(np.argmax(reverse))];reverse_best=float(reverse.max())
                # Supplement the integer-grid check with a continuous reverse
                # refinement. This never refits the forward or any held-out ROI.
                calls=0;best=(reverse_best,d.copy())
                def objective(d):
                    nonlocal_placeholder=None
                    global calls,best
                    calls+=1;value=corr(values,map_coordinates(oldfloat,(p+d).T,order=1,prefilter=False))
                    if value>best[0]:best=(value,d.copy())
                    return -value
                run=minimize(objective,d,method='Powell',bounds=[(-2,2)]*3,options=dict(maxfev=192,xtol=1e-4,ftol=1e-6))
                continuous.append(dict(case=folder,candidate=number,reverse_fine_parameters=best[1].tolist(),
                    continuous_reciprocal_norm=float(np.linalg.norm(best[1])),converged=bool(run.success),evaluations=calls,
                    scope='Stricter supplemental consistency diagnostic; candidate already rejected by reverse ambiguity.'))
            else:d=np.array(row['reverse_shift_native_zyx']);reverse_best=corr(values,map_coordinates(oldfloat,(p+d).T,order=1,prefilter=False))
            reverse_distinct=reverse_best-float(reverse[np.linalg.norm(coarse-d,axis=1)>=2].max())
            if np.linalg.norm(d)>.5:reasons.append('nonreciprocal')
            if reverse_distinct<.1:reasons.append('ambiguous_reverse_peak')
            reverse_controls=[corr(values,map_coordinates(oldfloat,(p+d+c).T,order=1,prefilter=False)) for c in controls]
            if reverse_best-max(reverse_controls)<.1:reasons.append('reverse_six_shift_margin')
        assert bool(reasons)==(not row['reliable'])
        case_checks.append(dict(case=folder,candidate=number,raw_forward_and_six_controls_replayed=True,
            competing_grid_peak_replayed=True,direct_pearson=score,reliable=row['reliable']))
    assert not r['registration_accepted'] and r['model'] is None
# Vectorized versus original accumulation, separately exercised on varied cells.
p=np.array([[99.,127.,95.],[159.4,191.2,158.8],[96.5,155.25,118.75]])
error=float(np.max(abs(direct(p)-scalar_offsets(p))));assert error<1e-9
previous=root/'paris4-independent-validation-v1';manifest=json.loads((previous/'evidence-manifest-v1.json').read_text())
for relative,row in manifest['files'].items():assert digest(previous/relative)==row['sha256']
result=dict(guard=guard,passed=True,previous_sealed_files_unchanged=len(manifest['files']),
    selection_checks=selection_checks,direct_match_checks=case_checks,legacy_witness_correction=legacy,
    continuous_reverse_diagnostics=continuous,vector_vs_scalar_footprint_max_abs_error=error,
    cache_pilot_four_points_are_provisional_and_superseded=True,final_reliable_direct_points=0,
    fresh_C_not_used_for_selected_outputs_or_fitting_and_not_admission_evaluated=True,
    registration_accepted=False,geometry_or_uv_modified=False,ink_used=False,letters_verified=0)
(out/'verification-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,raw_cases_replayed=len(case_checks),legacy_witnesses=len(legacy),vectorization_error=error)),flush=True)
