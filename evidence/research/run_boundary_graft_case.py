"""Run the frozen v2 prototype once, preserving v1 controls."""
import hashlib,json,os,subprocess
from independent_split_common import ROOT,DEST
from guard import start_guard
start_guard()
frozen=json.loads((DEST/'frozen-input.json').read_text())
binary=ROOT/'scrollfiesta-comparison/build/cube_mesh.boundary-graft-v2'
input_file=DEST/'cubes_PRED'/f"{frozen['cube_id']}.tif"
assert hashlib.sha256(input_file.read_bytes()).hexdigest()==frozen['input_sha256']
mode=os.environ.get('V2_MODE','v2');assert mode in ['v2','v2-off']
log=DEST/f'{mode}-meshing.log';assert not log.exists()
env=os.environ.copy()
for key in ['MLS_RADIUS_VOX','MLS_EDGE_ADAPT','MLS_PERTURB_EPS','VES_OVERLAP_COVERAGE_GUARD']:env.pop(key,None)
env['MLS_EDGE_ADAPT']='soft'
if mode=='v2':env['VES_OVERLAP_COVERAGE_GUARD']='1'
command=[str(binary),str(input_file),str(DEST/f'{mode}-output.tif'),'--dump-obj',str(DEST/f'{mode}-obj'),'--no-simplify']
(DEST/f'{mode}-command.json').write_text(json.dumps(dict(command=command,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD=env.get('VES_OVERLAP_COVERAGE_GUARD')),indent=2)+'\n')
with log.open('w') as stream:result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT)
print(log.read_text()[-7000:],flush=True)
raise SystemExit(result.returncode)
