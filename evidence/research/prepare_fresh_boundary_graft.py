"""Freeze a central real-CT window from a different cube; no label access."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from guard import start_guard
from inspect_cube import read_nrrd

start_guard()
root=Path(__file__).resolve().parent
base=root/'scrollfiesta-comparison'
offset_x=0
dest=base/'fresh-yplus32-v2'
assert not dest.exists(), 'Preserve frozen selection and results'
source=root/'data/01744_02256_04048_volume.nrrd'
volume,header=read_nrrd(source)
assert volume.shape==(256,256,256) and volume.dtype in [np.dtype('u1'),np.dtype('<u2')]
divisor=257 if volume.dtype.itemsize==2 else 1
raw=(volume[64:192,64:192,64:192].transpose(2,1,0)//divisor).astype('uint8')
window=raw[48:80,80:112,48:80]
hist=np.bincount(window.ravel(),minlength=256).astype(float)
p=hist/hist.sum();w=p.cumsum();mu=(p*np.arange(256)).cumsum()
score=np.full(256,-np.inf);good=(w>0)&(w<1)
score[good]=(mu[-1]*w[good]-mu[good])**2/(w[good]*(1-w[good]))
threshold=int(score.argmax())
pred=np.zeros_like(raw)
pred[48:80,80:112,48:80]=(window>threshold).astype('uint8')*255
dest.mkdir()
cube_id='z01808_y02320_x04112'
for folder,array in [('cubes_RAW',raw),('cubes_PRED',pred)]:
    output=dest/folder/f'{cube_id}.tif';output.parent.mkdir()
    frames=[Image.fromarray(frame) for frame in array]
    frames[0].save(output,save_all=True,append_images=frames[1:],compression='raw')
np.save(dest/'raw.npy',raw)
np.save(dest/'prediction.npy',pred)
record=dict(dataset='PHercParis4 harmonized manual-instance CT collection, 2024-10',
    source_cube='01744_02256_04048',source_volume=str(source),
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    source_axes='NRRD native XYZ, TIFF ZYX',parent_native_xyz_low=[64,64,64],
    parent_shape_xyz=[128,128,128],parent_world_origin_zyx=[1808,2320,4112],
    active_roi_parent_xyz=[[48,80,48],[80,112,80]],
    active_roi_source_xyz=[[112,144,112],[144,176,144]],
    roi_shape_xyz=[32,32,32],threshold_exclusive=threshold,
    foreground_voxels=int((pred>0).sum()),
    input_sha256=hashlib.sha256((dest/'cubes_PRED'/f'{cube_id}.tif').read_bytes()).hexdigest(),
    cube_id=cube_id,selection='One fixed positive-Y neighbor, +32 vox from central crop, chosen before outcomes; v2 code frozen; no alternative window search',
    input_method='CT native uint8 (or uint16 //257), Otsu from active window; prediction zero outside active ROI; real raw CT retained in whole parent',
    source_dtype=str(volume.dtype),intensity_divisor=divisor,
    manual_labels_opened=False,known_goal_or_seed_used_for_input=False,
    binary_sha256=hashlib.sha256((base/'build/cube_mesh.split-coverage').read_bytes()).hexdigest(),
    frozen_parameters=dict(mls_radius=12,mls_mode='soft',mls_strength=2,ownership_epsilon=.25,
        rebuild_bidirectional_epsilon=.5,skip_simplify=True,halo=0),
    evaluation_plan=dict(surface='all output charts plus source-component-specific summary',
        boundary='all source boundary vertices before separation; distances to final triangle surfaces',
        tip='largest-area source face component; positive extreme along its widest XYZ bounding-box axis, lexicographic tie break; freeze before corrected run',
        annotations='post-hoc reference coverage and mixed-label face cues only'),
    limitations=['Different cube but same scroll; not a new scroll test',
        'Same CT cube as development; this new window was not used to tune v2',
        'Otsu is a classical intensity baseline, not a trained surface predictor',
        'Artificial crop boundaries exist; geometric tip is not a certified torn anatomical tip',
        'No halo/seam or whole F0 validation'])
(dest/'frozen-input.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
