"""Independent exact-coordinate certificate; no native geometry code imported.

This deliberately certifies only exact duplicates and source-face retention.
It cannot certify sheet identity or detect general triangle intersections.
"""
from pathlib import Path
from collections import Counter
import json,struct,hashlib,subprocess
from guard import start_guard
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';d=b/'holefill-repair-v4'
def mesh(folder,stage):
    files=list(folder.glob(f'*/*{stage}/*_all.vmesh'));assert len(files)==1
    path=files[0];payload=path.read_bytes();h=struct.unpack('<8sIIIIQQQQQ',payload[:64])
    assert h[:5]==(b'VESMESH1',1,0x01020304,0,64)
    nv,nf,vo,uo,fo=h[5:];assert vo==64 and uo==0 and fo==vo+nv*12 and len(payload)==fo+nf*12
    vertices=list(struct.iter_unpack('<fff',payload[vo:fo]))
    faces=list(struct.iter_unpack('<iii',payload[fo:]))
    assert len(vertices)==nv and len(faces)==nf
    assert all(0<=i<nv for f in faces for i in f)
    return path,[tuple(vertices[i] for i in f) for f in faces]
def oriented(t):return min(t,t[1:]+t[:1],t[2:]+t[:2])
def duplicate_groups(tri):
    groups={}
    for i,t in enumerate(tri):groups.setdefault(tuple(sorted(t)),[]).append(i)
    return [g for g in groups.values() if len(g)>1]
pre,source=mesh(d/'y32-obj','step7_cc_bpa')
new,newtri=mesh(d/'y32-obj','step11_kibble')
old,oldtri=mesh(b/'fresh-yplus32-v2/corrected-obj','step11_kibble')
missing=Counter(map(oriented,source))-Counter(map(oriented,newtri))
assert not missing,'Source triangle multiplicities and cyclic orientations must survive'
oldgroups=duplicate_groups(oldtri);newgroups=duplicate_groups(newtri)
assert len(oldgroups)==1 and not newgroups
groups=[dict(faces=g,global_zyx_triangles=[oldtri[i] for i in g]) for g in oldgroups]
result=dict(source_triangles=len(source),source_missing_or_reoriented=0,
    exact_duplicate_groups_before=len(oldgroups),exact_duplicate_groups_after=len(newgroups),
    before_groups=groups,new_final_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),
    native_source_imports=False,coordinate_tolerance=0,
    limits=['Exact coincidence only; general intersections require the separate native audit',
            'Saved global float32 geometry; not an anatomical sheet-identity certificate'])
out=d/'independent-certificate.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
source_file=b/'source/src/holefill/hole_fill.c'
patch=d/'holefill-geometric-duplicate.patch';assert not patch.exists()
diff=subprocess.run(['diff','-u','--label','a/src/holefill/hole_fill.c','--label','b/src/holefill/hole_fill.c',str(b/'holefill-repair/hole_fill.before.c'),str(source_file)],capture_output=True,text=True)
assert diff.returncode==1;patch.write_text(diff.stdout)
files=[source_file,patch,b/'build/cube_mesh.holefill-v4',b/'build/cube_mesh.boundary-graft-v2',b/'build/cube_mesh.split-coverage',p/'replay_holefill.c',p/'test_holefill_duplicate.c',p/'evaluate_holefill_repair.py',p/'check_holefill_regressions.py',p/'independent_holefill_certificate.py',p/'run_holefill_guarded.sh']
hashfile=d/'sha256.txt';assert not hashfile.exists()
hashfile.write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(p))+'\n' for f in files))
print(json.dumps({k:v for k,v in result.items() if k!='before_groups'},indent=2))
