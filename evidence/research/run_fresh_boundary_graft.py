"""One predeclared window, no parameter search; v1 versus frozen v2."""
import hashlib,json,os,runpy,subprocess,sys
from pathlib import Path
from guard import start_guard
import independent_split_common as common
start_guard()
p=Path(__file__).resolve().parent;b=p/'scrollfiesta-comparison'
common.DEST=b/'fresh-yplus32-v2';d=common.DEST
runpy.run_path(str(p/'prepare_fresh_boundary_graft.py'),run_name='__main__')
frozen=json.loads((d/'frozen-input.json').read_text())
bins={'control':b/'build/cube_mesh.split-coverage','corrected':b/'build/cube_mesh.boundary-graft-v2'}
for mode,binary in bins.items():
    if mode=='corrected':
        runpy.run_path(str(p/'freeze_independent_source_probes.py'),run_name='__main__')
    env=os.environ.copy()
    for key in ['MLS_RADIUS_VOX','MLS_EDGE_ADAPT','MLS_PERTURB_EPS','VES_OVERLAP_COVERAGE_GUARD']:env.pop(key,None)
    env.update(MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD='1')
    cmd=[str(binary),str(d/'cubes_PRED'/f"{frozen['cube_id']}.tif"),str(d/f'{mode}-output.tif'),'--dump-obj',str(d/f'{mode}-obj'),'--no-simplify']
    log=d/f'{mode}-meshing.log';assert not log.exists()
    (d/f'{mode}-command.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),MLS_EDGE_ADAPT='soft',VES_OVERLAP_COVERAGE_GUARD='1'),indent=2)+'\n')
    with log.open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    print(mode,'completed',flush=True)
runpy.run_path(str(p/'evaluate_independent_split_crop.py'),run_name='__main__')
record=json.loads((d/'evaluation.json').read_text())
record.update(control_is_v1_coverage_guard_enabled=True,corrected_is_v2_boundary_graft=True,
    correction_parameters_changed=True,parameters_tuned_after_selection=False,
    window_selected_before_outcomes=True,code_frozen_before_selection=True)
(d/'evaluation.json').write_text(json.dumps(record,indent=2)+'\n')
