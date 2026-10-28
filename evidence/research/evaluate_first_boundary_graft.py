"""Post-hoc annotation, area and non-empty coverage checks of frozen masks."""
from collections import Counter
import itertools
import json
import sys
import numpy as np
from PIL import Image
from guard import start_guard
from evaluate_native import NATIVE, local_zarr, identities
from inspect_cube import read_nrrd

start_guard()
base = NATIVE.parent/'scrollfiesta-comparison'
labels, _ = read_nrrd(NATIVE.parent/'data/00768_02408_03536_mask.nrrd')
ctmask = local_zarr(NATIVE/'prediction-original-ct-otsu.zarr') > 0
path = np.asarray(json.loads((NATIVE/'exact-target-ct-diagnostic.json').read_text())['path_xyz'])
seed, goal = np.array([16,104,32]), np.array([53,56,32])
domain_low = path.min(axis=0)-8
domain_high = path.max(axis=0)+8
coverage_domain = np.argwhere(labels == 390)
coverage_domain = coverage_domain[((coverage_domain>=domain_low)&(coverage_domain<=domain_high)).all(axis=1)]
coverage_domain_codes = set(np.ravel_multi_index(coverage_domain.T,labels.shape))
def counts(points, radius):
    return dict(Counter(map(str,identities(labels,points,radius))))

def mesh(name, select_seed_component=True):
    folder = 'guided' if name == 'original6' else name
    files = list((base/f'{folder}-obj').glob('*/*step11_kibble/*_all.obj'))
    assert len(files) == 1
    logpath = NATIVE/'scrollfiesta-guided-dump.log' if name == 'original6' else base/f'{name}-meshing.log'
    log = logpath.read_text()
    assert 'Status: OK' in log
    assert 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in log
    vertices, faces = [], []
    for line in files[0].read_text().splitlines():
        if line.startswith('v '): vertices.append(list(map(float,line.split()[1:4])))
        elif line.startswith('f '): faces.append([int(s.split('/')[0])-1 for s in line.split()[1:]])
    xyz = (np.asarray(vertices)-[768,2408,3536])[:,::-1]
    faces = np.asarray(faces,dtype=int)
    assert faces.shape[1] == 3
    parent = np.arange(len(xyz))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a,b,c in faces:
        parent[find(b)] = find(a)
        parent[find(c)] = find(a)
    components = np.array([find(i) for i in range(len(xyz))])
    chosen = components[np.argmin(np.linalg.norm(xyz-seed,axis=1))]
    if select_seed_component:
        faces = faces[(components[faces]==chosen).all(axis=1)]
    selected = np.unique(faces)
    p = xyz[selected]
    roi = ((p>=[48,40,24])&(p<[59,112,41])).all(axis=1)
    samples, weights = [], []
    total_area = 0.
    for a,b,c in xyz[faces]:
        area = np.linalg.norm(np.cross(b-a,c-a))/2
        total_area += area
        n = max(1,int(np.ceil(max(np.linalg.norm(b-a),np.linalg.norm(c-a),np.linalg.norm(c-b))/.75)))
        uv = []
        for i in range(n):
            for j in range(n-i):
                uv.append(((i+1/3)/n,(j+1/3)/n))
                if i+j<n-1: uv.append(((i+2/3)/n,(j+2/3)/n))
        assert len(uv) == n*n
        uv = np.asarray(uv)
        samples.append(a+uv[:,0,None]*(b-a)+uv[:,1,None]*(c-a))
        weights.append(np.full(n*n,area/(n*n)))
    samples, weights = np.concatenate(samples),np.concatenate(weights)
    sample_roi = ((samples>=[48,40,24])&(samples<[59,112,41])).all(axis=1)
    tri = xyz[faces]
    a,b,c = tri[:,0],tri[:,1],tri[:,2]
    u,v,w = b-a,c-a,goal-a
    uu,uv,vv = np.sum(u*u,axis=1),np.sum(u*v,axis=1),np.sum(v*v,axis=1)
    wu,wv = np.sum(w*u,axis=1),np.sum(w*v,axis=1)
    denominator = uu*vv-uv*uv
    safe = np.where(denominator>1e-14,denominator,1)
    s,r = (vv*wu-uv*wv)/safe,(uu*wv-uv*wu)/safe
    projection = a+s[:,None]*u+r[:,None]*v
    inside = (denominator>1e-14)&(s>=0)&(r>=0)&(s+r<=1)
    distance_to_surface = float(np.linalg.norm(projection[inside]-goal,axis=1).min()) if inside.any() else float('inf')
    for left,right in [(a,b),(b,c),(c,a)]:
        edge = right-left
        t = np.clip(np.sum((goal-left)*edge,axis=1)/np.maximum(np.sum(edge*edge,axis=1),1e-14),0,1)
        distance_to_surface = min(distance_to_surface,float(np.linalg.norm(left+t[:,None]*edge-goal,axis=1).min()))
    area_by_id = {}
    for radius in [0,2]:
        ids = identities(labels,samples,radius)
        area_by_id[str(radius)] = {str(k):float(weights[ids==k].sum()) for k in np.unique(ids)}
    # Unique annotated voxels touched within one voxel of a dense face sample.
    covered = set()
    for d in itertools.product((-1,0,1),repeat=3):
        q = np.rint(samples).astype(int)+d
        good = ((q>=0)&(q<256)).all(axis=1)&(np.linalg.norm(q-samples,axis=1)<=1)
        q = q[good]
        q = q[labels[tuple(q.T)] == 390]
        covered.update(np.ravel_multi_index(q.T,labels.shape))
    covered &= coverage_domain_codes
    rounded = np.rint(samples).astype(int)
    supported = np.zeros(len(samples),dtype=bool)
    for d in itertools.product((-1,0,1),repeat=3):
        q = rounded+d
        good = ((q>=0)&(q<128)).all(axis=1)&(np.linalg.norm(q-samples,axis=1)<=1)
        ix = np.flatnonzero(good)
        supported[ix] |= ctmask[tuple(q[ix,::-1].T)]
    return dict(vertices=len(p),triangles=len(faces),total_components=len(np.unique(components)),
        nearest_seed_vertex_voxels=float(np.linalg.norm(p-seed,axis=1).min()),
        nearest_goal_vertex_voxels=float(np.linalg.norm(p-goal,axis=1).min()),
        nearest_goal_triangle_surface_voxels=distance_to_surface,
        face_samples_in_roi=int(sample_roi.sum()),
        roi_face_sample_reference_counts_radius0=counts(samples[sample_roi],0),
        roi_face_sample_reference_counts_radius2=counts(samples[sample_roi],2),
        roi_vertices=int(roi.sum()),vertex_reference_counts_radius0=counts(p,0),
        vertex_reference_counts_radius2=counts(p,2),
        face_samples=len(samples),face_sample_reference_counts_radius0=counts(samples,0),
        face_sample_reference_counts_radius2=counts(samples,2),area_voxel2=float(total_area),
        sampled_area_by_reference_id=area_by_id,
        unique_reference390_voxels_covered_within_radius1=len(covered),
        ct_supported_area_within_radius1_voxel2=float(weights[supported].sum()),
        component_selection='closest to seed before annotations' if select_seed_component else 'all output charts (may be disconnected)',source_obj=str(files[0]))

los = '--los' in sys.argv[1:]
ridge = '--ridge' in sys.argv[1:]
all_cases = '--all' in sys.argv[1:]
assert not(los and ridge)
results = json.loads((base/('adaptive-los-evaluation.json' if ridge else 'adaptive-corridor-evaluation.json')).read_text())['cases'] if (los or ridge) else {}
cases = [('adaptive8-ridge','prediction-ct-adaptive8-ridge.zarr')] if ridge else [('adaptive8-los','prediction-ct-adaptive8-los.zarr')] if los else [('original6','prediction-ct-goal-corridor.zarr'),('narrow3','prediction-ct-narrow3.zarr'),('adaptive8','prediction-ct-adaptive8.zarr')]
if all_cases:
    results = {}
    cases += [('adaptive8-los','prediction-ct-adaptive8-los.zarr'),('adaptive8-ridge','prediction-ct-adaptive8-ridge.zarr')]
single_case=sys.argv[sys.argv.index('--case')+1] if '--case' in sys.argv else None
if single_case:
    assert single_case in ['adaptive8-terminal','adaptive8-taper','adaptive8-taper-dense','adaptive8-taper3','adaptive8-taper3-dense','adaptive9-taper3','adaptive9-taper3-dense','mls-radius2','mls-radius3','mls-radius4','mls-radius6','mls-radius8','mls-edge-off','mls-edge-soft','mls-edge-strong','split-cover-control','split-cover-off','split-cover-soft','split-shape-control','split-shape-off','split-shape-soft','boundary-graft-soft']
    results=json.loads((base/'adaptive-final-evaluation.json').read_text())['cases']
    input_name='adaptive8-taper3' if single_case.startswith(('mls-','split-cover-','split-shape-','boundary-graft-')) else single_case.removesuffix('-dense')
    cases=[(single_case,f'prediction-ct-{input_name}.zarr')]
for name,zarr in cases:
    mask = local_zarr(NATIVE/zarr)>0
    q = np.argwhere(mask)[:,::-1]
    results[name] = dict(input_voxels=len(q), input_reference_counts_radius0=counts(q,0),
        input_reference_counts_radius2=counts(q,2),mesh=mesh(name))
    if name.startswith(('split-shape-','boundary-graft-')):
        results[name]['mesh_all_charts']=mesh(name,False)
result = dict(cases=results,goal_conditioned=True,manual_labels_used_only_after_generation=True,
    coverage_domain_xyz=[domain_low.tolist(),domain_high.tolist()],
    reference390_voxels_in_coverage_domain=len(coverage_domain_codes),
    area_units='source voxel squared',
    limitations=['Surface area uses Euclidean triangles; annotation-attributed area is sampled, not an anatomical certificate',
                 'Coverage is unique reference voxels within 1 voxel of face samples, sample spacing <=0.75 voxel',
                 'Common known-goal route, one cube only; current full F0 pipeline not evaluated'])
report_name=f'{single_case}-evaluation.json' if single_case else 'adaptive-final-evaluation.json' if all_cases else 'adaptive-ridge-evaluation.json' if ridge else 'adaptive-los-evaluation.json' if los else 'adaptive-corridor-evaluation.json'
(base/report_name).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(results[single_case] if single_case else result,indent=2),flush=True)
