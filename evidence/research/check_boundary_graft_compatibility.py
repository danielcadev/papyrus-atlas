"""Sequential focused checks: detector cap, disabled parity, original crop."""
from pathlib import Path
import json,os,subprocess,sys,hashlib
from guard import start_guard
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison';s=b/'source/src';build=b/'build'
subprocess.run(['cc','-O2','-std=gnu17','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I',str(s),str(p/'test_boundary_graft.c'),str(s/'common/arena.c'),str(s/'common/except.c'),str(s/'common/csr.c'),'-lm','-o',str(build/'test_boundary_graft')],check=True)
subprocess.run([str(build/'test_boundary_graft')],check=True)
env=os.environ.copy();env['V2_MODE']='v2-off';env.pop('SPLIT_VALIDATION_OFFSET_X',None)
subprocess.run([sys.executable,str(p/'run_boundary_graft_case.py')],env=env,check=True)
d=b/'independent-central32'
def final(directory):
    paths=list(directory.glob('*/*step11_kibble/*_all.vmesh'));assert len(paths)==1;return paths[0]
assert final(d/'v2-off-obj').read_bytes()==final(d/'control-obj').read_bytes()
print('Feature disabled: exact binary mesh parity with frozen control',flush=True)
name='boundary-graft-soft';log=b/f'{name}-meshing.log';assert not log.exists()
input_file=b/'inputs/adaptive8-taper3/cubes_PRED/z00768_y02408_x03536.tif'
binary=build/'cube_mesh.boundary-graft-v2'
env=os.environ.copy()
for key in ['MLS_RADIUS_VOX','MLS_EDGE_ADAPT','MLS_PERTURB_EPS','VES_OVERLAP_COVERAGE_GUARD']:env.pop(key,None)
env.update(MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD='1')
cmd=[str(binary),str(input_file),str(b/f'{name}-output.tif'),'--dump-obj',str(b/f'{name}-obj'),'--no-simplify']
(b/f'{name}-command.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(input_file.read_bytes()).hexdigest()),indent=2)+'\n')
with log.open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
logtext=log.read_text();assert 'Status: OK' in logtext
assert 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)' in logtext
identical=final(b/f'{name}-obj').read_bytes()==final(b/'split-shape-soft-obj').read_bytes()
result=dict(disabled_central_mesh_byte_identical=True,original_crop_mesh_byte_identical=identical)
if identical:
    result['original_crop_metrics_reused_from']='split-shape-soft-evaluation.json'
    result['original_crop_geometry_reused_from']='split-shape-soft-native-geometry.json'
else:
    subprocess.run([sys.executable,str(p/'evaluate_first_boundary_graft.py'),'--case',name],check=True)
    subprocess.run([str(build/'saved_geometry_audit.independent'),str(final(b/f'{name}-obj')),str(b/f'{name}-native-geometry.json'),str(b/f'{name}-native-geometry-pairs.csv'),'768','2408','3536'],check=True)
(b/'boundary-graft-compatibility.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
