"""Validate same-scan-supported axis correction using frozen modern CT queries."""
from pathlib import Path
import json,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
import numpy as np
root=Path(__file__).resolve().parent;case=root/'paris4-registration-anchors-v1'
out=case/'corrected-ct-v1';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'script.py')
axis=json.loads((case/'signed-axis-v1/result.json').read_text());assert axis['candidate_same_scan_gate_passed']
assert axis['chosen_by_training']['permutation_nrrd_to_global_zyx']==[0,1,2]
assert axis['chosen_by_training']['flips']==[False]*3
old=root/'repaired-mesh-ink-v1'
footprint=old/'ct-registration-footprint-v1';prior=json.loads((footprint/'result.json').read_text())
for name,sha in prior['artifacts'].items():assert digest(footprint/name)==sha
target=np.load(old/'ct-registration-v2/old-native-roi-xyz.npy',allow_pickle=False)
nominal=np.load(footprint/'modern-footprint-resampled-extended-xyz.npy',allow_pickle=False)
assert nominal.shape==(40,40,40)
# Prior X/Z ROI limits and footprint quadrature sets are identical, so every
# corrected query is already present: transpose query axes, not CT intensity.
corrected=nominal.transpose(2,1,0).copy()
(out/'plan.json').write_text(json.dumps(dict(guard=guard,
    same_scan_axis_result_sha256=digest(case/'signed-axis-v1/result.json'),
    source_footprint_result_sha256=digest(footprint/'result.json'),
    correction='Native NRRD axis order is global ZYX. Reverse native indices before applying the catalogue XYZ affine.',
    reuse='Exact reindexing of the identical symmetric X/Z ROI and 64-point cell quadrature; no new fitted translation.',
    gates=dict(pearson_min=.6,margin_over_six_four_voxel_controls_min=.1),
    ink_used=False,source_geometry_modified=False),indent=2))
np.save(out/'corrected-modern-footprint-native-zyx.npy',corrected,allow_pickle=False)
def corr(a,b):return float(np.corrcoef(a.ravel(),b.ravel())[0,1])
scores={}
for shift in ((0,0,0),(-4,0,0),(4,0,0),(0,-4,0),(0,4,0),(0,0,-4),(0,0,4)):
    scores['_'.join(map(str,shift))]=corr(target,corrected[tuple(slice(4+i,36+i) for i in shift)])
primary=scores['0_0_0'];control=max(v for k,v in scores.items() if k!='0_0_0')
passed=primary>=.6 and primary-control>=.1
blocks=[]
for b in ((0,0,0),(0,0,16),(0,16,0),(0,16,16),(16,0,0),(16,0,16),(16,16,0),(16,16,16)):
    sl=tuple(slice(i,i+16) for i in b);q=tuple(slice(4+i,20+i) for i in b)
    blocks.append(dict(origin_native=b,pearson=corr(target[sl],corrected[q])))
result=dict(guard=guard,primary_pearson=primary,best_shift_control=control,margin=primary-control,
    pearson_by_control_native_zyx=scores,diagnostic_structural_coherence_gate_passed=passed,
    blocks=blocks,anatomical_registration_error_voxels=None,letters_verified=0,
    source_geometry_modified=False,ink_used=False,
    interpretation='Corrected coordinate convention supported by same-scan CT and tested against unchanged cross-scan coherence gates. Not ink/letter truth or a subvoxel error bound.',
    artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()})
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
