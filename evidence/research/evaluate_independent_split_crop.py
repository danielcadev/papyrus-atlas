"""Evaluate frozen second-cube controls; no retries or parameter tuning."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import numpy as np
from guard import start_guard
from independent_split_common import ROOT,DEST,load_stage,areas,face_components,point_to_triangles
from inspect_cube import read_nrrd
from evaluate_native import identities

start_guard()
base=DEST.parent;build=base/'build';source=base/'source'
frozen=json.loads((DEST/'frozen-input.json').read_text())
probes=json.loads((DEST/'frozen-source-probes.json').read_text())
outputs={}
for mode in ['control','corrected']:
    v,f,path=load_stage(mode,'step11_kibble')
    source_v,source_f,source_path=load_stage(mode,'step1c_devcut')
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==probes['source_stage_sha256']
    log=(DEST/f'{mode}-meshing.log').read_text()
    assert 'Status: OK' in log
    assert 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in log
    outputs[mode]=(v,f,path)
identical=outputs['control'][2].read_bytes()==outputs['corrected'][2].read_bytes()

# Calibrated native detector, with this crop's actual working origin.
obj=build/'saved_geometry_audit.independent.o';binary=build/'saved_geometry_audit.independent'
subprocess.run(['cc','-O2','-std=c17','-I',str(source/'src'),'-c',
    str(ROOT/'saved_geometry_audit.c'),'-o',str(obj)],check=True)
subprocess.run(['c++','-fopenmp',str(obj),str(build/'libscrollfiesta_core.a'),
    str(build/'libsf_triangle.a'),str(build/'clipper2/libClipper2.a'),
    str(build/'clipper2/libClipper2Z.a'),'/lib64/libtiff.so.6','-lm','-o',str(binary)],check=True)
for mode in ['control'] if identical else ['control','corrected']:
    result=DEST/f'{mode}-native-geometry.json';assert not result.exists()
    subprocess.run([str(binary),str(outputs[mode][2]),str(result),
        str(DEST/f'{mode}-native-geometry-pairs.csv')]+list(map(str,frozen['parent_world_origin_zyx'])),check=True)
if identical:
    audit=json.loads((DEST/'control-native-geometry.json').read_text())
    audit['reused_from_byte_identical_output']='control'
    (DEST/'corrected-native-geometry.json').write_text(json.dumps(audit,indent=2)+'\n')

# References enter only here, after both frozen native outputs exist.
labels,_=read_nrrd(ROOT/'data/01744_02256_04048_mask.nrrd')
domain_low,domain_high=np.asarray(frozen['active_roi_source_xyz'])
domain=labels[tuple(slice(int(l),int(h)) for l,h in zip(domain_low,domain_high))]
reference_domain_counts=dict(Counter(map(str,domain[domain>0].ravel())))
prediction=np.load(DEST/'prediction.npy')>0
results={}
for mode in ['control'] if identical else ['control','corrected']:
    v,f,path=outputs[mode];tri=v[f];area=areas(tri)
    samples=[];weights=[];mixed=0;sample_total=0
    for t,a in zip(tri,area):
        n=max(1,int(np.ceil(max(np.linalg.norm(t[1]-t[0]),np.linalg.norm(t[2]-t[0]),np.linalg.norm(t[2]-t[1]))/.75)))
        sample_total+=n*n
        assert sample_total<=1000000,'Evaluation sample budget; do not silently coarsen'
        uv=[]
        for i in range(n):
            for j in range(n-i):
                uv.append(((i+1/3)/n,(j+1/3)/n))
                if i+j<n-1:uv.append(((i+2/3)/n,(j+2/3)/n))
        uv=np.asarray(uv)
        p=t[0]+uv[:,0,None]*(t[1]-t[0])+uv[:,1,None]*(t[2]-t[0])
        rounded=np.rint(p+64).astype(int)
        ids=labels[tuple(rounded.T)]
        mixed+=int(len(np.unique(ids[ids>0]))>1)
        samples.append(p);weights.append(np.full(n*n,a/(n*n)))
    samples=np.concatenate(samples);weights=np.concatenate(weights)
    direct=identities(labels,samples+64,0)
    nearby=identities(labels,samples+64,2)
    covered=set();supported=np.zeros(len(samples),dtype=bool)
    rounded=np.rint(samples).astype(int)
    for delta in itertools.product((-1,0,1),repeat=3):
        q=rounded+delta;close=np.linalg.norm(q-samples,axis=1)<=1
        valid=close&((q>=0)&(q<128)).all(1)
        ix=np.flatnonzero(valid);supported[ix]|=prediction[tuple(q[ix,::-1].T)]
        ref=q+64
        good=close&((ref>=domain_low)&(ref<domain_high)).all(1)
        ref=ref[good];ref=ref[labels[tuple(ref.T)]>0]
        covered.update(np.ravel_multi_index(ref.T,labels.shape))
    covered=np.array(sorted(covered),dtype=int)
    covered_labels=labels[np.unravel_index(covered,labels.shape)]
    boundary=np.asarray(probes['boundary_parent_xyz'])
    boundary_dist=np.array([float(point_to_triangles(tri,p).min()) for p in boundary])
    np.save(DEST/f'{mode}-source-boundary-distances.npy',boundary_dist)
    tip=np.asarray(probes['tip_parent_xyz'])
    stats=dict(vertices=len(v),triangles=len(f),components=len(np.unique(face_components(v,f))),
        area_voxel2=float(area.sum()),reference_voxels_covered_within_radius1=len(covered),
        reference_coverage_by_id=dict(Counter(map(str,covered_labels))),
        samples=len(samples),sample_reference_counts_radius0=dict(Counter(map(str,direct))),
        sample_reference_counts_radius2=dict(Counter(map(str,nearby))),
        sampled_area_by_id_radius0={str(k):float(weights[direct==k].sum()) for k in np.unique(direct)},
        mixed_reference_triangle_count=mixed,
        input_ct_supported_area_radius1=float(weights[supported].sum()),
        frozen_geometric_tip_distance=float(point_to_triangles(tri,tip).min()),
        source_boundary_probes=len(boundary_dist),
        boundary_distance_median=float(np.median(boundary_dist)),
        boundary_distance_p95=float(np.percentile(boundary_dist,95)),
        boundary_distance_max=float(boundary_dist.max()),
        boundary_vertices_farther_than1=int((boundary_dist>1).sum()),
        source_obj=str(path.with_suffix('.obj')))
    results[mode]=stats
    print(mode,json.dumps(stats,indent=2),flush=True)
if identical:
    results['corrected']=dict(results['control'])
    results['corrected']['source_obj']=str(outputs['corrected'][2].with_suffix('.obj'))
    results['corrected']['metrics_reused_from_byte_identical_output']='control'
result=dict(input=frozen,source_probes={k:v for k,v in probes.items() if k!='boundary_parent_xyz'},
    outputs_byte_identical=identical,cases=results,reference_domain_counts=reference_domain_counts,
    native_geometry={mode:json.loads((DEST/f'{mode}-native-geometry.json').read_text()) for mode in outputs},
    correction_parameters_changed=False,input_or_probe_selected_using_labels=False,
    limitations=['Same scroll, different CT cube; early unrelated 2D analysis exists for this cube',
        'Reference coverage counts all labeled identities, not an anatomical correctness certificate',
        'Mixed-label triangles are finite annotation cues, not proven sheet jumps',
        'Tip is a deterministic source boundary extreme, not certified torn papyrus tip',
        'Artificial 32^3 crop with zero exterior prediction, no halo or full F0 evaluation',
        'Native gap-zero audit measures intersections, not minimum physical separation'])
(DEST/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
print('outputs_byte_identical',identical,flush=True)
