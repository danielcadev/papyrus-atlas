"""Focused complete-pipeline regressions, sequential and immutable outputs."""
from pathlib import Path
import json,os,subprocess,hashlib,struct
from collections import Counter
from guard import start_guard
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';d=b/'holefill-repair-v4';build=b/'build'
binary=build/'cube_mesh.holefill-v4'
def final(folder):
    files=list(folder.glob('*/*step11_kibble/*_all.vmesh'));assert len(files)==1;return files[0]
env=os.environ.copy()
for k in ['MLS_RADIUS_VOX','MLS_PERTURB_EPS']:env.pop(k,None)
env.update(MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD='1')
cases=[('central',b/'independent-central32/cubes_PRED/z01808_y02320_x04112.tif',b/'independent-central32/v2-obj'),
       ('xplus32',b/'independent-xplus32/cubes_PRED/z01808_y02320_x04112.tif',b/'independent-xplus32/v2-obj'),
       ('original',b/'inputs/adaptive8-taper3/cubes_PRED/z00768_y02408_x03536.tif',b/'boundary-graft-soft-obj')]
results={}
for name,input_file,reference in cases:
    dest=d/f'{name}-obj';log=d/f'{name}-meshing.log'
    cmd=[str(binary),str(input_file),str(d/f'{name}-output.tif'),'--dump-obj',str(dest),'--no-simplify']
    if not log.exists():
        assert not dest.exists()
        with log.open('w') as stream:subprocess.run(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    text=log.read_text();assert 'Status: OK' in text
    assert 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in text
    out=final(dest);old=final(reference);identical=out.read_bytes()==old.read_bytes()
    results[name]=dict(command=cmd,input_sha256=hashlib.sha256(input_file.read_bytes()).hexdigest(),
        final_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),reference=str(old),
        byte_identical_to_v2=identical,guard_changes=0)
    if not identical:
        def triangles(path):
            payload=path.read_bytes();h=struct.unpack('<8sIIIIQQQQQ',payload[:64]);v=list(struct.iter_unpack('<fff',payload[h[7]:h[9]]))
            return [tuple(v[i] for i in f) for f in struct.iter_unpack('<iii',payload[h[9]:])]
        def directed(t):return min(t,t[1:]+t[:1],t[2:]+t[:2])
        before=list(dest.glob('*/*step7_cc_bpa/*_all.vmesh'));assert len(before)==1
        oldbefore=list(reference.glob('*/*step7_cc_bpa/*_all.vmesh'));assert len(oldbefore)==1
        assert before[0].read_bytes()==oldbefore[0].read_bytes()
        source=Counter(map(directed,triangles(before[0])));newtri=triangles(out);oldtri=triangles(old)
        assert not source-Counter(map(directed,newtri))
        origin=['768','2408','3536'] if name=='original' else ['1808','2320','4112']
        audit=d/f'{name}-audit.json';assert not audit.exists()
        subprocess.run([str(build/'saved_geometry_audit.independent'),str(out),str(audit),str(d/f'{name}-pairs.csv')]+origin,check=True)
        record=json.loads(audit.read_text());assert record['conflicts']==0
        results[name].update(before_faces=len(oldtri),after_faces=len(newtri),
            source_faces_preserved=True,native_audit=record,
            exact_duplicate_groups_before=sum(n>1 for n in Counter(tuple(sorted(t)) for t in oldtri).values()),
            exact_duplicate_groups_after=sum(n>1 for n in Counter(tuple(sorted(t)) for t in newtri).values()))
        print(name,json.dumps(results[name]),flush=True)
    else:print(name,'byte-identical to frozen v2; metrics and geometry audit reused',flush=True)
out=d/'regressions.json';assert not out.exists();out.write_text(json.dumps(results,indent=2)+'\n')
