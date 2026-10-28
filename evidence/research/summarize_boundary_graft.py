"""Preserve exact geometric conflict provenance and final v2 evidence."""
from pathlib import Path
import csv,difflib,hashlib,json,struct
import numpy as np
from guard import start_guard
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison'
def final(d):
 f=list(d.glob('*/*step11_kibble/*_all.vmesh'));assert len(f)==1;return f[0]
def read(path):
 data=path.read_bytes();magic,version,endian,flags,header,nv,nf,vo,uo,fo=struct.unpack('<8sIIIIQQQQQ',data[:64]);assert magic==b'VESMESH1'
 v=np.frombuffer(data,dtype='<f4',count=nv*3,offset=vo).reshape(-1,3)
 f=np.frombuffer(data,dtype='<i4',count=nf*3,offset=fo).reshape(-1,3)
 return v,f
def tri_key(t):return tuple(sorted(map(tuple,t.tolist())))
def conflict_keys(d,mode):
 v,f=read(final(d/f'{mode}-obj'))
 with (d/f'{mode}-native-geometry-pairs.csv').open() as stream:
  return sorted((int(row['kind']),tuple(sorted([tri_key(v[f[int(row['face0'])]]),tri_key(v[f[int(row['face1'])]])]))) for row in csv.DictReader(stream))
d=b/'fresh-yplus32-v2';before=conflict_keys(d,'control');after=conflict_keys(d,'corrected');assert before==after and len(before)==1
(d/'conflict-provenance.json').write_text(json.dumps(dict(geometric_pairs_identical=True,existing_pairs=len(before),new_pairs=0,removed_pairs=0,comparison='Exact global float32 coordinates of both triangles, independent of vertex/face numbering',pair_geometry=before),indent=2)+'\n')
# Real integration agrees with the saved-data probe, not just its face count.
d=b/'independent-central32';source=list((d/'v2-obj').glob('*/*step1c_devcut/*_all.vmesh'));assert len(source)==1
v,f=read(source[0]);v1,f1=read(final(d/'corrected-obj'));v2,f2=read(final(d/'v2-obj'))
k1={tri_key(t) for t in v1[f1]};k2={tri_key(t) for t in v2[f2]}
added=[i for i,t in enumerate(v[f]) if tri_key(t) in k2 and tri_key(t) not in k1]
expected=json.loads((d/'multichart-boundary-recovery-probe.json').read_text())['added_face_ids'];assert added==expected
(d/'v2-exact-source-recovery.json').write_text(json.dumps(dict(recovered_original_face_ids=added,unchanged_source_triangles=True,exact_probe_agreement=True),indent=2)+'\n')
# Neighbor is byte-identical: reuse prior measurements and collision audit.
d=b/'independent-xplus32';assert final(d/'v2-obj').read_bytes()==final(d/'corrected-obj').read_bytes()
old=json.loads((d/'evaluation.json').read_text())
(d/'v2-evaluation.json').write_text(json.dumps(dict(metrics_reused_from_byte_identical_output='evaluation.json/cases/corrected',cases={'v2':old['cases']['corrected']},native_geometry={'v2':old['native_geometry']['corrected']}),indent=2)+'\n')
rows=[]
old=json.loads((b/'split-shape-soft-evaluation.json').read_text())['cases']['split-shape-soft']['mesh_all_charts']
new=json.loads((b/'boundary-graft-soft-evaluation.json').read_text())['cases']['boundary-graft-soft']['mesh_all_charts']
rows.append(dict(case='original goal-conditioned development',before=old,after=new))
for folder in ['independent-central32','independent-xplus32','fresh-yplus32-v2']:
 d=b/folder;old=json.loads((d/'evaluation.json').read_text());fresh=folder.startswith('fresh')
 new=old['cases']['corrected'] if fresh else json.loads((d/'v2-evaluation.json').read_text())['cases']['v2']
 prior=old['cases']['control' if fresh else 'corrected']
 rows.append(dict(case=folder,before=prior,after=new))
result=dict(version='boundary-graft-v2',binary_sha256=hashlib.sha256((b/'build/cube_mesh.boundary-graft-v2').read_bytes()).hexdigest(),cases=rows,
    fresh_window_preexisting_conflict_geometry_identical=True,new_conflicts_in_fresh_window=0,
    original_and_central_conflicts=0,neighbor_byte_identical=True,disabled_central_byte_identical=True,
    resource_limits=dict(cpu_quota_percent=25,memory_max_mib=384,swap_max=0,gpu_inaccessible=True,desktop_reserve_mib=3072),
    limitations=['Development and fresh windows share the same CT cube/scroll','Fresh test compares v1 coverage guard with v2, not untouched upstream','Recorded projected constraints exclude shared-vertex pairs; native 3D audit is separate','A pre-existing native overlap remains in the fresh window','No whole-scroll, halo/seam or ink-reading evaluation'])
(b/'boundary-graft-results.json').write_text(json.dumps(result,indent=2)+'\n')
old=(b/'overlap_sep.before-boundary-graft.c').read_text().splitlines(True);new=(b/'source/src/split/overlap_sep.c').read_text().splitlines(True)
patch=''.join(difflib.unified_diff(old,new,fromfile='a/src/split/overlap_sep.c',tofile='b/src/split/overlap_sep.c'))
(b/'boundary-graft-v2.patch').write_text(patch)
files=[b/'boundary-graft-v2.patch',b/'boundary-graft-results.json',p/'test_boundary_graft.c',b/'source/src/split/overlap_sep.c',b/'build/cube_mesh.boundary-graft-v2']
(b/'boundary-graft-sha256.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(p))+'\n' for f in files))
print('Native 13-face recovery matches exact saved-source IDs; fresh conflict pair exact geometry identical; neighbor parity; patch and hashes preserved.',flush=True)
for row in rows:
 print(row['case'],row['before'].get('area_voxel2'),row['after'].get('area_voxel2'),flush=True)
